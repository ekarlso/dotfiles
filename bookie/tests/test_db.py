from bookie.testing import UnitTestBase
from bookie.models import models as m

import logging
from pprint import pprint
logging.basicConfig()


class TestUser(UnitTestBase):
    def setUp(self):
        super(TestUser, self).setUp()
        logging.getLogger("sqlalchemy.engine").setLevel(logging.WARN)
        self.u = m.User.by_user_name("admin")

    def test_perms_from_dict(self):
        self.u.from_dict(dict(user_permissions=[dict(perm_name="admin")]))

    def test_update_uname_changes_perms(self):
        """
        Had experiences earlier where if you change names it would screw
        permissions
        """
        self.u.from_dict(dict(user_permissions=[dict(perm_name="admin")]))
        self.u.from_dict(dict(user_name="test"))
        self.assertTrue(("test", "admin") in self.u.permissions)

    def test_clear_groups_changes_data(self):
        data = self.u.to_dict()
        self.u.from_dict(dict(groups=[])).save()
        self.assertEquals(data, self.u.to_dict())

    def test_add_group(self):
        """
        Just test that groups are added correctly using from_dict
        """
        self.u.from_dict({"groups": [{"group_name": "System Admins"}]}).save()
        self.assertEquals(len(self.u.groups), 1)
        self.u.from_dict({"groups": [
            {"group_name": "System Admins"}, {"group_name": "RentOurWrecks Inc"}]}).save()
        self.assertEquals(len(self.u.groups), 2)

class TestGroup(UnitTestBase):
    def setUp(self):
        super(TestGroup, self).setUp()
        self.g = m.Group.by_group_name("System Admins")
