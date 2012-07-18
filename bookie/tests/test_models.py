from unittest import TestCase

from pyramid.registry import Registry

from bookie.models.models import *
from bookie.testing import DummyRequest
from bookie.testing import UnitTestBase


class TestEntity(UnitTestBase):
    def make(self):
        return Entity(brand="Open", model="Safira", produced="test")

    def test_set_meta(self):
        e = self.make().save()
        e.set_meta("gps", True)
        self.assertEquals(e.metadata.count(), 1)

    def test_double_set_meta(self):
        e = self.make().save()
        e.set_meta("gps", 1)
        e.set_meta("gps", 1)
        self.assertEquals(e.metadata.count(), 1)

    def test_set_color(self):
        e = self.make().save()
        e.color = "green"
        self.assertEquals(e.color, "green")
