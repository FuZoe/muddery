"""
Player Characters

Player Characters are (by default) Objects setup to be puppeted by Players.
They are what you "see" in game. The Character class in this module
is setup to be the "default" character type created by the default
creation commands.

"""

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from evennia.utils.utils import lazy_property
from evennia.utils import logger, search
from evennia.comms.models import ChannelDB
from muddery.server.utils import utils
from muddery.server.utils.builder import build_object
from muddery.server.utils.quest_handler import QuestHandler
from muddery.server.utils.statement_attribute_handler import StatementAttributeHandler
from muddery.server.utils.exception import MudderyError
from muddery.server.utils.localized_strings_handler import _
from muddery.server.utils.game_settings import GAME_SETTINGS
from muddery.server.utils.dialogue_handler import DIALOGUE_HANDLER
from muddery.server.utils.defines import ConversationType
from muddery.server.utils.defines import CombatType
from muddery.server.database.worlddata.worlddata import WorldData
from muddery.server.database.worlddata.honour_settings import HonourSettings
from muddery.server.database.worlddata.default_objects import DefaultObjects
from muddery.server.mappings.element_set import ELEMENT
from muddery.server.utils import defines
from muddery.server.database.gamedata.honours_mapper import HONOURS_MAPPER
from muddery.server.database.gamedata.player_character import PLAYER_CHARACTER_DATA
from muddery.server.database.worlddata.equipment_positions import EquipmentPositions
from muddery.server.combat.match_pvp_handler import MATCH_COMBAT_HANDLER


class MudderyPlayerCharacter(ELEMENT("CHARACTER")):
    """
    The Character defaults to implementing some of its hook methods with the
    following standard functionality:

    at_basetype_setup - always assigns the DefaultCmdSet to this object type
                    (important!)sets locks so character cannot be picked up
                    and its commands only be called by itself, not anyone else.
                    (to change things, use at_object_creation() instead)
    at_after_move - launches the "look" command
    at_post_puppet(player) -  when Player disconnects from the Character, we
                    store the current location, so the "unconnected" character
                    object does not need to stay on grid but can be given a
                    None-location while offline.
    at_pre_puppet - just before Player re-connects, retrieves the character's
                    old location and puts it back on the grid with a "charname
                    has connected" message echoed to the room

    """
    element_type = "PLAYER_CHARACTER"
    element_name = _("Player Character", "elements")
    model_name = "player_characters"

    # initialize all handlers in a lazy fashion
    @lazy_property
    def quest_handler(self):
        return QuestHandler(self)

    # attributes used in statements
    @lazy_property
    def statement_attr(self):
        return StatementAttributeHandler(self)

    def at_object_creation(self):
        """
        Called once, when this object is first created. This is the
        normal hook to overload for most object types.
            
        """
        super(MudderyPlayerCharacter, self).at_object_creation()

        PLAYER_CHARACTER_DATA.add(self.id)

    def at_object_delete(self):
        """
        Called just before the database object is permanently
        delete()d from the database. If this method returns False,
        deletion is aborted.

        All skills, contents will be removed too.
        """
        result = super(MudderyPlayerCharacter, self).at_object_delete()
        if not result:
            return result

        # remove the character's honour
        HONOURS_MAPPER.remove_honour(self.id)

        # remove the character's data
        PLAYER_CHARACTER_DATA.remove(self.id)

        # remove quests
        self.quest_handler.remove_all()

        return True

    def after_data_loaded(self):
        """
        """
        super(MudderyPlayerCharacter, self).after_data_loaded()

        self.solo_mode = GAME_SETTINGS.get("solo_mode")
        self.available_channels = {}

        # refresh data
        self.refresh_properties(True)

        # if it is dead, reborn at init.
        if not self.is_alive():
            if not self.is_temp and self.reborn_time > 0:
                self.reborn()

    def move_to(self, destination, quiet=False,
                emit_to_obj=None, use_destination=True, to_none=False, move_hooks=True, **kwargs):
        """
        Moves this object to a new location.
        """
        if not quiet and self.solo_mode:
            # If in solo mode, move quietly.
            quiet = True

        return super(MudderyPlayerCharacter, self).move_to(destination,
                                                           quiet,
                                                           emit_to_obj,
                                                           use_destination,
                                                           to_none,
                                                           move_hooks)

    def at_before_move(self, destination, **kwargs):
        """
        Called just before starting to move this object to
        destination.
        """
        # trigger event
        if self.has_account:
            self.location.event.at_character_move_out(self)

        return True

    def at_after_move(self, source_location):
        """
        We make sure to look around after a move.

        """
        self.msg({"msg": _("Moved to %s ...") % self.location.name})
        self.show_location()

        # trigger event
        if self.has_account:
            self.location.event.at_character_move_in(self)

    def at_post_puppet(self):
        """
        Called just after puppeting has been completed and all
        Player<->Object links have been established.

        """
        self.available_channels = self.get_available_channels()

        allow_commands = False
        if self.account:
            if self.is_superuser:
                allow_commands = True
            else:
                for perm in self.account.permissions.all():
                    if perm in settings.PERMISSION_COMMANDS:
                        allow_commands = True
                        break

        # Django's superuser even it is quelled.
        if not allow_commands:
            allow_commands = self.db_account and self.db_account.is_superuser

        # Send puppet info to the client first.
        output = {
            "dbref": self.dbref,
            "name": self.get_name(),
            "icon": getattr(self, "icon", None),
        }

        if allow_commands:
            output["allow_commands"] = True

        self.msg({"puppet": output})

        # send character's data to player
        message = {
            "status": self.return_status(),
            "equipments": self.return_equipments(),
            "inventory": self.return_inventory(),
            "skills": self.return_skills(),
            "quests": self.quest_handler.return_quests(),
            "revealed_map": self.get_revealed_map(),
            "channels": self.available_channels
        }
        self.msg(message)

        self.show_location()

        # notify its location
        if not self.solo_mode:
            if self.location:
                change = {"dbref": self.dbref,
                          "name": self.get_name()}
                self.location.msg_contents({"player_online": change}, exclude=[self])

        self.resume_last_dialogue()

        self.resume_combat()

        # Resume all scripts.
        scripts = self.scripts.all()
        for script in scripts:
            script.unpause()

    def at_pre_unpuppet(self):
        """
        Called just before beginning to un-connect a puppeting from
        this Player.
        """
        # Pause all scripts.
        scripts = self.scripts.all()
        for script in scripts:
            script.pause()

        if not self.solo_mode:
            # notify its location
            if self.location:
                change = {"dbref": self.dbref,
                          "name": self.get_name()}
                self.location.msg_contents({"player_offline":change}, exclude=self)

        MATCH_COMBAT_HANDLER.remove(self)

    def get_object_key(self):
        """
        Get the object's key.
        """
        if not hasattr(self, "object_key"):
            self.object_key = GAME_SETTINGS.get("default_player_character_key")

        return self.object_key

    def set_nickname(self, nickname):
        """
        Set player character's nickname.
        """
        PLAYER_CHARACTER_DATA.update_nickname(self.id, nickname)

    def get_name(self):
        """
        Get player character's name.
        """
        # Use nick name instead of normal name.
        return PLAYER_CHARACTER_DATA.get_nickname(self.id)

    def get_available_commands(self, caller):
        """
        This returns a list of available commands.
        """
        commands = []
        if self.is_alive():
            commands.append({"name": _("Attack"), "cmd": "attack", "args": self.dbref})
        return commands

    def get_available_channels(self):
        """
        Get available channel's info.

        Returns:
            (dict) channels
        """
        channels = {}
        channel = ChannelDB.objects.get_channel(settings.DEFAULT_CHANNELS[0]["key"])
        if channel.has_connection(self):
            channels[channel.key] = {
                "type": "CHANNEL",
                "name": _("Public", category="channels"),
            }

        """
        commands = False
        if self.account:
            if self.is_superuser:
                commands = True
            else:
                for perm in self.account.permissions.all():
                    if perm in settings.PERMISSION_COMMANDS:
                        commands = True
                        break

        # Django's superuser even it is quelled.
        if not commands:
            commands = self.db_account and self.db_account.is_superuser

        if commands:
            channels["CMD"] = {
                "type": "CMD",
                "name": _("Cmd"),
            }
        """
        return channels

    def get_revealed_map(self):
        """
        Get the map that the character has revealed.
        Return value:
            {
                "rooms": {room1's key: {"name": name,
                                        "icon": icon,
                                        "area": area,
                                        "pos": position},
                          room2's key: {"name": name,
                                        "icon": icon,
                                        "area": area,
                                        "pos": position},
                          ...},
                "exits": {exit1's key: {"from": room1's key,
                                        "to": room2's key},
                          exit2's key: {"from": room3's key,
                                        "to": room4's key},
                          ...}
            }
        """
        rooms = {}
        exits = {}

        revealed_map = self.states.load("revealed_map", set())
        for room_key in revealed_map:
            # get room's information
            try:
                room = utils.get_object_by_key(room_key)
                rooms[room_key] = {"name": room.get_name(),
                                   "icon": room.icon,
                                   "area": room.location and room.location.get_object_key(),
                                   "pos": room.position}
                new_exits = room.get_exits()
                if new_exits:
                    exits.update(new_exits)
            except ObjectDoesNotExist:
                pass

        for path in exits.values():
            # add room's neighbours
            if not path["to"] in rooms:
                try:
                    neighbour = utils.get_object_by_key(path["to"])
                    rooms[neighbour.get_object_key()] = {
                        "name": neighbour.get_name(),
                        "icon": neighbour.icon,
                        "area": neighbour.location and neighbour.location.get_object_key(),
                        "pos": neighbour.position
                    }
                except ObjectDoesNotExist:
                    pass

        return {"rooms": rooms, "exits": exits}

    def show_location(self):
        """
        show character's location
        """
        if self.location:
            location_key = self.location.get_object_key()
            area = self.location.location and self.location.location.get_appearance(self)

            msg = {"current_location": {"key": location_key,
                                        "area": area}}

            """
            reveal_map:
            {
                "rooms": {room1's key: {"name": name,
                                        "icon": icon,
                                        "area": area,
                                        "pos": position},
                          room2's key: {"name": name,
                                        "icon": icon,
                                        "area": area,
                                        "pos": position},
                          ...},
                "exits": {exit1's key: {"from": room1's key,
                                        "to": room2's key},
                          exit2's key: {"from": room3's key,
                                        "to": room4's key},
                          ...}
            }
            """
            revealed_map = self.states.load("revealed_map", set())
            if not location_key in revealed_map:
                # reveal map
                revealed_map.add(self.location.get_object_key())
                self.states.save("revealed_map", revealed_map)

                rooms = {
                    location_key: {
                        "name": self.location.get_name(),
                        "icon": self.location.icon,
                        "area": self.location.location and self.location.location.get_object_key(),
                        "pos": self.location.position
                    }
                }

                exits = self.location.get_exits()

                for path in exits.values():
                    # add room's neighbours
                    if not path["to"] in rooms:
                        try:
                            neighbour = utils.get_object_by_key(path["to"])
                            rooms[neighbour.get_object_key()] = {
                                "name": neighbour.get_name(),
                                "icon": neighbour.icon,
                                "area": neighbour.location and neighbour.location.get_object_key(),
                                "pos": neighbour.position
                            }
                        except ObjectDoesNotExist:
                            pass
                    
                msg["reveal_map"] = {"rooms": rooms, "exits": exits}

            # get appearance
            appearance = self.location.get_appearance(self)
            appearance.update(self.location.get_surroundings(self))
            msg["look_around"] = appearance

            self.msg(msg)

    def load_default_objects(self):
        """
        Load character's default objects.
        """
        # default objects
        object_records = DefaultObjects.get(self.get_object_key())

        # add new default objects
        obj_list = []
        inventory = self.states.load("inventory", [])
        for object_record in object_records:
            found = False
            for item in inventory:
                if object_record.object == item["key"]:
                    found = True
                    break
            if not found:
                obj_list.append({
                    "object": object_record.object,
                    "level": object_record.level,
                    "number": object_record.number,
                })

        if obj_list:
            self.receive_objects(obj_list, mute=True)

    def receive_objects(self, obj_list, mute=False):
        """
        Add objects to the inventory.

        Args:
            obj_list: (list) a list of object keys and there numbers.
                             list item: {"object": object's key
                                         "number": object's number}
            mute: (boolean) do not send messages to the owner

        Returns:
            (list) a list of objects that not have been received and their reasons.
            [{
                "key": key,
                "name": name,
                "level": level,
                "number": number,
                "icon": icon,
                "reject": reason,
            }]
        """
        objects = []           # objects that have been accepted

        # check what the character has now
        changed = False
        inventory = self.states.load("inventory", [])

        for obj in obj_list:
            key = obj["object"]
            level = obj.get("level")
            available = obj["number"]
            number = available
            accepted = 0
            reject = False

            try:
                common_models = ELEMENT("COMMON_OBJECT").get_models()
                object_record = WorldData.get_tables_data(common_models, key=key)
                object_record = object_record[0]
            except Exception as e:
                logger.log_err("Can not find object %s: %s" % (key, e))
                continue

            inventory_obj_list = [index for index, item in enumerate(inventory) if item["key"] == key]

            if number == 0:
                # it is an empty object
                if len(inventory_obj_list) > 0:
                    # already has this object
                    continue

                if object_record.can_remove:
                    # remove this empty object
                    continue

                # create a new content
                new_obj = build_object(key, level=level)
                if new_obj:
                    # move the new object to the inventory
                    inventory.append({
                        "key": key,
                        "dbref": new_obj.dbref,
                        "obj": new_obj,
                        "number": number,
                    })
                    changed = True
                else:
                    reject = _("Can not get %s.") % key

            else:
                # common number
                if object_record.unique:
                    # unique object
                    if len(inventory_obj_list) > 0:
                        # add object number
                        current_number = inventory[inventory_obj_list[0]]["number"]
                        add = number
                        if add > object_record.max_stack - current_number:
                            add = object_record.max_stack - current_number

                        if add > 0:
                            # increase stack number
                            inventory[inventory_obj_list[0]]["number"] += add
                            changed = True
                            number -= add
                            accepted += add
                        else:
                            reject = _("Can not get more %s.") % object_record.name
                    else:
                        # create a new content
                        new_obj = build_object(key, level=level)
                        if not new_obj:
                            reject = _("Can not get %s.") % object_record.name
                            break

                        # Get the number that actually added.
                        add = number
                        if add > object_record.max_stack:
                            add = object_record.max_stack

                        # move the new object to the inventory
                        inventory.append({
                            "key": key,
                            "dbref": new_obj.dbref,
                            "obj": new_obj,
                            "number": add,
                        })
                        changed = True

                        number -= add
                        accepted += add
                else:
                    # not unique object
                    # if already has this kind of object
                    for index in inventory_obj_list:
                        add = number
                        if add > object_record.max_stack - inventory[index]["number"]:
                            add = object_record.max_stack - inventory[index]["number"]

                        if add > 0:
                            # increase stack number
                            inventory[inventory_obj_list[0]]["number"] += add
                            changed = True
                            number -= add
                            accepted += add

                        if number == 0:
                            break

                    # if does not have this kind of object, or stack is full
                    while number > 0:
                        if object_record.unique:
                            # can not have more than one unique objects
                            reject = _("Can not get more %s.") % object_record.name
                            break

                        # create a new content
                        new_obj = build_object(key, level=level)
                        if not new_obj:
                            reject = _("Can not get %s.") % object_record.name
                            break

                        # Get the number that actually added.
                        add = number
                        if add > object_record.max_stack:
                            add = object_record.max_stack

                        # move the new object to the inventory
                        inventory.append({
                            "key": key,
                            "dbref": new_obj.dbref,
                            "obj": new_obj,
                            "number": add,
                        })
                        changed = True

                        number -= add
                        accepted += add

            objects.append({
                "key": object_record.key,
                "name": object_record.name,
                "icon": object_record.icon,
                "number": accepted,
                "reject": reject,
            })

        if changed:
            self.states.save("inventory", inventory)

        if not mute:
            # Send results to the player.
            message = {"get_objects": objects}
            self.msg(message)

        self.show_inventory()

        # call quest handler
        for item in objects:
            if not item["reject"]:
                self.quest_handler.at_objective(defines.OBJECTIVE_OBJECT, item["key"], item["number"])

        return objects

    def get_object_number(self, obj_key):
        """
        Get the number of this object.
        Args:
            obj_key: (String) object's key

        Returns:
            int: object number
        """
        inventory = self.states.load("inventory", [])

        # get total number
        total = sum([item["number"] for item in inventory if obj_key == item["key"]])

        return total

    def can_get_object(self, obj_key, number):
        """
        Check if the character can get these objects.

        Args:
            obj_key: (String) object's key
            number: (int) object's number

        Returns:
            boolean: can get

        Notice:
            If the character does not have this object, the return will be always true,
            despite of the number!
        """
        try:
            common_models = ELEMENT("COMMON_OBJECT").get_models()
            object_record = WorldData.get_tables_data(common_models, key=obj_key)
            object_record = object_record[0]
        except Exception as e:
            return False

        total = self.get_object_number(obj_key)
        if not total:
            return True

        if not object_record.unique:
            return True

        if total + number <= object_record.max_stack:
            return True

        return False

    def use_object(self, obj_dbref, number=1):
        """
        Use an object.

        Args:
            obj_dbref: (string) object' dbref
            number: (int) number to use

        Returns:
            result: (string) the description of the result
        """
        item = None
        inventory = self.states.load("inventory", [])
        for value in inventory:
            if value["dbref"] == obj_dbref:
                item = value
                break
        if not item:
            raise MudderyError(_("Can not find this object."))

        if item["number"] < number:
            return _("Not enough number.")

        # take effect
        try:
            result, used = item["obj"].take_effect(self, number)
            if used > 0:
                # remove used object
                self.remove_object_by_dbref(obj_dbref, used, True)

            self.show_inventory()
            return result
        except Exception as e:
            ostring = "Can not use %s: %s" % (item["key"], e)
            logger.log_tracemsg(ostring)

        return _("No effect.")

    def remove_object_dbref_all(self, dbref, mute=False):
        """
        Remove an object by its dbref.

        :param dbref:
        :param mute:
        :return:
        """
        inventory = self.states.load("inventory", [])
        for item in inventory:
            if item["dbref"] == dbref:
                item["number"] = 0
                if item["obj"].can_remove:
                    item["obj"].delete()
                    inventory.remove(item)

                self.states.save("inventory", inventory)
                if not mute:
                    self.show_inventory()

                return

        raise(MudderyError(_("Can not remove this object.")))

    def remove_object_by_dbref(self, dbref, number, mute=False):
        """
        Remove an object by its dbref.

        :param dbref:
        :param mute:
        :return:
        """
        inventory = self.states.load("inventory", [])
        for item in inventory:
            if item["dbref"] == dbref:
                obj_num = item["number"]
                if obj_num > 0:
                    if obj_num > number:
                        item["number"] -= number
                    else:
                        item["number"] = 0
                        if item["obj"].can_remove:
                            item["obj"].delete()
                            inventory.remove(item)

                    self.states.save("inventory", inventory)
                    if not mute:
                        self.show_inventory()

                return

        raise(MudderyError(_("Can not remove this object.")))

    def remove_objects(self, obj_list, mute=False):
        """
        Remove objects from the inventory.

        Args:
            obj_list: (list) a list of object keys and there numbers.
                             list item: {"object": object's key
                                         "number": object's number}

        Returns:
            boolean: success
        """
        for item in obj_list:
            self.remove_object(item["object"], item["number"], True)

        if not mute:
            self.show_inventory()

    def remove_object(self, obj_key, number, mute=False):
        """
        Remove objects from the inventory.

        Args:
            obj_key: object's key
            number: object's number
            mute: send inventory information

        Returns:
            boolean: success
        """
        # Count objects in the inventory.
        inventory = self.states.load("inventory", [])
        total = sum([item["number"] for item in inventory if obj_key == item["key"]])
        if total < number:
            raise (MudderyError(_("Can not remove this object.")))

        # remove objects
        to_remove = number
        try:
            i = 0
            while i < len(inventory):
                item = inventory[i]
                if item["key"] != obj_key:
                    i += 1
                    continue

                deleted = False
                obj_num = item["number"]
                if obj_num > 0:
                    if obj_num >= to_remove:
                        item["number"] -= to_remove
                        to_remove = 0
                    else:
                        item["number"] = 0
                        to_remove -= obj_num

                    if item["number"] == 0:
                        # If this object can be removed from the inventor.
                        obj = item["obj"]
                        if obj.can_remove:
                            obj.delete()
                            del inventory[i]
                            deleted = True

                if to_remove == 0:
                    break

                if not deleted:
                    i += 1

        except Exception as e:
            logger.log_tracemsg("Can not remove object %s: %s" % (obj_key, e))
            raise (MudderyError(_("Can not remove this object.")))

        if to_remove > 0:
            logger.log_err("Remove object error: %s" % obj_key)
            raise (MudderyError(_("Can not remove this object.")))

        # Save the inventory.
        self.states.save("inventory", inventory)

        if not mute:
            self.show_inventory()

    def exchange_objects(self, remove_list, receive_list, mute=False):
        """
        Exchange some objects to other objects.

        :param remove_list:
        :param receive_list:
        :param mute:
        :return:
        """
        with self.states.atomic():
            self.remove_objects(remove_list, True)
            self.receive_objects(receive_list, True)

        if not mute:
            self.show_inventory()

    def show_inventory(self):
        """
        Send inventory data to player.
        """
        self.msg({"inventory": self.return_inventory()})

    def return_inventory(self):
        """
        Get inventory's data.
        """
        inv = []
        inventory = self.states.load("inventory", [])

        for item in inventory:
            obj = item["obj"]
            info = {
                "dbref": item["dbref"],             # item's dbref
                "number": item["number"],           # item's number
                "name": obj.get_name(),             # item's name
                "desc": obj.get_desc(self),         # item's desc
                "can_remove": obj.can_remove,
                "icon": obj.get_icon(),             # item's icon
            }
            inv.append(info)

        # sort by created time
        # inv.sort(key=lambda x: x["dbref"])

        return inv

    def return_inventory_object(self, dbref):
        """
        Get inventory's data.
        """
        inventory = self.states.load("inventory", [])

        for item in inventory:
            if item["dbref"] == dbref:
                appearance = item["obj"].get_appearance(self)
                appearance["number"] = item["number"]
                return appearance

    def return_equipments_object(self, dbref):
        """
        Get equipments data.
        """
        equipments = self.states.load("equipments", [])

        for pos, item in equipments.items():
            if item["dbref"] == dbref:
                appearance = item["obj"].get_appearance(self)

                appearance["number"] = item["number"]

                commands = [c for c in appearance["cmds"] if c["cmd"] != "equip" and c["cmd"] != "discard"]
                commands.append({
                    "name": _("Take Off"),
                    "cmd": "takeoff",
                    "args": dbref,
                })
                appearance["cmds"] = commands

                return appearance

    def show_status(self):
        """
        Send status to player.
        """
        status = self.return_status()
        self.msg({"status": status})

    def return_status(self):
        """
        Get character's status.
        """
        status = {}
        status["level"] = {"name": _("LEVEL"),
                           "value": self.get_level()}

        for key, info in self.get_properties_info().items():
            if not info["mutable"]:
                status[key] = {"name": info["name"],
                               "value": self.const_data_handler.get(key)}
            else:
                status[key] = {"name": info["name"],
                               "value": self.states.load(key)}

        return status

    def show_equipments(self):
        """
        Send equipments to player.
        """
        self.msg({
            "equipments": self.return_equipments()
        })

    def return_equipments(self):
        """
        Get equipments' data.
        """
        info = {}
        equipments = self.states.load("equipments", {})

        for pos, item in equipments.items():
            # in order of positions
            if item:
                obj = item["obj"]
                info[pos] = {
                    "dbref": item["dbref"],
                    "name": obj.get_name(),
                    "desc": obj.get_desc(self),
                    "icon": obj.get_icon(),
                }

        return info

    def equip_object(self, obj_dbref):
        """
        Equip an object.
        args: obj_dbref(string): the equipment object's dbref.
        """
        inventory = self.states.load("inventory", [])
        equipments = self.states.load("equipments", {})

        index = None
        item = None
        for i, value in enumerate(inventory):
            if value["dbref"] == obj_dbref:
                index = i
                item = value
                break

        if index is None:
            raise MudderyError(_("Can not find this equipment."))

        pos = item["obj"].position
        available_positions = set([r.key for r in EquipmentPositions.all()])
        if pos not in available_positions:
            raise MudderyError(_("Can not equip it on this position."))

        # Take off old equipment
        if pos in equipments and equipments[pos]:
            inventory.append(equipments[pos])
            equipments[pos] = None

        # Put on new equipment.
        equipments[pos] = item
        del inventory[index]

        # Save changes.
        with self.states.atomic():
            self.states.save("equipments", equipments)
            self.states.save("inventory", inventory)

        # reset character's attributes
        self.refresh_properties(True)

        message = {
            "status": self.return_status(),
            "equipments": self.return_equipments(),
            "inventory": self.return_inventory()
        }
        self.msg(message)

        return

    def take_off_equipment(self, obj_dbref):
        """
        Take off an equipment.
        args: obj_dbref(string): the equipment object's dbref.
        """
        inventory = self.states.load("inventory", [])
        equipments = self.states.load("equipments", {})

        pos = None
        item = None
        for key, value in equipments.items():
            if value["dbref"] == obj_dbref:
                pos = key
                item = value
                break

        if pos is None:
            raise MudderyError(_("Can not find this equipment."))

        inventory.append(item)
        del equipments[pos]

        # Save changes.
        with self.states.atomic():
            self.states.save("equipments", equipments)
            self.states.save("inventory", inventory)

        # reset character's attributes
        self.refresh_properties(True)

        message = {
            "status": self.return_status(),
            "equipments": self.return_equipments(),
            "inventory": self.return_inventory()
        }
        self.msg(message)

    def lock_exit(self, exit):
        """
        Lock an exit. Remove the exit's key from the character's unlock list.
        """
        exit_key = exit.get_object_key()
        unlocked_exits = self.states.load("unlocked_exits", set())
        if exit_key not in unlocked_exits:
            return

        unlocked_exits.remove(exit_key)
        self.states.save("unlocked_exits", unlocked_exits)

    def unlock_exit(self, exit):
        """
        Unlock an exit. Add the exit's key to the character's unlock list.
        """
        exit_key = exit.get_object_key()
        unlocked_exits = self.states.load("unlocked_exits", set())
        if exit_key in unlocked_exits:
            return True

        if not exit.can_unlock(self):
            self.msg({"msg": _("Can not open this exit.")})
            return False

        unlocked_exits.add(exit_key)
        self.states.save("unlocked_exits", unlocked_exits)
        return True

    def is_exit_unlocked(self, exit_key):
        """
        Whether the exit is unlocked.
        """
        unlocked_exits = self.states.load("unlocked_exits", set())
        return exit_key in unlocked_exits

    def show_skills(self):
        """
        Send skills to player.
        """
        skills = self.return_skills()
        self.msg({"skills": skills})

    def return_skills(self):
        """
        Get skills' data.
        """
        skills_list = []

        skills = self.states.load("skills", {})
        for key, skill in skills.items():
            skills_list.append(skill.get_appearance(self))

        return skills_list

    def resume_combat(self):
        """
        Resume unfinished combat.

        Returns:
            None
        """
        combat_handler = getattr(self.ndb, "combat_handler", None)
        if combat_handler:
            if not combat_handler.is_finished():
                # show combat infomation
                combat_handler.show_combat(self)
            else:
                self.leave_combat()

    def combat_result(self, combat_type, result, opponents=None, rewards=None):
        """
        Set the combat result.

        :param combat_type: combat's type
        :param result: defines.COMBAT_WIN, defines.COMBAT_LOSE, or defines.COMBAT_DRAW
        :param opponents: combat opponents
        :param rewards: combat rewards
        """
        combat_result = {
            "type": combat_type.value,
            "result": result,
            "rewards": {},
        }

        # get rewards
        if rewards:
            if "exp" in rewards and rewards["exp"]:
                exp = rewards["exp"]
                self.add_exp(exp)
                combat_result["rewards"]["exp"] = exp

            # give objects to winner
            if "loots" in rewards and rewards["loots"]:
                get_objects = self.receive_objects(rewards["loots"], mute=True)
                combat_result["rewards"]["get_objects"] = get_objects

            # honours
            if "honour" in rewards and rewards["honour"]:
                combat_result["rewards"]["honour"] = rewards["honour"]

        self.msg({"combat_finish": combat_result})

    def leave_combat(self):
        """
        Leave the current combat.
        """
        status = None
        opponents = None
        rewards = None
        if self.ndb.combat_handler:
            result = self.ndb.combat_handler.get_combat_result(self.id)
            if result:
                status, opponents, rewards = result

        combat_type = self.ndb.combat_handler.get_combat_type()

        if combat_type == CombatType.NORMAL:
            # normal combat
            # trigger events
            if status == defines.COMBAT_WIN:
                for opponent in opponents:
                    opponent.event.at_character_kill(self)
                    opponent.event.at_character_die()

                # call quest handler
                for opponent in opponents:
                    self.quest_handler.at_objective(defines.OBJECTIVE_KILL, opponent.get_object_key())
            elif status == defines.COMBAT_LOSE:
                self.die(opponents)
        elif combat_type == CombatType.HONOUR:
            if status == defines.COMBAT_WIN:
                self.honour_win()
            elif status == defines.COMBAT_LOSE:
                self.honour_lose()

        super(MudderyPlayerCharacter, self).leave_combat()

        # show status
        self.show_status()

        self.show_location()

    def die(self, killers):
        """
        This character is killed. Move it to it's home.
        """

        # player's character can always reborn
        if self.reborn_time < 1:
            self.reborn_time = 1

        super(MudderyPlayerCharacter, self).die(killers)
        
        self.msg({"msg": _("You died.")})

        if self.reborn_time > 0:
            self.msg({"msg": _("You will be reborn in {C%(s)s{n seconds.") % {'s': self.reborn_time}})

    def honour_win(self):
        """
        The character win in an honour combat.
        """
        # Recover properties.
        self.recover()
        self.show_status()

    def honour_lose(self):
        """
        The character lost in an honour combat.
        """
        # Recover properties.
        self.recover()
        self.show_status()

    def reborn(self):
        """
        Reborn after being killed.
        """
        # Reborn at its home.
        home = None
        default_home_key = GAME_SETTINGS.get("default_player_home_key")
        if default_home_key:
            try:
                home = utils.get_object_by_key(default_home_key)
            except ObjectDoesNotExist:
                pass;

        if not home:
            rooms = search.search_object(settings.DEFAULT_HOME)
            if rooms:
                home = rooms[0]

        if home:
            self.move_to(home, quiet=True)

        # Recover properties.
        self.recover()
        self.show_status()

        if home:
            self.msg({"msg": _("You are reborn at {C%s{n.") % home.get_name()})
        else:
            self.msg({"msg": _("You are reborn.")})

    def save_current_dialogues(self, dialogues, npc):
        """
        Save player's current dialogues.

        Args:
            dialogues: the current dialogues
            npc: NPC whom the player is talking to.

        Returns:
            None
        """
        if not GAME_SETTINGS.get("auto_resume_dialogues"):
            # Can not auto resume dialogues.
            return

        if not dialogues:
            self.clear_current_dialogue()
            return

        # Save the dialogue's id.
        dialogues = [d["dialogue"] for d in dialogues]

        npc_key = None
        if npc:
            npc_key = npc.get_object_key()

        location_key = None
        if self.location:
            location_key = self.location.get_object_key()

        current_dialogue = {"dialogues": dialogues,
                            "npc": npc_key,
                            "location": location_key}
        self.states.save("current_dialogue", current_dialogue)
        return

    def clear_current_dialogue(self):
        """
        Clear player's current dialogues.

        Returns:
            None
        """
        self.states.save("current_dialogue", None)
        return

    def resume_last_dialogue(self):
        """
        Restore player's dialogues when he return to game.

        Returns:
            None
        """
        if not GAME_SETTINGS.get("auto_resume_dialogues"):
            # Can not auto resume dialogues.
            return

        current_dialogue = self.states.load("current_dialogue")
        if not current_dialogue:
            return

        if not current_dialogue["dialogues"]:
            return

        # Check dialogue's location
        if self.location.get_object_key() != current_dialogue["location"]:
            # If player's location has changed, return.
            return

        # Check npc.
        npc_talking = None
        if current_dialogue["npc"]:
            try:
                npc = utils.get_object_by_key(current_dialogue["npc"])
                if npc.location == self.location:
                    npc_talking = npc
                else:
                    return
            except ObjectDoesNotExist:
                return

        dialogues = [DIALOGUE_HANDLER.get_dialogue(d) for d in current_dialogue["dialogues"]]
        dialogues = DIALOGUE_HANDLER.create_output_sentences(dialogues, self, npc_talking)
        self.msg({"dialogue": dialogues})
        return

    def talk_to_npc(self, npc):
        """
        Talk to an NPC.

        Args:
            npc: NPC's object.

        Returns:
            None
        """
        # Set caller's target.
        self.set_target(npc)

        # Get NPC's dialogue list.
        dialogues = DIALOGUE_HANDLER.get_npc_dialogues(self, npc)
        
        self.save_current_dialogues(dialogues, npc)
        self.msg({"dialogue": dialogues})

    def show_dialogue(self, dlg_key, npc):
        """
        Show a dialogue.

        Args:
            dlg_key: dialogue's key.
            npc: (optional) NPC's object.

        Returns:
            None
        """
        # Get next sentences_list.
        dialogue = DIALOGUE_HANDLER.get_dialogues_by_key(dlg_key, npc)

        # Send the dialogue to the player.
        self.save_current_dialogues(dialogue, npc)
        self.msg({"dialogue": dialogue})

    def finish_dialogue(self, dlg_key, npc):
        """
        Continue current dialogue.

        Args:
            dlg_key: current dialogue's key.
            npc: (optional) NPC's object.

        Returns:
            None
        """
        if GAME_SETTINGS.get("auto_resume_dialogues"):
            # Check current dialogue.
            current_dialogue = self.states.load("current_dialogue", None)
            if not current_dialogue:
                return

            if dlg_key not in current_dialogue["dialogue"]:
                # Can not find specified dialogue in current dialogues.
                return

        try:
            # Finish current dialogue
            DIALOGUE_HANDLER.finish_dialogue(dlg_key, self, npc)
        except Exception as e:
            ostring = "Can not finish dialogue %s: %s" % (dlg_key, e)
            logger.log_tracemsg(ostring)

        # Get next dialogue.
        next_dialogues = DIALOGUE_HANDLER.get_next_dialogues(dlg_key, self, npc)

        # Send dialogues_list to the player.
        self.save_current_dialogues(next_dialogues, npc)
        self.msg({"dialogue": next_dialogues})
        if not next_dialogues:
            # dialogue finished, refresh surroundings
            self.show_location()            

    def add_exp(self, exp):
        """
        Add character's exp.
        Args:
            exp: (number) the exp value to add.
        Returns:
            None
        """
        super(MudderyPlayerCharacter, self).add_exp(exp)

        self.msg({"get_exp": {"exp": exp}})

    def level_up(self):
        """
        Upgrade level.

        Returns:
            None
        """
        super(MudderyPlayerCharacter, self).level_up()

        # notify the player
        self.msg({"msg": _("{C%s upgraded to level %s.{n") % (self.get_name(), self.get_level())})

    def get_message(self, caller, message):
        """
        Receive a message from a character.

        :param caller: talker.
        :param message: content.
        """
        output = {
            "type": ConversationType.PRIVATE.value,
            "channel": self.get_name(),
            "from_dbref": caller.dbref,
            "from_name": caller.get_name(),
            "msg": message
        }
        self.msg({"conversation": output})
        caller.msg({"conversation": output})

    def show_rankings(self):
        """
        Show character's rankings.
        """
        honour_settings = HonourSettings.get_first_data()
        top_rankings = HONOURS_MAPPER.get_top_rankings(honour_settings.top_rankings_number)
        nearest_rankings = HONOURS_MAPPER.get_nearest_rankings(self, honour_settings.nearest_rankings_number)

        rankings = top_rankings
        rankings.extend([char_id for char_id in nearest_rankings if char_id not in top_rankings])

        characters = [self.search_dbref("#%s" % char_id) for char_id in rankings]
        data = [{"name": char.get_name(),
                 "dbref": char.dbref,
                 "ranking": HONOURS_MAPPER.get_ranking(char),
                 "honour": HONOURS_MAPPER.get_honour(char)} for char in characters if char]
        self.msg({"rankings": data})
