"""
Upgrade custom's game dir to the latest version.
"""

import os, traceback
import muddery
from muddery.launcher.upgrader import utils
from muddery.launcher.upgrader import upgrader_0_7_0
from muddery.launcher import utils as launcher_utils
from muddery.server.utils.exception import MudderyError, ERR


class UpgradeHandler(object):
    """
    Upgrade custom's game dir to the latest version.
    """
    def __init__(self):
        """
        Add upgraders.
        """
        self.upgrader_list = []
        self.upgrader_list.append(upgrader_0_7_0.Upgrader())

    def upgrade_game(self, game_dir, template, muddery_lib):
        # Get first two version numbers.
        if not os.path.exists(game_dir):
            print("\nCan not find dir '%s'.\n" % game_dir)
            return

        # Get game config
        game_ver, game_template = launcher_utils.get_game_config(game_dir)
        ver_str = ".".join([str(v) for v in game_ver])
        print("Current game's version is %s." % ver_str)

        if not template:
            template = game_template

        # Get proper upgrader.
        upgrader = self.get_upgrader(game_ver)
        if not upgrader:
            print("\nYour game does not need upgrade.\n")
            return

        try:
            # backup current game dir
            utils.make_backup(game_dir)

            # do upgrade
            upgrader.upgrade_game(game_dir, template, muddery_lib)
            print("\nYour game has been upgraded to muddery version %s.\n" % muddery.__version__)

            # create config file
            launcher_utils.create_config_file(game_dir, template)

        except MudderyError as e:
            if e.code != ERR.can_not_upgrade:
                traceback.print_exc()
                print("\nUpgrade failed: %s\n" % e)
        except Exception as e:
            traceback.print_exc()
            print("\nUpgrade failed: %s\n" % e)

        return

    def upgrade_data(self, data_path, template, muddery_lib):
        """
        Upgrade game data.

        Args:
            data_path: (string) the path of game data.

        Returns:
            None
        """
        # Get game config
        game_ver, game_template = launcher_utils.get_game_config(data_path)
        ver_str = ".".join([str(v) for v in game_ver])
        print("Data's version is %s." % ver_str)

        if not template:
            template = game_template

        # Get proper upgrader.
        upgrader = self.get_upgrader(game_ver)
        if not upgrader:
            # Does not need upgrade.
            return

        try:
            upgrader.upgrade_data(data_path, template, muddery_lib)
            print("\nYour game data have been upgraded to muddery version %s.\n" % muddery.__version__)

        except Exception as e:
            print("\nUpgrade failed: %s\n" % e)

    def get_upgrader(self, game_ver):
        """
        Get a proper upgrader according the data version.

        Args:
            game_ver: (tuple) version number's list.

        Returns:
            Game upgrader.
        """
        for upgrader in self.upgrader_list:
            if upgrader.can_upgrade(game_ver):
                return upgrader
        return None

    def can_upgrade(self, game_ver):
        """
        Check if the game need upgrade.

        Args:
            game_ver: (tuple) version number's list.

        Returns:
            (bool)need upgrade or not
        """
        for upgrader in self.upgrader_list:
            if upgrader.can_upgrade(game_ver):
                return True
        return False

UPGRADE_HANDLER = UpgradeHandler()
