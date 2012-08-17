import unittest

from pyramid.registry import Registry

from bookie.models import models
from bookie.testing import Dummy, DummyRequest, UnitTestBase

from bookie.views import misc


class TestMessage(UnitTestBase):
    def make(self):
        request = DummyRequest()
        request.context = Dummy()
        request.user = models.User.by_user_name("r1_booker")
        return request

    def test_possible_recipients(self):
        """
        Test that we resolve recipients correctly...
        """
        request = self.make()
        recipients = misc.possible_recipients(request)

        # NOTE: Username shouldn't be in recipients list
        self.assertEquals("u:" + request.user.user_name in recipients, False)
        self.assertEquals(request.user.user_name in recipients.values(), False)

        # NOTE: Group should be in recipients
        self.assertEquals("g:" + request.user.groups[0].uuid in recipients, True)
        self.assertEquals(request.user.groups[0].group_name in recipients.values(), True)

    def test_recipient_resolve(self):
        """
        test that a recipient string resolves correctly.

        calling recipient_resolve with "type:value" should
        return ("type", "value").
        """
        self.assertEquals(misc.recipient_resolve("g:group"), ("group", "group"))
        self.assertEquals(misc.recipient_resolve("u:user"), ("user", "user"))

    def test_send_message(self):
        message = models.Message(content="random_content").save()
        user = models.User.by_id(1)

        assoc = models.MessageAssociation(user_id=user.id, message_id=message.id).save()
        assoc.save()

        # NOTE: This should be ok...
        self.assertEquals(assoc.user_id, 1)
        self.assertEquals(assoc.message_id, message.id)


if __name__ == '__main__':
    unittest.main()

