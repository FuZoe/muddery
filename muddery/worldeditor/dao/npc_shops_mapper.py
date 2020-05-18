"""
Query and deal common tables.
"""

from evennia.utils import logger
from django.apps import apps
from django.conf import settings


class NPCShopsMapper(object):
    """
    NPC's shop.
    """
    def __init__(self):
        self.model_name = "npc_shops"
        self.model = apps.get_model(settings.WORLD_DATA_APP, self.model_name)
        self.objects = self.model.objects

    def filter(self, npc):
        """
        Get NPC's shop.

        Args:
            npc: (string) NPC's key.
        """
        return self.objects.filter(npc=npc)


NPC_SHOPS = NPCShopsMapper()

