"""
This model translates default strings into localized strings.
"""

from collections import deque
import time
import math
from django.conf import settings
from twisted.internet import reactor
from twisted.internet import task
from evennia.utils import logger
from evennia import create_script
from evennia.utils.search import search_object
from muddery.server.dao.honours_mapper import HONOURS_MAPPER
from muddery.server.utils.localized_strings_handler import _


class MatchQueueHandler(object):
    """
    This model translates default strings into localized strings.
    """
    max_candidates = 20
    max_honour_diff = 200
    min_waiting_time = 5
    preparing_time = 15
    ave_samples_number = 20
    match_interval = 10
    
    def __init__(self):
        """
        Initialize handler
        """
        self.queue = deque()
        self.waiting_time = {}
        self.preparing = {}
        self.ave_samples = deque()
        self.ave_waiting = -1
        
        self.loop = task.LoopingCall(self.match)
        self.loop.start(self.match_interval)
        
    def __del__(self):
        """
        Clear all resources.
        """
        if self.loop and self.loop.running:
            self.loop.stop()

    def add(self, character):
        """
        Add a character to the queue.
        """
        character_id = character.id

        if character_id in self.waiting_time:
            return
        
        self.queue.append(character_id)
        self.waiting_time[character_id] = time.time()
        character.msg({"in_combat_queue": self.ave_waiting})

    def remove_by_id(self, character_id):
        """
        Remove a character from the queue.
        """
        character = search_object("#%s" % character_id)
        if character:
            self.remove(character[0])

    def remove(self, character):
        """
        Remove a character from the queue.
        """
        character_id = character.id

        if character_id in self.waiting_time:
            del self.waiting_time[character_id]
            self.queue.remove(character_id)

        if character_id in self.preparing:
            del self.preparing[character_id]

        character.msg({"left_combat_queue": ""})

    def match(self):
        """
        Match opponents according to character's scores.
        The longer a character in the queue, the score is higher.
        The nearer of two character's rank, the score is higher.
        """
        if len(self.queue) < 2:
            return

        time_now = time.time()
        candidates = []
        count = 0
        max = self.max_candidates
        for id in self.queue:
            if count >= max:
                break
                
            if id in self.preparing:
                continue
                
            characters = search_object("#%s" % id)
            if not characters or characters[0].is_in_combat():
                continue

            candidates.append(id)
            count += 1

        max_score = 0
        opponents = ()
        for i in range(len(candidates) - 1):
            for j in range(i + 1, len(candidates)):
                score_A = time_now - self.waiting_time[candidates[i]]
                score_B = time_now - self.waiting_time[candidates[j]]
                honour_A = HONOURS_MAPPER.get_honour_by_id(candidates[i], 0)
                honour_B = HONOURS_MAPPER.get_honour_by_id(candidates[j], 0)
                score_C = self.max_honour_diff - math.fabs(honour_A - honour_B)

                if score_A <= self.min_waiting_time or score_B <= self.min_waiting_time or score_C <= 0:
                    break

                score = score_A + score_B + score_C
                if score > max_score:
                    max_score = score
                opponents = candidates[i], candidates[j]
        
        if opponents:
            self.preparing[opponents[0]] = {"time": time.time(),
                                            "opponent": opponents[1],
                                            "confirmed": False}
            self.preparing[opponents[1]] = {"time": time.time(),
                                            "opponent": opponents[0],
                                            "confirmed": False}
            character_A = search_object("#%s" % opponents[0])
            character_B = search_object("#%s" % opponents[1])
            if character_A:
                character_A[0].msg({"prepare_match": self.preparing_time})
            if character_B:
                character_B[0].msg({"prepare_match": self.preparing_time})
            
            call_id = reactor.callLater(self.preparing_time, self.fight, opponents)
            self.preparing[opponents[0]]["call_id"] = call_id
            self.preparing[opponents[1]]["call_id"] = call_id

            self.ave_samples.append(time_now - self.waiting_time[opponents[0]])
            self.ave_samples.append(time_now - self.waiting_time[opponents[1]])

            while len(self.ave_samples) > self.ave_samples_number:
                self.ave_samples.popleft()

            self.ave_waiting = float(sum(self.ave_samples)) / len(self.ave_samples)

    def confirm(self, character):
        """
        Confirm an honour combat.
        """
        character_id = character.id
        if character_id not in self.preparing:
            return
            
        self.preparing[character_id]["confirmed"] = True

    def reject(self, character):
        """
        Reject an honour combat.
        """
        character_id = character.id
        if character_id not in self.preparing:
            return

        # stop the call
        call_id = self.preparing[character_id]["call_id"]
        call_id.cancel()
        
        # remove characters from the preparing queue
        opponent_id = self.preparing[character_id]["opponent"]

        character = search_object("#%s" % character_id)
        if character:
            character[0].msg({"match_rejected": character_id})
            del self.preparing[character_id]

        opponent = search_object("#%s" % opponent_id)
        if opponent:
            opponent[0].msg({"match_rejected": character_id})
            del self.preparing[opponent_id]

        self.remove_by_id(character_id)

    def fight(self, opponents):
        """
        Create a combat.
        """
        confirmed0 = opponents[0] in self.preparing and self.preparing[opponents[0]]["confirmed"]
        confirmed1 = opponents[1] in self.preparing and self.preparing[opponents[1]]["confirmed"]

        if not confirmed0 and not confirmed1:
            self.remove_by_id(opponents[0])
            self.remove_by_id(opponents[1])

            opponent0 = search_object("#%s" % opponents[0])
            opponent0[0].msg({"match_rejected": opponents[0],
                              "left_combat_queue": ""})
            opponent1 = search_object("#%s" % opponents[1])
            opponent1[0].msg({"match_rejected": opponents[1],
                              "left_combat_queue": ""})
        elif not confirmed0:
            # opponents 0 not confirmed
            self.remove_by_id(opponents[0])
            if opponents[1] in self.preparing:
                del self.preparing[opponents[1]]

            opponent0 = search_object("#%s" % opponents[0])
            opponent0[0].msg({"match_rejected": opponents[0],
                              "left_combat_queue": ""})

            opponent1 = search_object("#%s" % opponents[1])
            opponent1[0].msg({"match_rejected": opponents[0]})
        elif not confirmed1:
            # opponents 1 not confirmed
            self.remove_by_id(opponents[1])
            if opponents[0] in self.preparing:
                del self.preparing[opponents[0]]

            opponent1 = search_object("#%s" % opponents[1])
            opponent1[0].msg({"match_rejected": opponents[1],
                              "left_combat_queue": ""})

            opponent0 = search_object("#%s" % opponents[0])
            opponent0[0].msg({"match_rejected": opponents[1]})
        elif confirmed0 and confirmed1:
            # all confirmed
            opponent0 = search_object("#%s" % opponents[0])
            opponent1 = search_object("#%s" % opponents[1])
            # create a new combat handler
            chandler = create_script(settings.HONOUR_COMBAT_HANDLER)
            # set combat team and desc
            chandler.set_combat({1:[opponent0[0]], 2:[opponent1[0]]}, _("Fight of Honour"), settings.AUTO_COMBAT_TIMEOUT)

            self.remove_by_id(opponents[0])
            self.remove_by_id(opponents[1])


# main handler
MATCH_QUEUE_HANDLER = MatchQueueHandler()
