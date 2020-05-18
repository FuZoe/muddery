
from django.contrib.admin.forms import forms
from muddery.utils.localiztion_handler import localize_form_fields
from muddery.mappings.quest_objective_set import QUEST_OBJECTIVE_SET
from muddery.mappings.quest_status_set import QUEST_STATUS_SET
from muddery.mappings.event_action_set import EVENT_ACTION_SET
from muddery.mappings.event_trigger_set import EVENT_TRIGGER_SET
from muddery.mappings.typeclass_set import TYPECLASS_SET
from muddery.worlddata.dao import model_mapper
from muddery.worlddata.dao import common_mappers as CM
from muddery.worlddata.forms.location_field import LocationField
from muddery.worlddata.forms.image_field import ImageField


def get_all_objects():
    """
    Get all objects.
    """
    records = CM.OBJECTS.all()
    return [(r.key, r.name + " (" + r.key + ")") for r in records]


def get_all_pocketable_objects():
    """
    Get all objects that can be put in player's pockets.
    """
    records = CM.COMMON_OBJECTS.all_with_base()
    return [(r["key"], r["name"] + " (" + r["key"] + ")") for r in records]


def generate_key(form_obj):
    """
    Generate a key for a new record.

    Args:
        form_obj: record's form.
    """
    index = 1
    if form_obj.instance.id:
        index = int(form_obj.instance.id)
    else:
        try:
            # Get last id.
            query = form_obj.Meta.model.objects.last()
            index = int(query.id)
            index += 1
        except Exception as e:
            pass

    return form_obj.instance.__class__.__name__ + "_" + str(index)


class GameSettingsForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(GameSettingsForm, self).__init__(*args, **kwargs)
        
        choices = [("", "---------")]
        objects = CM.WORLD_ROOMS.all_with_base()
        choices.extend([(obj["key"], obj["name"] + " (" + obj["key"] + ")") for obj in objects])
        self.fields['default_home_key'] = forms.ChoiceField(choices=choices, required=False)
        self.fields['start_location_key'] = forms.ChoiceField(choices=choices, required=False)
        self.fields['default_player_home_key'] = forms.ChoiceField(choices=choices, required=False)

        choices = [("", "---------")]
        objects = CM.CHARACTERS.all_with_base()
        choices.extend([(obj["key"], obj["name"] + " (" + obj["key"] + ")") for obj in objects
                            if obj["typeclass"]=="PLAYER_CHARACTER"])
        self.fields['default_player_character_key'] = forms.ChoiceField(choices=choices, required=False)

        localize_form_fields(self)

    class Meta:
        model = CM.GAME_SETTINGS.model
        fields = '__all__'
        list_template = "common_list.html"
        form_template = "common_form.html"


class EquipmentTypesForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(EquipmentTypesForm, self).__init__(*args, **kwargs)
        localize_form_fields(self)

    class Meta:
        model = CM.EQUIPMENT_TYPES.model
        fields = '__all__'


class EquipmentPositionsForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(EquipmentPositionsForm, self).__init__(*args, **kwargs)
        localize_form_fields(self)

    class Meta:
        model = CM.EQUIPMENT_POSITIONS.model
        fields = '__all__'


class ObjectsForm(forms.ModelForm):
    """
    Objects base form.
    """
    def __init__(self, *args, **kwargs):
        super(ObjectsForm, self).__init__(*args, **kwargs)
        localize_form_fields(self)

    class Meta:
        model = CM.OBJECTS.model
        fields = '__all__'


class WorldAreasForm(ObjectsForm):
    def __init__(self, *args, **kwargs):
        super(WorldAreasForm, self).__init__(*args, **kwargs)

        self.fields['background'] = ImageField(image_type="background", required=False)

        localize_form_fields(self)

    class Meta:
        model = CM.WORLD_AREAS.model
        fields = '__all__'
        

class WorldRoomsForm(ObjectsForm):
    def __init__(self, *args, **kwargs):
        super(WorldRoomsForm, self).__init__(*args, **kwargs)

        choices = [("", "---------")]
        objects = CM.WORLD_AREAS.all_with_base()
        choices.extend([(obj["key"], obj["name"] + " (" + obj["key"] + ")") for obj in objects])
        self.fields['location'] = forms.ChoiceField(choices=choices)

        self.fields['icon'] = ImageField(image_type="icon", required=False)

        self.fields['background'] = ImageField(image_type="background", required=False)

        localize_form_fields(self)

    class Meta:
        model = CM.WORLD_ROOMS.model
        fields = '__all__'


class WorldExitsForm(ObjectsForm):
    def __init__(self, *args, **kwargs):
        super(WorldExitsForm, self).__init__(*args, **kwargs)

        rooms = CM.WORLD_ROOMS.all_with_base()
        choices = [(r["key"], r["name"] + " (" + r["key"] + ")") for r in rooms]
        self.fields['location'] = LocationField(choices=choices)
        self.fields['destination'] = LocationField(choices=choices)

        localize_form_fields(self)

    class Meta:
        model = CM.WORLD_EXITS.model
        fields = '__all__'


class ExitLocksForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(ExitLocksForm, self).__init__(*args, **kwargs)

        #objects = models.world_exits.objects.filter(typeclass="CLASS_LOCKED_EXIT")
        #choices = [(obj.key, obj.name + " (" + obj.key + ")") for obj in objects]
        #self.fields['key'] = forms.ChoiceField(choices=choices)

        localize_form_fields(self)

    class Meta:
        model = CM.EXIT_LOCKS.model
        fields = '__all__'


class WorldObjectsForm(ObjectsForm):
    def __init__(self, *args, **kwargs):
        super(WorldObjectsForm, self).__init__(*args, **kwargs)

        rooms = CM.WORLD_ROOMS.all_with_base()
        choices = [(r["key"], r["name"] + " (" + r["key"] + ")") for r in rooms]
        self.fields['location'] = LocationField(choices=choices)

        self.fields['icon'] = ImageField(image_type="icon", required=False)

        localize_form_fields(self)

    class Meta:
        model = CM.WORLD_OBJECTS.model
        fields = '__all__'


class WorldNPCsForm(ObjectsForm):
    def __init__(self, *args, **kwargs):
        super(WorldNPCsForm, self).__init__(*args, **kwargs)
        
        # NPC's location
        rooms = CM.WORLD_ROOMS.all_with_base()
        choices = [(r["key"], r["name"] + " (" + r["key"] + ")") for r in rooms]
        self.fields['location'] = LocationField(choices=choices)

        localize_form_fields(self)

    class Meta:
        model = CM.WORLD_NPCS.model
        fields = '__all__'


class ObjectCreatorsForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(ObjectCreatorsForm, self).__init__(*args, **kwargs)

        #objects = models.world_objects.objects.filter(typeclass="CLASS_OBJECT_CREATOR")
        #choices = [(obj.key, obj.name + " (" + obj.key + ")") for obj in objects]
        #self.fields['key'] = forms.ChoiceField(choices=choices)

        localize_form_fields(self)

    class Meta:
        model = CM.OBJECT_CREATORS.model
        fields = '__all__'


class CreatorLootListForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(CreatorLootListForm, self).__init__(*args, **kwargs)

        # providers must be object_creators
        objects = CM.OBJECT_CREATORS.all_with_base()
        choices = [(obj["key"], obj["name"] + " (" + obj["key"] + ")") for obj in objects]
        self.fields['provider'] = forms.ChoiceField(choices=choices)

        # available objects
        choices = get_all_pocketable_objects()
        self.fields['object'] = forms.ChoiceField(choices=choices)
        
        # depends on quest
        choices = [("", "---------")]
        objects = CM.QUESTS.all_with_base()
        choices.extend([(obj["key"], obj["name"] + " (" + obj["key"] + ")") for obj in objects])
        self.fields['quest'] = forms.ChoiceField(choices=choices, required=False)

        localize_form_fields(self)

    class Meta:
        model = CM.CREATOR_LOOT_LIST.model
        fields = '__all__'


class CharacterLootListForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(CharacterLootListForm, self).__init__(*args, **kwargs)

        # providers can be world_npc or common_character
        npcs = CM.WORLD_NPCS.all_with_base()
        choices = [(obj["key"], obj["name"] + " (" + obj["key"] + ")") for obj in npcs]

        characters = CM.CHARACTERS.all_with_base()
        choices.extend([(obj["key"], obj["name"] + " (" + obj["key"] + ")") for obj in characters])

        self.fields['provider'] = forms.ChoiceField(choices=choices)

        # available objects
        choices = get_all_pocketable_objects()
        self.fields['object'] = forms.ChoiceField(choices=choices)

        # depends on quest
        choices = [("", "---------")]
        objects = CM.QUESTS.all_with_base()
        choices.extend([(obj["key"], obj["name"] + " (" + obj["key"] + ")") for obj in objects])
        self.fields['quest'] = forms.ChoiceField(choices=choices, required=False)

        localize_form_fields(self)
        
    class Meta:
        model = CM.CHARACTER_LOOT_LIST.model
        fields = '__all__'


class QuestRewardListForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(QuestRewardListForm, self).__init__(*args, **kwargs)

        # providers must be object_creators
        objects = CM.QUESTS.all_with_base()
        choices = [(obj["key"], obj["name"] + " (" + obj["key"] + ")") for obj in objects]
        self.fields['provider'] = forms.ChoiceField(choices=choices)

        # available objects
        choices = get_all_pocketable_objects()
        self.fields['object'] = forms.ChoiceField(choices=choices)
        
        # depends on quest
        choices = [("", "---------")]
        objects = CM.QUESTS.all_with_base()
        choices.extend([(obj["key"], obj["name"] + " (" + obj["key"] + ")") for obj in objects])
        self.fields['quest'] = forms.ChoiceField(choices=choices, required=False)

        localize_form_fields(self)

    class Meta:
        model = CM.QUEST_REWARD_LIST.model
        fields = '__all__'


class CommonObjectsForm(ObjectsForm):
    def __init__(self, *args, **kwargs):
        super(CommonObjectsForm, self).__init__(*args, **kwargs)
        
        self.fields['icon'] = ImageField(image_type="icon", required=False)

        localize_form_fields(self)

    class Meta:
        model = CM.COMMON_OBJECTS.model
        fields = '__all__'


class FoodsForm(ObjectsForm):
    def __init__(self, *args, **kwargs):
        super(FoodsForm, self).__init__(*args, **kwargs)

        localize_form_fields(self)

    class Meta:
        model = CM.FOODS.model
        fields = '__all__'
        

class SkillBooksForm(ObjectsForm):
    def __init__(self, *args, **kwargs):
        super(SkillBooksForm, self).__init__(*args, **kwargs)
        
        # skills
        objects = CM.SKILLS.all_with_base()
        choices = [(obj["key"], obj["name"] + " (" + obj["key"] + ")") for obj in objects]
        self.fields['skill'] = forms.ChoiceField(choices=choices)

        localize_form_fields(self)

    class Meta:
        model = CM.SKILL_BOOKS.model
        fields = '__all__'


class PropertiesDictForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(PropertiesDictForm, self).__init__(*args, **kwargs)
        localize_form_fields(self)

    class Meta:
        model = CM.PROPERTIES_DICT.model
        fields = '__all__'


class CharactersForm(ObjectsForm):
    def __init__(self, *args, **kwargs):
        super(CharactersForm, self).__init__(*args, **kwargs)

        self.fields['icon'] = ImageField(image_type="icon", required=False)

        choices = [("", "---------")]
        characters = CM.CHARACTERS.all_with_base()
        choices.extend([(obj["key"], obj["name"] + " (" + obj["key"] + ")") for obj in characters])
        self.fields['clone'] = forms.ChoiceField(choices=choices, required=False)

        localize_form_fields(self)

    class Meta:
        model = CM.CHARACTERS.model
        fields = '__all__'


class BaseNPCsForm(ObjectsForm):
    def __init__(self, *args, **kwargs):
        super(BaseNPCsForm, self).__init__(*args, **kwargs)
        localize_form_fields(self)

    class Meta:
        model = CM.BASE_NPCS.model
        fields = '__all__'


class CommonNPCsForm(ObjectsForm):
    def __init__(self, *args, **kwargs):
        super(CommonNPCsForm, self).__init__(*args, **kwargs)
        localize_form_fields(self)

    class Meta:
        model = CM.COMMON_NPCS.model
        fields = '__all__'


class PlayerCharactersForm(ObjectsForm):
    def __init__(self, *args, **kwargs):
        super(PlayerCharactersForm, self).__init__(*args, **kwargs)
        localize_form_fields(self)

    class Meta:
        model = CM.PLAYER_CHARACTERS.model
        fields = '__all__'


class DefaultObjectsForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(DefaultObjectsForm, self).__init__(*args, **kwargs)

        # all character's
        objects = CM.CHARACTERS.all_with_base()
        choices = [(obj["key"], obj["name"] + " (" + obj["key"] + ")") for obj in objects]
        self.fields['character'] = forms.ChoiceField(choices=choices)

        # available objects
        choices = get_all_pocketable_objects()
        self.fields['object'] = forms.ChoiceField(choices=choices)

        localize_form_fields(self)
        
    class Meta:
        model = CM.DEFAULT_OBJECTS.model
        fields = '__all__'


class ShopsForm(ObjectsForm):
    def __init__(self, *args, **kwargs):
        super(ShopsForm, self).__init__(*args, **kwargs)
        
        self.fields['icon'] = ImageField(image_type="icon", required=False)
        
        localize_form_fields(self)
        
    class Meta:
        model = CM.SHOPS.model
        fields = '__all__'


class ShopGoodsForm(ObjectsForm):
    def __init__(self, *args, **kwargs):
        super(ShopGoodsForm, self).__init__(*args, **kwargs)

        # all shops
        objects = CM.SHOPS.all_with_base()
        choices = [(obj["key"], obj["name"] + " (" + obj["key"] + ")") for obj in objects]
        self.fields['shop'] = forms.ChoiceField(choices=choices)

        # available objects
        choices = get_all_pocketable_objects()
        self.fields['goods'] = forms.ChoiceField(choices=choices)

        # available units are common objects
        objects = CM.COMMON_OBJECTS.all_with_base()
        choices = [(obj["key"], obj["name"] + " (" + obj["key"] + ")") for obj in objects]
        self.fields['unit'] = forms.ChoiceField(choices=choices)

        localize_form_fields(self)
        
    class Meta:
        model = CM.SHOP_GOODS.model
        fields = '__all__'


class NPCShopsForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(NPCShopsForm, self).__init__(*args, **kwargs)

        # All NPCs.
        objects = CM.WORLD_NPCS.all_with_base()
        choices = [(obj["key"], obj["name"] + " (" + obj["key"] + ")") for obj in objects]
        self.fields['npc'] = forms.ChoiceField(choices=choices)
        
        # All shops.
        objects = CM.SHOPS.all_with_base()
        choices = [(obj["key"], obj["name"] + " (" + obj["key"] + ")") for obj in objects]
        self.fields['shop'] = forms.ChoiceField(choices=choices)

        localize_form_fields(self)
        
    class Meta:
        model = CM.NPC_SHOPS.model
        fields = '__all__'


class SkillsForm(ObjectsForm):
    def __init__(self, *args, **kwargs):
        super(SkillsForm, self).__init__(*args, **kwargs)
        
        self.fields['icon'] = ImageField(image_type="icon", required=False)
        
        choices = [("", "---------")]
        objects = CM.SKILL_TYPES.objects.all()
        choices.extend([(obj.key, obj.name + " (" + obj.key + ")") for obj in objects])
        self.fields['main_type'] = forms.ChoiceField(choices=choices, required=False)
        self.fields['sub_type'] = forms.ChoiceField(choices=choices, required=False)

        localize_form_fields(self)

    class Meta:
        model = CM.SKILLS.model
        fields = '__all__'
        

class SkillTypesForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(SkillTypesForm, self).__init__(*args, **kwargs)
        localize_form_fields(self)

    class Meta:
        model = CM.SKILL_TYPES.model
        fields = '__all__'


class DefaultSkillsForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(DefaultSkillsForm, self).__init__(*args, **kwargs)

        # all character's models
        objects = CM.CHARACTERS.all_with_base()
        choices = [(obj["key"], obj["name"] + " (" + obj["key"] + ")") for obj in objects]
        self.fields['character'] = forms.ChoiceField(choices=choices)

        objects = CM.SKILLS.all_with_base()
        choices = [(obj["key"], obj["name"] + " (" + obj["key"] + ")") for obj in objects]
        self.fields['skill'] = forms.ChoiceField(choices=choices)

        localize_form_fields(self)
        
    class Meta:
        model = CM.DEFAULT_SKILLS.model
        fields = '__all__'


class NPCDialoguesForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(NPCDialoguesForm, self).__init__(*args, **kwargs)

        # All NPCs.
        objects = CM.WORLD_NPCS.all_with_base()
        choices = [(obj["key"], obj["name"] + " (" + obj["key"] + ")") for obj in objects]
        self.fields['npc'] = forms.ChoiceField(choices=choices)
        
        objects = CM.DIALOGUES.objects.all()
        choices = [(obj.key, obj.name + " (" + obj.key + ")") for obj in objects]
        self.fields['dialogue'] = forms.ChoiceField(choices=choices)

        localize_form_fields(self)

    class Meta:
        model = CM.NPC_DIALOGUES.model
        fields = '__all__'


class QuestsForm(ObjectsForm):
    def __init__(self, *args, **kwargs):
        super(QuestsForm, self).__init__(*args, **kwargs)

        localize_form_fields(self)

    class Meta:
        model = CM.QUESTS.model
        fields = '__all__'


class QuestObjectivesForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(QuestObjectivesForm, self).__init__(*args, **kwargs)

        objects = CM.QUESTS.all_with_base()
        choices = [(obj["key"], obj["name"] + " (" + obj["key"] + ")") for obj in objects]
        self.fields['quest'] = forms.ChoiceField(choices=choices)

        objects = QUEST_OBJECTIVE_SET.all()
        choices = [(obj, obj) for obj in objects]
        self.fields['type'] = forms.ChoiceField(choices=choices)

        localize_form_fields(self)

    class Meta:
        model = CM.QUEST_OBJECTIVES.model
        fields = '__all__'


class QuestDependenciesForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(QuestDependenciesForm, self).__init__(*args, **kwargs)

        objects = CM.QUESTS.all_with_base()
        choices = [(obj["key"], obj["name"] + " (" + obj["key"] + ")") for obj in objects]
        self.fields['quest'] = forms.ChoiceField(choices=choices)
        self.fields['dependency'] = forms.ChoiceField(choices=choices)
        
        choices = QUEST_STATUS_SET.choice_all()
        self.fields['type'] = forms.ChoiceField(choices=choices)

        localize_form_fields(self)

    class Meta:
        model = CM.QUEST_DEPENDENCIES.model
        fields = '__all__'


class DialogueQuestDependenciesForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(DialogueQuestDependenciesForm, self).__init__(*args, **kwargs)

        objects = CM.DIALOGUES.objects.all()
        choices = [(obj.key, obj.name + " (" + obj.key + ")") for obj in objects]
        self.fields['dialogue'] = forms.ChoiceField(choices=choices)
        
        objects = CM.QUESTS.all_with_base()
        choices = [(obj["key"], obj["name"] + " (" + obj["key"] + ")") for obj in objects]
        self.fields['dependency'] = forms.ChoiceField(choices=choices)
        
        choices = QUEST_STATUS_SET.choice_all()
        self.fields['type'] = forms.ChoiceField(choices=choices)

        localize_form_fields(self)

    class Meta:
        model = CM.DIALOGUE_QUEST_DEPENDENCIES.model
        fields = '__all__'


class EquipmentsForm(ObjectsForm):
    def __init__(self, *args, **kwargs):
        super(EquipmentsForm, self).__init__(*args, **kwargs)

        objects = CM.EQUIPMENT_POSITIONS.objects.all()
        choices = [(obj.key, obj.name + " (" + obj.key + ")") for obj in objects]
        self.fields['position'] = forms.ChoiceField(choices=choices)
        
        objects = CM.EQUIPMENT_TYPES.objects.all()
        choices = [(obj.key, obj.name + " (" + obj.key + ")") for obj in objects]
        self.fields['type'] = forms.ChoiceField(choices=choices)
        
        localize_form_fields(self)

    class Meta:
        model = CM.EQUIPMENTS.model
        fields = '__all__'


class EventDataForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(EventDataForm, self).__init__(*args, **kwargs)

        choices = EVENT_ACTION_SET.choice_all()
        self.fields['action'] = forms.ChoiceField(choices=choices)

        choices = EVENT_TRIGGER_SET.choice_all()
        self.fields['trigger_type'] = forms.ChoiceField(choices=choices)

        localize_form_fields(self)

    def clean(self):
        cleaned_data = super(EventDataForm, self).clean()

        # check object's key
        key = cleaned_data["key"]
        if not key:
            cleaned_data["key"] = generate_key(self)
        
    class Meta:
        model = CM.EVENT_DATA.model
        fields = '__all__'


class ActionAttackForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(ActionAttackForm, self).__init__(*args, **kwargs)

        objects = CM.EVENT_DATA.objects.filter(action="ACTION_ATTACK")
        choices = [(obj.key, obj.key + " (" + obj.key + ")") for obj in objects]
        self.fields['event_key'] = forms.ChoiceField(choices=choices)
        
        objects = CM.CHARACTERS.all_with_base()
        choices = [(obj["key"], obj["name"] + " (" + obj["key"] + ")") for obj in objects]
        self.fields['mob'] = forms.ChoiceField(choices=choices)

        localize_form_fields(self)

    class Meta:
        model = CM.ACTION_ATTACK.model
        fields = '__all__'


class ActionDialogueForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(ActionDialogueForm, self).__init__(*args, **kwargs)

        objects = CM.EVENT_DATA.objects.filter(action="ACTION_DIALOGUE")
        choices = [(obj.key, obj.key + " (" + obj.key + ")") for obj in objects]
        self.fields['event_key'] = forms.ChoiceField(choices=choices)

        objects = CM.DIALOGUES.objects.all()
        choices = [(obj.key, obj.name + " (" + obj.key + ")") for obj in objects]
        self.fields['dialogue'] = forms.ChoiceField(choices=choices)

        # NPCs
        choices = [("", "---------")]
        objects = CM.WORLD_NPCS.all_with_base()
        choices.extend([(obj["key"], obj["name"] + " (" + obj["key"] + ")") for obj in objects])
        self.fields['npc'] = forms.ChoiceField(choices=choices, required=False)

        localize_form_fields(self)

    class Meta:
        model = CM.ACTION_DIALOGUE.model
        fields = '__all__'


class ActionLearnSkillForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(ActionLearnSkillForm, self).__init__(*args, **kwargs)

        objects = CM.EVENT_DATA.objects.filter(action="ACTION_LEARN_SKILL")
        choices = [(obj.key, obj.key + " (" + obj.key + ")") for obj in objects]
        self.fields['event_key'] = forms.ChoiceField(choices=choices)

        objects = CM.SKILLS.all_with_base()
        choices = [(obj["key"], obj["name"] + " (" + obj["key"] + ")") for obj in objects]
        self.fields['skill'] = forms.ChoiceField(choices=choices)

        localize_form_fields(self)

    class Meta:
        model = CM.ACTION_LEARN_SKILL.model
        fields = '__all__'


class ActionAcceptQuestForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(ActionAcceptQuestForm, self).__init__(*args, **kwargs)

        objects = CM.EVENT_DATA.objects.filter(action="ACTION_ACCEPT_QUEST")
        choices = [(obj.key, obj.key + " (" + obj.key + ")") for obj in objects]
        self.fields['event_key'] = forms.ChoiceField(choices=choices)

        objects = CM.QUESTS.all_with_base()
        choices = [(obj["key"], obj["name"] + " (" + obj["key"] + ")") for obj in objects]
        self.fields['quest'] = forms.ChoiceField(choices=choices)

        localize_form_fields(self)

    class Meta:
        model = CM.ACTION_ACCEPT_QUEST.model
        fields = '__all__'
        
        
class ActionTurnInQuestForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(ActionTurnInQuestForm, self).__init__(*args, **kwargs)

        objects = CM.EVENT_DATA.objects.filter(action="ACTION_TURN_IN_QUEST")
        choices = [(obj.key, obj.key + " (" + obj.key + ")") for obj in objects]
        self.fields['event_key'] = forms.ChoiceField(choices=choices)

        objects = CM.QUESTS.all_with_base()
        choices = [(obj["key"], obj["name"] + " (" + obj["key"] + ")") for obj in objects]
        self.fields['quest'] = forms.ChoiceField(choices=choices)

        localize_form_fields(self)

    class Meta:
        model = CM.ACTION_TURN_IN_QUEST.model
        fields = '__all__'
        
        
class ActionCloseEventForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(ActionCloseEventForm, self).__init__(*args, **kwargs)

        objects = CM.EVENT_DATA.objects.filter(action="ACTION_CLOSE_EVENT")
        choices = [(obj.key, obj.key + " (" + obj.key + ")") for obj in objects]
        self.fields['event_key'] = forms.ChoiceField(choices=choices)

        objects = CM.EVENT_DATA.objects.all()
        choices = [(obj.key, obj.key) for obj in objects]
        self.fields['event'] = forms.ChoiceField(choices=choices)

        localize_form_fields(self)

    class Meta:
        model = CM.ACTION_CLOSE_EVENT.model
        fields = '__all__'
        

class ActionMessageForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(ActionMessageForm, self).__init__(*args, **kwargs)
        localize_form_fields(self)

    class Meta:
        model = EVENT_ACTION_SET.get("ACTION_MESSAGE").model()
        fields = '__all__'


class ActionRoomIntervalForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(ActionRoomIntervalForm, self).__init__(*args, **kwargs)

        choices = EVENT_ACTION_SET.choice_repeatedly()
        self.fields['action'] = forms.ChoiceField(choices=choices)

        localize_form_fields(self)

    class Meta:
        model = EVENT_ACTION_SET.get("ACTION_ROOM_INTERVAL").model()
        fields = '__all__'


class ActionGetObjectsForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(ActionGetObjectsForm, self).__init__(*args, **kwargs)

        # available objects
        choices = get_all_pocketable_objects()
        self.fields['object'] = forms.ChoiceField(choices=choices)

        localize_form_fields(self)

    class Meta:
        model = EVENT_ACTION_SET.get("ACTION_GET_OBJECTS").model()
        fields = '__all__'


class DialoguesForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(DialoguesForm, self).__init__(*args, **kwargs)
        localize_form_fields(self)

    def clean(self):
        cleaned_data = super(DialoguesForm, self).clean()

        # check object's key
        key = cleaned_data["key"]
        if not key:
            cleaned_data["key"] = generate_key(self)

    class Meta:
        model = CM.DIALOGUES.model
        fields = '__all__'


class DialogueRelationsForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(DialogueRelationsForm, self).__init__(*args, **kwargs)

        objects = CM.DIALOGUES.objects.all()
        choices = [(obj.key, obj.name + " (" + obj.key + ")") for obj in objects]
        self.fields['dialogue'] = forms.ChoiceField(choices=choices)
        self.fields['next_dlg'] = forms.ChoiceField(choices=choices)

        localize_form_fields(self)

    class Meta:
        model = CM.DIALOGUE_RELATIONS.model
        fields = '__all__'


class DialogueSentencesForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(DialogueSentencesForm, self).__init__(*args, **kwargs)

        objects = CM.DIALOGUES.objects.all()
        choices = [(obj.key, obj.name + " (" + obj.key + ")") for obj in objects]
        self.fields['dialogue'] = forms.ChoiceField(choices=choices)

        # dialogue's icon
        self.fields['icon'] = ImageField(image_type="icon", required=False)

        localize_form_fields(self)

    def clean(self):
        cleaned_data = super(DialogueSentencesForm, self).clean()

        # check object's key
        key = cleaned_data["key"]
        if not key:
            cleaned_data["key"] = generate_key(self)

    class Meta:
        model = CM.DIALOGUE_SENTENCES.model
        fields = '__all__'


class ConditionDescForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(ConditionDescForm, self).__init__(*args, **kwargs)

        choices = get_all_objects()
        self.fields['key'] = forms.ChoiceField(choices=choices)

        localize_form_fields(self)

    class Meta:
        model = CM.CONDITION_DESC.model
        fields = '__all__'
        

class LocalizedStringsForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(LocalizedStringsForm, self).__init__(*args, **kwargs)
        localize_form_fields(self)

    class Meta:
        model = CM.LOCALIZED_STRINGS.model
        fields = '__all__'


class ImageResourcesForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(ImageResourcesForm, self).__init__(*args, **kwargs)

        choices = [("background", "background"),
                   ("icon", "icon")]
        self.fields['type'] = forms.ChoiceField(choices=choices, required=False)

        localize_form_fields(self)

    class Meta:
        model = CM.IMAGE_RESOURCES.model
        fields = '__all__'
