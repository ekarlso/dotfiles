from unittest import TestCase
from mock import patch
from mock import MagicMock

from bookie.testing import Dummy
from bookie.testing import DummyRequest

from bookie.db import models as m


class TestBooking(TestCase):
    def test_latest(self):
        self.assertEquals(len(m.Booking.latest()), 2)
