from pprint import pprint
import unittest

from mock import patch
from mock import MagicMock

from bookie.testing import Dummy
from bookie.testing import DummyRequest


MENU = {"title": "Home", "url": "#", "children": [
        {"title": "child1", "url": "child1"},
        {"title": "child2", "url": "child2", "children": [
            {"title": "subchild", "url": "subchild"}]
        }]}

class TestMenuItem(unittest.TestCase):
    def make(self, menu=MENU):
        from bookie.views.helpers.menu import MenuItem
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


if __name__ == '__main__':
    unittest.main()
