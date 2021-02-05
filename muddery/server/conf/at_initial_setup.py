"""
At_initial_setup module template

Custom at_initial_setup method. This allows you to hook special
modifications to the initial server startup process. Note that this
will only be run once - when the server starts up for the very first
time! It is called last in the startup process and can thus be used to
overload things that happened before it.

The module must contain a global function at_initial_setup().  This
will be called without arguments. Note that tracebacks in this module
will be QUIETLY ignored, so make sure to check it well to make sure it
does what you expect it to.

"""

import os
from django.conf import settings
from evennia.utils import search
from muddery.server.utils import builder
from muddery.server.utils.game_settings import GAME_SETTINGS
import traceback

LIMBO_DESC = "Welcome to your new {wMuddery{n-based game! " +\
             "Visit http://www.muddery.org if you need help, " +\
             "want to contribute, report issues or just join the community."


def at_initial_setup():
    """
    Build up the default world and set default locations.
    """

    try:
        # load data
        from muddery.server.dao.worlddata import WorldData
        WorldData.reload()
        print("Reload world data.")

        # load game settings
        GAME_SETTINGS.reset()
        print("Reset game settings.")

        # build world
        builder.build_all()
        print("Builder build all.")

        # set limbo's desc
        limbo_obj = search.search_object("#2", exact=True)
        if limbo_obj:
            limbo_obj[0].db.desc = LIMBO_DESC
            limbo_obj[0].position = None
        print("Set limbo object.")

        # set default locations
        builder.reset_default_locations()
        print("Set default locations.")

        superuser = search.search_object("#1", exact=True)
        if superuser:
            superuser = superuser[0]

            # move the superuser to the start location
            start_location = search.search_object(settings.START_LOCATION, exact=True)
            if start_location:
                start_location = start_location[0]
                superuser.move_to(start_location, quiet=True)

            # set superuser's data
            superuser.set_data_key(GAME_SETTINGS.get("default_staff_character_key"), 1)
            superuser.set_nickname("superuser")
            print("Set superuser.")

    except Exception as e:
        ostring = "Can't set initial data: %s" % e
        print(ostring)
        print(traceback.format_exc())
