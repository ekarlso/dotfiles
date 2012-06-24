from unittest import TestCase

from bookie.testing import Dummy, DummyRequest, UnitTestBase

from bookie import models
from bookie.views.helpers import AddFormView
from bookie.views.bookings import BookingSchema


class TestForm(AddFormView):
    item_type = "Test"


class TestAddForm(UnitTestBase):
    def test_something(self):
        f = TestForm(Dummy(), DummyRequest(),
            schema=models.Booking.get_schema())()
