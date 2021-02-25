"""
DialogueHandler

The DialogueHandler maintains a pool of dialogues.

"""

from evennia.utils import logger
from muddery.server.utils.builder import build_object
from muddery.server.mappings.element_set import ELEMENT
from muddery.server.utils.localized_strings_handler import _
from muddery.server.database.dao.shop_goods import ShopGoods


class MudderyShop(ELEMENT("OBJECT")):
    """
    A shop.
    """
    element_key = "SHOP"
    element_name = _("Shop", "elements")
    model_name = "shops"

    def at_object_creation(self):
        """
        Called once, when this object is first created. This is the
        normal hook to overload for most object types.

        It will be called when swap its typeclass, so it must keep
        old values.
        """
        super(MudderyShop, self).at_object_creation()

    def at_object_delete(self):
        """
        Called just before the database object is permanently
        delete()d from the database. If this method returns False,
        deletion is aborted.

        All goods will be removed too.
        """
        result = super(MudderyShop, self).at_object_delete()
        if not result:
            return result

        # delete all goods
        for goods in self.goods.values():
            goods.delete()

        return True

    def after_data_loaded(self):
        """
        Set data_info to the object.

        Returns:
            None
        """
        super(MudderyShop, self).after_data_loaded()

        # load shop goods
        self.load_goods()
        
        self.verb = self.const.verb

    def load_goods(self):
        """
        Load shop goods.
        """
        # shops records
        goods_records = ShopGoods.get(self.get_data_key())

        goods_keys = set([record.key for record in goods_records])

        # current goods
        self.goods = self.states.load("goods", {})
        changed = False

        # remove old goods
        diff = set(self.goods.keys()) - goods_keys
        if len(diff) > 0:
            changed = True
            for goods_key in diff:
                # remove goods that is not in goods_keys
                self.goods[goods_key].delete()
                del self.goods[goods_key]

        # add new goods
        for goods_record in goods_records:
            goods_key = goods_record.key
            if goods_key not in self.goods:
                # Create shop_goods object.
                goods_obj = build_object(goods_key)
                if not goods_obj:
                    logger.log_errmsg("Can't create goods: %s" % goods_key)
                    continue

                self.goods[goods_key] = goods_obj
                changed = True

        if changed:
            self.states.save("goods", self.goods)

    def show_shop(self, caller):
        """
        Send shop data to the caller.

        Args:
            caller (obj): the custom
        """
        if not caller:
            return

        info = self.return_shop_info(caller)
        caller.msg({"shop": info})

    def return_shop_info(self, caller):
        """
        Get shop information.

        Args:
            caller (obj): the custom
        """
        info = {
            "dbref": self.dbref,
            "name": self.get_name(),
            "desc": self.get_desc(caller),
            "icon": self.icon,
        }

        goods_list = self.return_shop_goods(caller)
        info["goods"] = goods_list
            
        return info
                
    def return_shop_goods(self, caller):
        """
        Get shop's information.

        Args:
            caller (obj): the custom
        """
        goods_list = []

        # Get shop goods
        for obj in self.goods.values():
            if not obj.is_available(caller):
                continue

            goods = {
                "dbref": obj.dbref,
                "name": obj.name,
                "desc": obj.desc,
                "number": obj.number,
                "price": obj.price,
                "unit": obj.unit_name,
                "icon": obj.icon
            }
            
            goods_list.append(goods)

        return goods_list
