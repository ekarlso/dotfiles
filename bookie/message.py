from html2text import HTML2Text
from pyramid_mailer.mailer import Mailer
from pyramid_mailer.message import Message
from pyramid.renderers import render

from . import get_settings


def get_mailer():
    return Mailer.from_settings(get_settings())


def send(subject=None, sender=None, recipients=[], html=None,
        template="mail.mako", request=None, variables={}):
    settings = get_settings()

    template = "message/%s" % template

    data = request.user.to_dict() if request and request.user else {}
    data.update(variables)

    data["site_title"] = settings["bookie.site_title"]

    text = render(template, data, request)
    subject, htmlbody = text.strip().split('\n', 1)
    subject = subject.replace('Subject:', '', 1).strip()
    html2text = HTML2Text()
    html2text.body_width = 0
    textbody = html2text.handle(htmlbody).strip()

    message = Message(recipients=recipients, subject=subject, body=textbody,
            html=htmlbody)

    mailer = get_mailer()
    mailer.send(message)


def includeme(config):
    pass
