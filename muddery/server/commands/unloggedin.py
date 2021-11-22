"""
General commands usually availabe to all users.
"""

import re
import time
import hashlib
from collections import defaultdict
from django.conf import settings
from muddery.server.mappings.element_set import ELEMENT
from muddery.server.utils import logger
from muddery.server.commands.base_command import BaseCommand
from muddery.server.utils.exception import MudderyError, ERR
from muddery.server.utils.localized_strings_handler import _
from muddery.server.utils.game_settings import GAME_SETTINGS
from muddery.server.database.worlddata.equipment_positions import EquipmentPositions
from muddery.server.database.worlddata.honour_settings import HonourSettings


# Helper function to throttle failed connection attempts.
# This can easily be used to limit player creation too,
# (just supply a different storage dictionary), but this
# would also block dummyrunner, so it's not added as default.

_LATEST_FAILED_LOGINS = defaultdict(list)
def _throttle(session, maxlim=None, timeout=None, storage=_LATEST_FAILED_LOGINS):
    """
    This will check the session's address against the
    _LATEST_LOGINS dictionary to check they haven't
    spammed too many fails recently.

    Args:
        session (Session): Session failing
        maxlim (int): max number of attempts to allow
        timeout (int): number of timeout seconds after
            max number of tries has been reached.

    Returns:
        throttles (bool): True if throttling is active,
            False otherwise.

    Notes:
        If maxlim and/or timeout are set, the function will
        just do the comparison, not append a new datapoint.

    """
    address = session.address
    if isinstance(address, tuple):
        address = address[0]
    now = time.time()
    if maxlim and timeout:
        # checking mode
        latest_fails = storage[address]
        if latest_fails and len(latest_fails) >= maxlim:
            # too many fails recently
            if now - latest_fails[-1] < timeout:
                # too soon - timeout in play
                return True
            else:
                # timeout has passed. Reset faillist
                storage[address] = []
                return False
    else:
        # store the time of the latest fail
        storage[address].append(time.time())
        return False


class CmdConnectAccount(BaseCommand):
    """
    connect to the game

    Usage:
        {
            "cmd":"connect",
            "args":{
                "playername":<playername>,
                "password":<password>
            }
        }

    """
    key = "connect"

    @classmethod
    def func(cls, session, args, context):
        """
        Uses the Django admin api. Note that unlogged-in commands
        have a unique position in that their func() receives
        a session object instead of a source_object like all
        other types of logged-in commands (this is because
        there is no object yet before the player has logged in)
        """
        try:
            username = args["username"]
            password = args["password"]
        except Exception:
            string = 'Can not log in.'
            logger.log_err(string)
            session.msg({"alert":string})
            return

        # check for too many login errors too quick.
        if _throttle(session, maxlim=5, timeout=5*60, storage=_LATEST_FAILED_LOGINS):
            # timeout is 5 minutes.
            session.msg({"alert":_("{RYou made too many connection attempts. Try again in a few minutes.{n")})
            return

        if not password:
            session.msg({"alert":_("Please input password.")})
            return

        # Get the account.
        element_type = settings.ACCOUNT_ELEMENT_TYPE
        account = ELEMENT(element_type)()

        # Set the account with username and password.
        try:
            account.set_user(username, password, session)
        except MudderyError as e:
            if e.code == ERR.no_authentication:
                # Wrong username or password.
                session.msg({"alert": str(e)})
            else:
                session.msg({"alert": _("You can not login.")})

            # this just updates the throttle
            _throttle(session)
            return None

        # actually do the login. This will call all other hooks:
        #   session.at_login()
        #   player.at_init()  # always called when object is loaded from disk
        #   player.at_first_login()  # only once, for player-centric setup
        #   player.at_pre_login()
        #   player.at_post_login(session=session)
        session.sessionhandler.login(session, account)

        session.msg({
            "login": {
                "name": username,
                "id": account.get_id(),
            },
            "char_all": account.get_all_nicknames()
        })


class CmdCreateAccount(BaseCommand):
    """
    create a new player account and login

    Usage:
        {
            "cmd":"create",
            "args":{
                "playername":<playername>,
                "password":<password>,
                "connect":<connect>
            }
        }

    args:
        connect: (boolean)connect after created
    """
    key = "create"

    @classmethod
    def func(cls, session, args, context):
        "Do checks, create account and login."
        if not args:
            session.msg({"alert": _("Syntax error!")})
            return

        if "username" not in args:
            session.msg({"alert": _("You should appoint a username.")})
            return

        if "password" not in args:
            session.msg({"alert": _("You should appoint a password.")})
            return

        username = args["username"]
        username = re.sub(r"\s+", " ", username).strip()

        password = args["password"]

        connect = True
        if "connect" in args:
            connect = args["connect"]

        # Create an account.
        element_type = settings.ACCOUNT_ELEMENT_TYPE
        account = ELEMENT(element_type)()

        # Set the account with username and password.
        try:
            account.new_user(username, password, "", session)
        except MudderyError as e:
            if e.code == ERR.no_authentication:
                # Wrong username or password.
                session.msg({"alert": str(e)})
            else:
                session.msg({"alert": _("There was an error creating the Player: %s" % e)})

            return None

        if connect:
            session.msg({"login":{"name": username, "id": account.get_id()}})
            session.sessionhandler.login(session, account)
        else:
            session.msg({"created":{"name": session, "id": account.get_id()}})


class CmdQuitAccount(BaseCommand):
    """
    quit when in unlogged-in state

    Usage:
        {
            "cmd":"quit",
            "args":""
        }

    We maintain a different version of the quit command
    here for unconnected players for the sake of simplicity. The logged in
    version is a bit more complicated.
    """
    key = "quit"

    @classmethod
    def func(cls, session, args, context):
        #session.msg("Good bye! Disconnecting ...")
        session.sessionhandler.disconnect(session, "Good bye! Disconnecting.")


class CmdUnloginLook(BaseCommand):
    """
    login started unlogged-in state

    Usage:
        {
            "cmd": "unloggedin_look"
        }

    This is an unconnected version of the look command for simplicity.

    This is called by the server and kicks everything in gear.
    All it does is display the connect screen.
    """
    key = "unloggedin_look"

    @classmethod
    def func(cls, session, args, context):
        "Show the connect screen."
        game_name = GAME_SETTINGS.get("game_name")
        connection_screen = GAME_SETTINGS.get("connection_screen")
        honour_settings = HonourSettings.get_first_data()
        records = EquipmentPositions.all()
        equipment_pos = [{
            "key": r.key,
            "name": r.name,
            "desc": r.desc,
        } for r in records]

        session.msg({
            "game_name": game_name,
            "conn_screen": connection_screen,
            "equipment_pos": equipment_pos,
            "min_honour_level": honour_settings.min_honour_level,
        })
