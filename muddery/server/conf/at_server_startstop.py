"""
Server startstop hooks

This module contains functions called by Evennia at various
points during its startup, reload and shutdown sequence. It
allows for customizing the server operation as desired.

This module must contain at least these global functions:

at_server_start()
at_server_stop()
at_server_reload_start()
at_server_reload_stop()
at_server_cold_start()
at_server_cold_stop()

"""

import traceback


def at_server_start():
    """
    This is called every time the server starts up, regardless of
    how it was shut down.
    """
    print("server start")

    # load data
    from muddery.server.database.worlddata.worlddata import WorldData
    WorldData.reload()
    print("WorldData loaded.")

    # reset settings
    from muddery.server.utils.game_settings import GAME_SETTINGS
    GAME_SETTINGS.reset()
    print("GAME_SETTINGS loaded.")

    # reload local strings
    from muddery.server.utils.localized_strings_handler import LOCALIZED_STRINGS_HANDLER
    LOCALIZED_STRINGS_HANDLER.reload()
    print("LOCALIZED_STRINGS_HANDLER loaded.")

    # clear dialogues
    from muddery.server.utils.dialogue_handler import DIALOGUE_HANDLER
    DIALOGUE_HANDLER.clear()
    print("DIALOGUE_HANDLER loaded.")

    # reload equipment types
    from muddery.server.utils.equip_type_handler import EQUIP_TYPE_HANDLER
    EQUIP_TYPE_HANDLER.reload()
    print("EQUIP_TYPE_HANDLER loaded.")

    # localize model fields
    from muddery.server.utils.localiztion_handler import localize_model_fields
    localize_model_fields()
    print("localize_model_fields loaded.")

    # load honours
    from muddery.server.database.gamedata.honours_mapper import HONOURS_MAPPER
    HONOURS_MAPPER.reload()
    print("HONOURS_MAPPER loaded.")

    # create the world
    try:
        from muddery.server.server import Server
        Server.create_the_world()
        print("The world has been created.")
    except Exception as e:
        traceback.print_exc()


def at_server_stop():
    """
    This is called just before the server is shut down, regardless
    of it is for a reload, reset or shutdown.
    """
    pass


def at_server_reload_start():
    """
    This is called only when server starts back up after a reload.
    """
    pass


def at_server_reload_stop():
    """
    This is called only time the server stops before a reload.
    """
    pass


def at_server_cold_start():
    """
    This is called only when the server starts "cold", i.e. after a
    shutdown or a reset.
    """
    pass


def at_server_cold_stop():
    """
    This is called only when the server goes down due to a shutdown or
    reset.
    """
    pass
