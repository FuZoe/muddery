"""
Query and deal common tables.
"""

from evennia.utils import logger
from django.apps import apps
from django.conf import settings


class DialoguesMapper(object):
    """
    NPC's dialogue list.
    """
    def __init__(self):
        self.model_name = "dialogues"
        self.model = apps.get_model(settings.WORLD_DATA_APP, self.model_name)
        self.objects = self.model.objects

    def get(self, key):
        """
        Get dialogues.

        Args:
            key: (string) dialogue's key.
        """
        return self.objects.get(key=key)


DIALOGUES = DialoguesMapper()

