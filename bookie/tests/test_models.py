from unittest import TestCase

from pyramid.registry import Registry

from bookie.models.models import *
from bookie.testing import DummyRequest
from bookie.testing import UnitTestBase


class TestEntityMetadata(UnitTestBase):
    def make(self):
        return Entity(brand="Open", model="Safira", produced="test")

    def test_meta_set(self):
        """
        Test setting some metadata
        """
        e = self.make().save()
        e.meta_set({"gps": True})
        self.assertEquals(e.metadata.count(), 1)

    def test_meta_double_set(self):
        """
        Test setting the same value twice, it should only be added to the db
        with one entry
        """
        e = self.make().save()
        e.meta_set({"gps": True})
        e.meta_set({"gps": True})
        self.assertEquals(e.metadata.count(), 1)

    def test_get_non_existant(self):
        e = self.make().save()
        self.assertEquals(e.meta_get("color"), None)

    def test_meta_set_color(self):
        """
        Test setting a color
        """
        e = self.make().save()
        e.color = "green"
        self.assertEquals(e.color, "green")

    def test_meta_get_color(self):
        e = self.make().save()
        e.color = "yellow"
        self.assertEquals(e.color, "yellow")

