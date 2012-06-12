import os
from unittest import TestCase

from pyramid import testing
from pyramid.config import DEFAULT_RENDERERS
from pyramid.security import ALL_PERMISSIONS
import transaction

BASE_URL = 'http://localhost:6543'


class Dummy(dict):
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


class DummyRequest(testing.DummyRequest):
    is_xhr = False
    POST = dict()

    def is_response(self, ob):
        return (hasattr(ob, 'app_iter') and hasattr(ob, 'headerlist') and
                hasattr(ob, 'status'))


def testing_db_url():
    return os.environ.get('BOOKIE_TEST_DB_STRING', 'sqlite://')


def _initTestingDB():
    from sqlalchemy import create_engine
    from bookie.models import configure_db

    database_url = testing_db_url()
    session = configure_db({"sqlalchemy.url": database_url})
    return session


def _populator():
    from bookie import DBSession
    from bookie.resources import Document
    from bookie.populate import populate

    populate()
    for doc in DBSession.query(Document)[1:]:
        DBSession.delete(doc)
    transaction.commit()


def _turn_warnings_into_errors():  # pragma: no cover
    # turn all warnings into errors, but let the `ImportWarning`
    # produced by Babel's `localedata.py` vs `localedata/` show up once...
    from babel import localedata
    localedata  # make pyflakes happy... :p
    from warnings import filterwarnings
    filterwarnings("error")


def setUp(init_db=True, **kwargs):
    from bookie import _resolve_dotted
    from bookie import conf_defaults

    tearDown()
    settings = conf_defaults.copy()
    settings['bookie.secret'] = 'secret'
    settings['bookie.secret2'] = 'secret2'
    settings['bookie.populators'] = 'bookie.testing._populator'
    settings.update(kwargs.get('settings', {}))
    _resolve_dotted(settings)
    kwargs['settings'] = settings
    config = testing.setUp(**kwargs)
    for name, renderer in DEFAULT_RENDERERS:
        config.add_renderer(name, renderer)

    if init_db:
        _initTestingDB()

    transaction.begin()
    return config


def tearDown():
    from bookie import security

    # These should arguable use the configurator, so they don't need
    # to be torn down separately:
    security.reset()

    transaction.abort()
    testing.tearDown()


class UnitTestBase(TestCase):
    def setUp(self, **kwargs):
        self.config = setUp(**kwargs)

    def tearDown(self):
        tearDown()


class EventTestBase(TestCase):
    def setUp(self, **kwargs):
        super(EventTestBase, self).setUp(**kwargs)
        self.config.include('bookie.events')

# Functional ----


def setUpFunctional(global_config=None, **settings):
    from bookie import main
    import wsgi_intercept.zope_testbrowser
    from webtest import TestApp

    tearDown()

    _settings = {
        'sqlalchemy.url': testing_db_url(),
        'bookie.secret': 'secret',
        'bookie.site_title': 'Bookie BETA',  # for mailing
        'bookie.populators': 'bookie.testing._populator',
        'mail.default_sender': 'bookie@localhost',
        }
    _settings.update(settings)

    host, port = BASE_URL.split(':')[-2:]
    app = main({}, **_settings)
    wsgi_intercept.add_wsgi_intercept(host[2:], int(port), lambda: app)
    Browser = wsgi_intercept.zope_testbrowser.WSGI_Browser

    return dict(
        Browser=Browser,
        browser=Browser(),
        test_app=TestApp(app),
        )


class FunctionalTestBase(TestCase):
    BASE_URL = BASE_URL

    def setUp(self, **kwargs):
        self.__dict__.update(setUpFunctional(**kwargs))

    def tearDown(self):
        tearDown()

    def login(self, login=u'admin', password=u'secret'):
        return self.test_app.post(
            '/@@login',
            {'login': login, 'password': password, 'submit': 'submit'},
            status=302,
            )

    def login_testbrowser(self, login=u'admin', password=u'secret'):
        browser = self.Browser()
        browser.open(BASE_URL + '/edit')
        browser.getControl("Username or email").value = login
        browser.getControl("Password").value = password
        browser.getControl(name="submit").click()
        return browser


class TestingRootFactory(dict):
    __name__ = ''  # root is required to have an empty name!
    __parent__ = None
    __acl__ = [('Allow', 'role:admin', ALL_PERMISSIONS)]

    def __init__(self, request):
        super(TestingRootFactory, self).__init__()


def dummy_view(context, request):
    return {}


def include_testing_view(config):
    config.add_view(
        dummy_view,
        context=TestingRootFactory,
        renderer='bookie:tests/testing_view.pt',
        )

    config.add_view(
        dummy_view,
        name='secured',
        permission='view',
        context=TestingRootFactory,
        renderer='bookie:tests/testing_view.pt',
        )


def setUpFunctionalStrippedDownApp(global_config=None, **settings):
    # An app that doesn't use Nodes at all
    _settings = {
        'bookie.base_includes': (
            'bookie bookie.views bookie.views.login bookie.views.site_setup '
            'bookie.views.users'),
        'bookie.use_tables': 'principals',
        'bookie.populators': 'bookie.populate.populate_users',
        'pyramid.includes': 'bookie.testing.include_testing_view',
        'bookie.root_factory': 'bookie.testing.TestingRootFactory',
        'bookie.site_title': 'My Stripped Down bookie',
        }
    _settings.update(settings)

    return setUpFunctional(global_config, **_settings)


def registerDummyMailer():
    from pyramid_mailer.mailer import DummyMailer
    from bookie.message import _inject_mailer

    mailer = DummyMailer()
    _inject_mailer.append(mailer)
    return mailer
