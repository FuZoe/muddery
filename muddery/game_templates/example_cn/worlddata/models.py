from django.db import models
from muddery.worlddata.db import models as BaseModels


# ------------------------------------------------------------
#
# The game world system's data.
#
# ------------------------------------------------------------
class system_data(BaseModels.system_data):
    """
    The game world system's data.
    """
    pass


# ------------------------------------------------------------
#
# game's basic settings
#
# ------------------------------------------------------------
class game_settings(BaseModels.game_settings):
    """
    Game's basic settings.
    """
    pass


# ------------------------------------------------------------
#
# all objects
#
# ------------------------------------------------------------
class objects(BaseModels.objects):
    "All objects in the game."
    pass


# ------------------------------------------------------------
#
# world areas
#
# ------------------------------------------------------------
class world_areas(BaseModels.world_areas):
    "Rooms belongs to areas."
    pass
    

#------------------------------------------------------------
#
# store all rooms
#
#------------------------------------------------------------
class world_rooms(BaseModels.world_rooms):
    "Store all unique rooms."
    pass


#------------------------------------------------------------
#
# store all exits
#
#------------------------------------------------------------
class world_exits(BaseModels.world_exits):
    "Store all unique exits."
    pass


#------------------------------------------------------------
#
# store exit locks
#
#------------------------------------------------------------
class exit_locks(BaseModels.exit_locks):
    "Store all exit locks."
    pass


#------------------------------------------------------------
#
# store all objects
#
#------------------------------------------------------------
class world_objects(BaseModels.world_objects):
    "Store all unique objects."
    pass


#------------------------------------------------------------
#
# store all object creators
#
#------------------------------------------------------------
class object_creators(BaseModels.object_creators):
    "Store all object creators."
    pass


#------------------------------------------------------------
#
# object creator's loot list
#
#------------------------------------------------------------
class creator_loot_list(BaseModels.creator_loot_list):
    "Object creator's loot list"
    pass


#------------------------------------------------------------
#
# store all common objects
#
#------------------------------------------------------------
class common_objects(BaseModels.common_objects):
    "Store all common objects."
    pass


# ------------------------------------------------------------
#
# store all foods
#
# ------------------------------------------------------------
class foods(BaseModels.foods):
    "Foods inherit from common objects."
    pass


# ------------------------------------------------------------
#
# store all skill books
#
# ------------------------------------------------------------
class skill_books(BaseModels.skill_books):
    "Skill books inherit from common objects."
    pass
    

#------------------------------------------------------------
#
# store all equip_types
#
#------------------------------------------------------------
class equipment_types(BaseModels.equipment_types):
    "Store all equip types."
    pass


#------------------------------------------------------------
#
# store all equip_positions
#
#------------------------------------------------------------
class equipment_positions(BaseModels.equipment_positions):
    "Store all equip types."
    pass


#------------------------------------------------------------
#
# store all equipments
#
#------------------------------------------------------------
class equipments(BaseModels.equipments):
    "Store all equipments."
    pass


# ------------------------------------------------------------
#
# Object's custom properties.
#
# ------------------------------------------------------------
class properties_dict(BaseModels.properties_dict):
    """
    Object's custom properties.
    """
    pass


# ------------------------------------------------------------
#
# Object's custom properties
#
# ------------------------------------------------------------
class object_properties(BaseModels.object_properties):
    "Store object's custom properties."
    pass


#------------------------------------------------------------
#
# store all npcs
#
#------------------------------------------------------------
class world_npcs(BaseModels.world_npcs):
    "Store all unique objects."
    pass


class base_npcs(BaseModels.base_npcs):
    pass


class common_npcs(BaseModels.common_npcs):
    pass


class player_characters(BaseModels.player_characters):
    pass


#------------------------------------------------------------
#
# store common characters
#
#------------------------------------------------------------
class characters(BaseModels.characters):
    "Store all common characters."
    pass


#------------------------------------------------------------
#
# character's loot list
#
#------------------------------------------------------------
class character_loot_list(BaseModels.character_loot_list):
    "Character's loot list"
    pass


#------------------------------------------------------------
#
# character's default objects
#
#------------------------------------------------------------
class default_objects(BaseModels.default_objects):
    "Store character's default objects information."
    pass
    

# ------------------------------------------------------------
#
# shops
#
# ------------------------------------------------------------
class shops(BaseModels.shops):
    "Store all shops."
    pass
        
        
# ------------------------------------------------------------
#
# shop goods
#
# ------------------------------------------------------------
class shop_goods(BaseModels.shop_goods):
    "All goods that sold in shops."
    pass


# ------------------------------------------------------------
#
# npc shops
#
# ------------------------------------------------------------
class npc_shops(BaseModels.npc_shops):
    "Store npc's shops."
    pass
    
    
#------------------------------------------------------------
#
# store all skills
#
#------------------------------------------------------------
class skills(BaseModels.skills):
    "Store all skills."
    pass


# ------------------------------------------------------------
#
# skill types
#
# ------------------------------------------------------------
class skill_types(BaseModels.skill_types):
    "Skill's types."
    pass


#------------------------------------------------------------
#
# character skills
#
#------------------------------------------------------------
class default_skills(BaseModels.default_skills):
    "Store all character skill informations."
    pass


#------------------------------------------------------------
#
# store all quests
#
#------------------------------------------------------------
class quests(BaseModels.quests):
    "Store all dramas."
    pass


#------------------------------------------------------------
#
# quest's reward list
#
#------------------------------------------------------------
class quest_reward_list(BaseModels.quest_reward_list):
    "Quest's reward list"
    pass


#------------------------------------------------------------
#
# store quest objectives
#
#------------------------------------------------------------
class quest_objectives(BaseModels.quest_objectives):
    "Store all quest objectives."
    pass


#------------------------------------------------------------
#
# store quest dependencies
#
#------------------------------------------------------------
class quest_dependencies(BaseModels.quest_dependencies):
    "Store quest dependency."
    pass


#------------------------------------------------------------
#
# store event data
#
#------------------------------------------------------------
class event_data(BaseModels.event_data):
    "Store event data."
    pass


#------------------------------------------------------------
#
# store all dialogues
#
#------------------------------------------------------------
class dialogues(BaseModels.dialogues):
    "Store all dialogues."
    pass


#------------------------------------------------------------
#
# store dialogue quest dependencies
#
#------------------------------------------------------------
class dialogue_quest_dependencies(BaseModels.dialogue_quest_dependencies):
    "Store dialogue quest dependencies."
    pass


#------------------------------------------------------------
#
# store dialogue relations
#
#------------------------------------------------------------
class dialogue_relations(BaseModels.dialogue_relations):
    "Store dialogue relations."
    pass


#------------------------------------------------------------
#
# store dialogue sentences
#
#------------------------------------------------------------
class dialogue_sentences(BaseModels.dialogue_sentences):
    "Store dialogue sentences."
    pass


#------------------------------------------------------------
#
# store npc's dialogue
#
#------------------------------------------------------------
class npc_dialogues(BaseModels.npc_dialogues):
    "Store all dialogues."
    pass


# ------------------------------------------------------------
#
# action to attack a target
#
# ------------------------------------------------------------
class action_attack(BaseModels.action_attack):
    "event attack's data"
    pass


#------------------------------------------------------------
#
# action to begin a dialogue
#
#------------------------------------------------------------
class action_dialogue(BaseModels.action_dialogue):
    pass


#------------------------------------------------------------
#
# action to learn a skill
#
#------------------------------------------------------------
class action_learn_skill(BaseModels.action_learn_skill):
    pass


#------------------------------------------------------------
#
# action to accept a quest
#
#------------------------------------------------------------
class action_accept_quest(BaseModels.action_accept_quest):
    pass


#------------------------------------------------------------
#
# action to turn in a quest
#
#------------------------------------------------------------
class action_turn_in_quest(BaseModels.action_turn_in_quest):
    pass


# ------------------------------------------------------------
#
# action to close an event
#
# ------------------------------------------------------------
class action_close_event(BaseModels.action_close_event):
    pass


# ------------------------------------------------------------
#
# action to send a message to the character
#
# ------------------------------------------------------------
class action_message(BaseModels.action_message):
    pass


# ------------------------------------------------------------
#
# action to trigger other actions at interval.
#
# ------------------------------------------------------------
class action_room_interval(BaseModels.action_room_interval):
    pass


# ------------------------------------------------------------
#
# action to add objects to characters
#
# ------------------------------------------------------------
class action_get_objects(BaseModels.action_get_objects):
    pass


# ------------------------------------------------------------
#
# condition descriptions
#
# ------------------------------------------------------------
class condition_desc(BaseModels.condition_desc):
    "Object descriptions in different conditions."
    pass


#------------------------------------------------------------
#
# localized strings
#
#------------------------------------------------------------
class localized_strings(BaseModels.localized_strings):
    "Store all system localized strings."
    pass


#------------------------------------------------------------
#
# image resources
#
#------------------------------------------------------------
class image_resources(BaseModels.image_resources):
    "Store all image resource's information."
    pass
