"""
Battle commands. They only can be used when a character is in a combat.
"""

from django.db import transaction
from django.core.exceptions import ObjectDoesNotExist
from wtforms import fields as wtfields
from muddery.server.utils.exception import MudderyError, ERR
from muddery.worldeditor.dao import general_query_mapper
from muddery.worldeditor.dao.common_mappers import WORLD_AREAS, WORLD_ROOMS
from muddery.worldeditor.dao.system_data_mapper import SystemDataMapper
from muddery.worldeditor.dao.element_properties_mapper import ElementPropertiesMapper
from muddery.worldeditor.mappings.form_set import FORM_SET
from muddery.server.mappings.element_set import ELEMENT, ELEMENT_SET
from muddery.server.mappings.event_action_set import EVENT_ACTION_SET
from muddery.server.utils.localized_strings_handler import _
from muddery.worldeditor.forms.location_field import LocationField
from muddery.worldeditor.forms.image_field import ImageField
from muddery.worldeditor.dao.general_query_mapper import get_all_fields


def query_form(table_name, condition=None):
    """
    Query table's data.

    Args:
        table_name: (string) data table's name.
        condition: (dict) conditions.
    """
    form_class = FORM_SET.get(table_name)
    if not form_class:
        raise MudderyError(ERR.no_table, "Can not find table: %s" % table_name)

    form = None
    record = None
    if condition:
        try:
            # Query record's data.
            record = general_query_mapper.get_record(table_name, condition)
            form = form_class(instance=record)
        except Exception as e:
            form = None

    if not form:
        # Get empty data.
        form = form_class()

    fields = []
    model_fields = get_all_fields(table_name)

    label_category = "field_" + table_name
    help_category = "help_" + table_name
    for model_field in model_fields:
        form_field = getattr(form, model_field)
        info = {
            "name": model_field,
            "label": _(model_field, label_category),
            "disabled": (model_field == "id"),
            "help_text": _(model_field, help_category),
            "type": type(form_field.widget).__name__,
        }

        if record:
            info["value"] = getattr(record, model_field)

        if info["type"] == "Select":
            info["choices"] = form_field.choices
        elif info["type"] == "ImageInput":
            info["image_type"] = form_field.image_type()

        fields.append(info)

    return fields


def save_form(values, table_name, record_id=None):
    """
    Save data to a record.
    
    Args:
        values: (dict) values to save.
        table_name: (string) data table's name.
        record_id: (string, optional) record's id. If it is empty, add a new record.
    """
    form_class = FORM_SET.get(table_name)
    if not form_class:
        raise MudderyError(ERR.no_table, "Can not find table: %s" % table_name)

    form = None
    if record_id:
        try:
            # Query record's data.
            record = general_query_mapper.get_record_by_id(table_name, record_id)
            form = form_class(values, instance=record)
        except Exception as e:
            form = None

    if not form:
        # Get empty data.
        form = form_class(values)

    # Save data
    if form.is_valid():
        instance = form.save()
        return instance.pk
    else:
        raise MudderyError(ERR.invalid_form, "Invalid form.", data=form.errors)


def delete_record(table_name, record_id):
    """
    Delete a record of a table.
    """
    general_query_mapper.delete_record_by_id(table_name, record_id)


def delete_records(table_name, condition=None):
    """
    Delete records by conditions.
    """
    general_query_mapper.delete_records(table_name, condition)


def query_element_form(base_element_type, obj_element_type, element_key):
    """
    Query all data of an object.

    Args:
        base_element_type: (string) the base element of the object.
        obj_element_type: (string, optional) object's element type. If it is empty, use the element type of the object
                        or use the base element type.
        element_key: (string) the element's key. If it is empty, query an empty form.
    """
    candidate_element_types = ELEMENT_SET.get_group(base_element_type)
    if not candidate_element_types:
        raise MudderyError(ERR.no_table, "Can not find the element: %s" % base_element_type)

    element = ELEMENT_SET.get(obj_element_type)
    if not element:
        raise MudderyError(ERR.no_table, "Can not get the element: %s" % obj_element_type)
    table_names = element.get_models()

    forms = []
    for table_name in table_names:
        if element_key:
            object_form = query_form(table_name, {"key": element_key})
        else:
            object_form = query_form(table_name)

        forms.append({
            "table": table_name,
            "fields": object_form
        })

    # add elements
    if len(forms) > 0:
        for field in forms[0]["fields"]:
            if field["name"] == "element_type":
                # set the element type to the new value
                field["value"] = obj_element_type
                field["type"] = "Select"
                field["choices"] = [(key, _(element.element_name, "elements") + " (" + key + ")")
                                    for key, element in candidate_element_types.items()]
                break

    return forms


def save_element_level_properties(element_type, element_key, level, values):
    """
    Save properties of an element.

    Args:
        element_type: (string) the element's type.
        element_key: (string) the element's key.
        level: (number) object's level.
        values: (dict) values to save.
    """
    ElementPropertiesMapper.inst().add_properties(element_type, element_key, level, values)


def delete_element_level_properties(element_type, element_key, level):
    """
    Delete properties of a level of the element.

    Args:
        element_type: (string) the element's type.
        element_key: (string) the element's key.
        level: (number) object's level.
    """
    ElementPropertiesMapper.inst().delete_properties(element_type, element_key, level)


def save_element_form(tables, element_type, element_key):
    """
    Save all data of an object.

    Args:
        tables: (list) a list of table data.
               [{
                 "table": (string) table's name.
                 "record": (string, optional) record's id. If it is empty, add a new record.
                }]
        element_type: (string) element's type.
        element_key: (string) current element's key. If it is empty or changed, query an empty form.
    """
    if not tables:
        raise MudderyError(ERR.invalid_form, "Invalid form.", data="Empty form.")

    # Get object's new key from the first form.
    try:
        new_key = tables[0]["values"]["key"]
    except KeyError:
        new_key = element_key

    if not new_key:
        # Does not has a new key, generate a new key.
        index = SystemDataMapper.inst().get_object_index()
        new_key = "%s_auto_%s" % (element_type, index)
        for table in tables:
            table["values"]["key"] = new_key

    forms = []
    for table in tables:
        table_name = table["table"]
        form_values = table["values"]

        form_class = FORM_SET.get(table_name)
        form = None
        if element_key:
            try:
                # Query the current object's data.
                record = general_query_mapper.get_record_by_key(table_name, element_key)
                form = form_class(form_values, instance=record)
            except ObjectDoesNotExist:
                form = None

        if not form:
            # Get empty data.
            form = form_class(form_values)

        forms.append(form)

    # check data
    for form in forms:
        if not form.is_valid():
            raise MudderyError(ERR.invalid_form, "Invalid form.", data=form.errors)

    # Save data
    with transaction.atomic():
        for form in forms:
            form.save()

    return new_key


def save_map_positions(area, rooms):
    """
    Save all data of an object.

    Args:
        area: (dict) area's data.
        rooms: (dict) rooms' data.
    """
    with transaction.atomic():
        # area data
        record = WORLD_AREAS.get(key=area["key"])
        record.background = area["background"]
        record.width = area["width"]
        record.height = area["height"]

        record.full_clean()
        record.save()

        # rooms
        for room in rooms:
            position = ""
            if len(room["position"]) > 1:
                position = "(%s,%s)" % (room["position"][0], room["position"][1])
            record = WORLD_ROOMS.get(key=room["key"])
            record.position = position

            record.full_clean()
            record.save()


def delete_element(element_key, base_element_type=None):
    """
    Delete an element from all tables under the base element type.
    """
    elements = ELEMENT_SET.get_group(base_element_type)
    tables = set()
    for key, value in elements.items():
        tables.update(value.get_models())

    with transaction.atomic():
        for table in tables:
            try:
                general_query_mapper.delete_record_by_key(table, element_key)
            except ObjectDoesNotExist:
                pass


def query_event_action_forms(action_type, event_key):
    """
    Query forms of the event action.

    Args:
        action_type: (string) action's type
        event_key: (string) event's key
    """
    # Get action's data.
    action = EVENT_ACTION_SET.get(action_type)
    if not action:
        raise MudderyError(ERR.no_table, "Can not find action: %s" % action_type)

    # Get all forms.
    forms = []
    table_name = action.model_name
    records = general_query_mapper.filter_records(table_name, event_key=event_key)
    if records:
        for record in records:
            forms.append(query_form(table_name, {"id": record.id}))
    else:
        forms.append(query_form(table_name))

    return {
        "forms": forms,
        "repeatedly": action.repeatedly
    }


def update_element_key(element_type, old_key, new_key):
    """
    Update an element's key in relative tables.

    Args:
        element_type: (string) object's element type.
        old_key: (string) object's old key.
        new_key: (string) object's new key
    """
    # The object's key has changed.
    element = ELEMENT(element_type)
    if issubclass(element, ELEMENT("AREA")):
        # Update relative room's location.
        model_name = ELEMENT("ROOM").model_name
        if model_name:
            general_query_mapper.filter_records(model_name, area=old_key).update(area=new_key)
    elif issubclass(element, ELEMENT("ROOM")):
        # Update relative exit's location.
        model_name = ELEMENT("EXIT").model_name
        if model_name:
            general_query_mapper.filter_records(model_name, location=old_key).update(location=new_key)
            general_query_mapper.filter_records(model_name, destination=old_key).update(destination=new_key)

        # Update relative world object's location.
        model_name = ELEMENT("WORLD_OBJECT").model_name
        if model_name:
            general_query_mapper.filter_records(model_name, location=old_key).update(location=new_key)

        # Update relative world NPC's location.
        model_name = ELEMENT("WORLD_NPC").model_name
        if model_name:
            general_query_mapper.filter_records(model_name, location=old_key).update(location=new_key)
