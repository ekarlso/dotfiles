from pprint import pprint
import unittest

from mock import patch
from mock import MagicMock

from bookie.testing import Dummy
from bookie.testing import DummyRequest
from bookie.views.helpers.menu import Menu, MenuItem


MENU = {"title": "Home", "url": "#", "children": [
        {"title": "child1", "url": "child1"},
        {"title": "child2", "url": "child2", "children": [
            {"title": "subchild", "url": "subchild"}]
        },
        {"title": "child3", "url": "child3", "children": [
            {"title": "subchild", "url": "subchild"}]}
        ]}


class TestMenuItem(unittest.TestCase):
    def make(self, menu=MENU):
        return MenuItem(Dummy(), DummyRequest(), **menu)

    def test_menu_structure(self):
        """
        Test that a menu is created as it should
        """
        m = self.make()
        self.assertEquals(m.title, "Home")
        self.assertEquals(m.url, "#")
        self.assertEquals(m.children[0].title, "child1")
        self.assertEquals(m.children[0].url, "child1")
        self.assertEquals(m.children[1].title, "child2")
        self.assertEquals(m.children[1].url, "child2")
        self.assertEquals(m.children[1].children[0].title, "subchild")
        self.assertEquals(m.children[1].children[0].url, "subchild")
        self.assertEquals(m.children[2].title, "child3")
        self.assertEquals(m.children[2].url, "child3")
        self.assertEquals(m.children[2].children[0].title, "subchild")
        self.assertEquals(m.children[2].children[0].url, "subchild")

    def test_menu_is_parents(self):
        m = self.make()
        self.assertEquals(m.is_parent, True)
        self.assertEquals(m.children[0].is_parent, False)
        self.assertEquals(m.children[1].is_parent, True)
        self.assertEquals(m.children[2].is_parent, True)

class TestMenu(unittest.TestCase):
    def make(self, menu=MENU):
        return Menu(Dummy(), DummyRequest, menu)

    def test(self):
        m = self.make()
        for i in m.items.items():
            print i.title, i.is_parent


if __name__ == '__main__':
    unittest.main()
