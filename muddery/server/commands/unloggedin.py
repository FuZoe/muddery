"""
General commands usually availabe to all users.
"""

import re
import os
import time
import base64
from collections import defaultdict
from muddery.common.utils.exception import MudderyError, ERR
from muddery.server.settings import SETTINGS
from muddery.server.mappings.element_set import ELEMENT
from muddery.server.utils.logger import logger
from muddery.server.utils.crypto import RSA
from muddery.server.commands.base_command import BaseCommand, BaseRequest
from muddery.server.utils.localized_strings_handler import _
from muddery.server.utils.game_settings import GameSettings
from muddery.server.database.worlddata.equipment_positions import EquipmentPositions
from muddery.server.database.worlddata.honour_settings import HonourSettings
from muddery.server.commands.command_set import SessionCmd


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


@SessionCmd.request("first_connect")
async def first_connect(session, args):
    """
    Get the game's information for the first time connected to the server.

    Usage:
        {
            "cmd": "connect"
        }

    This is an unconnected version of the look command for simplicity.

    This is called by the server and kicks everything in gear.
    All it does is display the connect screen.
    """
    game_name = GameSettings.inst().get("game_name")
    connection_screen = GameSettings.inst().get("connection_screen")
    honour_settings = HonourSettings.get_first_data()
    records = EquipmentPositions.all()
    equipment_pos = [{
        "key": r.key,
        "name": r.name,
        "desc": r.desc,
    } for r in records]

    return {
        "game_name": game_name,
        "conn_screen": connection_screen,
        "equipment_pos": equipment_pos,
        "min_honour_level": honour_settings.min_honour_level,
    }


@SessionCmd.request("create_account")
async def create_account(session, args):
    """
    Respond the request of creating a new player account.

    Usage:
        {
            "cmd":"create_account",
            "args":{
                "playername":<playername>,
                "password":<password>,
            }
        }

    args:
        connect: (boolean)connect after created
    """
    if not args:
        raise MudderyError(ERR.missing_args, "Syntax error!")

    if "username" not in args:
        raise MudderyError(ERR.missing_args, "Need a username.")

    if "password" not in args:
        raise MudderyError(ERR.missing_args, "Need a password.")

    username = args["username"]
    username = re.sub(r"\s+", " ", username).strip()

    if SETTINGS.ENABLE_ENCRYPT:
        encrypted = base64.b64decode(args["password"])
        decrypted = RSA.inst().decrypt(encrypted)
        password = decrypted.decode("utf-8")
    else:
        password = args["password"]

    if not password:
        raise MudderyError(ERR.invalid_input, "Need a password.")

    # Create an account.
    element_type = SETTINGS.ACCOUNT_ELEMENT_TYPE
    account = ELEMENT(element_type)()

    # Set the account with username and password.
    await account.new_user(username, password, "")

    return {
        "name": username,
        "id": account.get_id()
    }


@SessionCmd.request("login")
async def login(session, args):
    """
    Login the game server.

    Usage:
        {
            "cmd":"connect",
            "args":{
                "playername":<playername>,
                "password":<password>
            }
        }

    """
    # check for too many login errors too quick.
    if _throttle(session, maxlim=5, timeout=5*60, storage=_LATEST_FAILED_LOGINS):
        # timeout is 5 minutes.
        await session.msg({"alert": _("{RYou made too many connection attempts. Try again in a few minutes.{n")})
        return

    if "username" not in args:
        await session.msg({"alert": _("You should input a username.")})
        return

    if "password" not in args:
        await session.msg({"alert": _("You should input a password.")})
        return

    username = args["username"]
    username = re.sub(r"\s+", " ", username).strip()

    if SETTINGS.ENABLE_ENCRYPT:
        encrypted = base64.b64decode(args["password"])
        decrypted = RSA.inst().decrypt(encrypted)
        password = decrypted.decode("utf-8")
    else:
        password = args["password"]

    if not password:
        await session.msg({"alert": _("You should input a password.")})
        return

    # Get the account.
    element_type = SETTINGS.ACCOUNT_ELEMENT_TYPE
    account = ELEMENT(element_type)()

    # Set the account with username and password.
    try:
        await account.set_user(username, password)
    except MudderyError as e:
        if e.code == ERR.no_authentication:
            # Wrong username or password.
            await session.msg({"alert": str(e)})
        else:
            await session.msg({"alert": _("You can not login.")})

        # this just updates the throttle
        _throttle(session)
        return None

    # actually do the login. This will call all other hooks:
    #   session.at_login()
    #   player.at_init()  # always called when object is loaded from disk
    #   player.at_first_login()  # only once, for player-centric setup
    #   player.at_pre_login()
    #   player.at_post_login(session=session)
    await session.login(account)


@SessionCmd.request("logout")
async def logout(session, args):
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
    await session.logout()

