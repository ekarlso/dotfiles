from pprint import pprint
import unittest

from mock import patch
from mock import MagicMock

from bookie.testing import Dummy
from bookie.testing import DummyRequest
from bookie.views.helpers.menu import Dropdown, Menu, MenuItem, Sidebar


MENU = {"value": "Home", "url": "#", "children": [
        {"value": "child1", "url": "child1", "icon": "user"},
        {"value": "divider"},
        {"value": "child2", "url": "child2", "children": [
            {"value": "subchild", "url": "subchild"}]
        },
        {"value": "child3", "url": "child3", "children": [
            {"value": "subchild", "url": "subchild"}]}
        ]}


class TestMenuItem(unittest.TestCase):
    def make(self, menu=MENU):
        return MenuItem(Dummy(), DummyRequest(), **menu)

    def test_menu_structure(self):
        """
        Test that a menu is created as it should
        """
        m = self.make()
        self.assertEquals(m.value, "Home")
        self.assertEquals(m.url, "#")
        self.assertEquals(m.children[0].value, "child1")
        self.assertEquals(m.children[0].url, "child1")
        self.assertNotEquals(m.children[0].icon, None)
        self.assertEquals(m.children[1].value, "divider")
        self.assertEquals(m.children[2].value, "child2")
        self.assertEquals(m.children[2].url, "child2")
        self.assertEquals(m.children[2].children[0].value, "subchild")
        self.assertEquals(m.children[2].children[0].url, "subchild")
        self.assertEquals(m.children[3].value, "child3")
        self.assertEquals(m.children[3].url, "child3")
        self.assertEquals(m.children[3].children[0].value, "subchild")
        self.assertEquals(m.children[3].children[0].url, "subchild")

    def test_menu_is_parents(self):
        m = self.make()
        self.assertEquals(m.is_parent, True)
        self.assertEquals(m.children[0].is_parent, False)
        self.assertEquals(m.children[1].is_parent, False)
        self.assertEquals(m.children[2].is_parent, True)
        self.assertEquals(m.children[2].is_parent, True)


class TestMenu(unittest.TestCase):
    cls = Menu

    def make(self, menu=MENU):
        return self.cls(Dummy(), DummyRequest(), menu)


class TestDropdown(TestMenu):
    cls = Dropdown

    def test_html(self):
        m = self.make()


class TestSidebar(TestMenu):
    cls = Sidebar

    def test_html(self):
        m = self.make()


if __name__ == '__main__':
    unittest.main()
