"""
Exits

Exits are connectors between Rooms. An exit always has a destination property
set and has a single command defined on itself with the same name as its key,
for allowing Characters to traverse the exit to its destination.

"""

from muddery.server.statements.statement_handler import STATEMENT_HANDLER
from muddery.server.utils.localized_strings_handler import _
from muddery.server.mappings.element_set import ELEMENT


class MudderyLockedExit(ELEMENT("EXIT")):
    """
    Characters must unlock these exits to pass it.
    The view and commands of locked exits are different from unlocked exits.
    """
    element_type = "LOCKED_EXIT"
    element_name = _("Locked Exit", "elements")
    model_name = "exit_locks"

    def after_data_loaded(self):
        """
        Set data_info to the object."
        """
        super(MudderyLockedExit, self).after_data_loaded()

        self.unlock_condition = self.const.unlock_condition
        self.unlock_verb = self.const.unlock_verb
        self.locked_desc = self.const.locked_desc
        self.auto_unlock = self.const.auto_unlock
        self.unlock_forever = self.const.unlock_forever

    def at_before_traverse(self, traversing_object):
        """
        Called just before an object uses this object to traverse to
        another object (i.e. this object is a type of Exit)

        Args:
            traversing_object (Object): The object traversing us.

        Notes:
            The target destination should normally be available as
            `self.destination`.
            
            If this method returns False/None, the traverse is cancelled
            before it is even started.

        """
        if not super(MudderyLockedExit, self).at_before_traverse(traversing_object):
            return False

        # Only can pass exits which have already been unlocked.
        if traversing_object.is_exit_unlocked(self.get_object_key()):
            if not self.unlock_forever:
                # lock the exit again
                traversing_object.lock_exit(self)
            return True

        if self.auto_unlock and self.can_unlock(traversing_object):
            # Can unlock the exit automatically.
            if self.unlock_forever:
                # Unlock it.
                traversing_object.unlock_exit(self)
            return True

        # Show the object's appearance.
        appearance = self.get_appearance(traversing_object)
        traversing_object.msg({"look_obj": appearance})
        return False

    def can_unlock(self, caller):
        """
        Unlock an exit.
        """
        # Only can unlock exits which match there conditions.
        return STATEMENT_HANDLER.match_condition(self.unlock_condition, caller, self)

    def get_appearance(self, caller):
        """
        This is a convenient hook for a 'look'
        command to call.
        """
        # Get name and description.
        if caller.is_exit_unlocked(self.get_object_key()):
            # If is unlocked, use common appearance.
            return super(MudderyLockedExit, self).get_appearance(caller)

        can_unlock = self.can_unlock(caller)

        if self.auto_unlock and can_unlock:
            if self.unlock_forever:
                # Automatically unlock the exit when a character looking at it.
                caller.unlock_exit(self)
            
            # If is unlocked, use common appearance.
            return super(MudderyLockedExit, self).get_appearance(caller)

        cmds = []
        if can_unlock:
            # show unlock command
            verb = self.unlock_verb
            if not verb:
                verb = _("Unlock")
            cmds = [{"name": verb, "cmd": "unlock_exit", "args": self.dbref}]
        
        info = {"dbref": self.dbref,
                "name": self.name,
                "desc": self.locked_desc,
                "cmds": cmds}
                
        return info

    def get_available_commands(self, caller):
        """
        This returns a list of available commands.
        "args" must be a string without ' and ", usually it is self.dbref.
        """
        if caller.is_exit_unlocked(self.get_object_key()):
            # If is unlocked, use common commands.
            return super(MudderyLockedExit, self).get_available_commands(caller)

        cmds = []
        can_unlock = STATEMENT_HANDLER.match_condition(self.unlock_condition, caller, self)
        if can_unlock:
            # show unlock command
            verb = self.unlock_verb
            if not verb:
                verb = _("Unlock")
            cmds = [{"name": verb, "cmd": "unlock", "args": self.dbref}]

        return cmds

