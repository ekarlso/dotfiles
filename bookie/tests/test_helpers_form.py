from unittest import TestCase

from mock import patch
from mock import MagicMock

from bookie.testing import Dummy
from bookie.testing import DummyRequest


class TestBaseFormView(TestCase):
    def make(self):
        from bookie.views.helpers.form import BaseFormView
        return BaseFormView(Dummy(), DummyRequest())

    def test_init(self):
        from bookie.views.helpers.form import BaseFormView
        view = BaseFormView(Dummy(), DummyRequest(), more='args')
        assert view.more == 'args'

    def test_schema_factory_bind(self):
        view = self.make()
        schema = MagicMock()
        view.schema_factory = lambda: schema
        view.__call__()
        assert view.schema == schema.bind.return_value
        schema.bind.assert_called_with(request=view.request)

    def test_use_csrf_token(self):
        view = self.make()
        schema = view.schema = MagicMock()
        view.__call__()
        assert schema.children.append.called
        assert schema.children.append.call_args[0][0].name == 'csrf_token'

    def test_use_csrf_token_not(self):
        view = self.make()
        view.use_csrf_token = False
        schema = view.schema = MagicMock()
        view.__call__()
        assert not schema.children.append.called


class TestGetAppstruct(TestCase):
    def call(self, *args, **kwargs):
        from bookie.views.helpers.form import get_appstruct
        return get_appstruct(*args, **kwargs)

    def test_schema_has_more_children_than_attrs(self):
        context = Dummy(first='firstvalue')
        schema = Dummy(children=[Dummy(name='first'), Dummy(name='second')])
        assert self.call(context, schema) == {'first': 'firstvalue'}

    def test_schema_has_fewer_children_than_attrs(self):
        context = Dummy(first='firstvalue', second='secondvalue')
        schema = Dummy(children=[Dummy(name='first')])
        assert self.call(context, schema) == {'first': 'firstvalue'}


class TestEditFormView(TestCase):
    def make(self):
        from bookie.views.helpers.form import EditFormView
        return EditFormView(
            Dummy(), DummyRequest(), success_url='http://localhost')

    def test_before(self):
        view = self.make()
        view.context.three = 3
        view.schema = Dummy()
        view.schema.children = [Dummy(name='three')]
        form = Dummy()
        view.before(form)
        assert form.appstruct == {'three': 3}

    def test_save_success_calls_edit(self):
        view = self.make()
        view.edit = MagicMock()
        view.save_success({'three': 3})
        view.edit.assert_called_with(three=3)

    def test_save_success_redirects(self):
        view = self.make()
        result = view.save_success({'three': 3})
        assert result.status == '302 Found'
        assert result.location == view.success_url

    def test_save_success_redirects_to_resource_url(self):
        view = self.make()
        view.success_url = None
        view.request.resource_url = lambda context: context.__class__.__name__
        result = view.save_success({'three': 3})
        assert result.status == '302 Found'
        assert result.location == 'Dummy'



class TestAddFormView(TestCase):
    def make(self):
        from bookie.views.helpers.form import AddFormView
        return AddFormView(Dummy(), DummyRequest())

    def test_save_success_calls_add(self):
        view = self.make()
        view.add = MagicMock()
        view.find_name = lambda appstruct: 'somename'
        view.request.resource_url = lambda context: u''
        view.save_success({'three': 3})
        view.add.assert_called_with(three=3)
        assert view.add.return_value == view.context['somename']

    def test_save_success_redirects(self):
        view = self.make()
        view.add = MagicMock()
        view.find_name = lambda appstruct: 'somename'
        view.request.resource_url = lambda context: u'MagicMock'
        result = view.save_success({'three': 3})
        assert result.status == '302 Found'
        assert result.location == 'MagicMock'

    def test_save_success_redirects_custom_url(self):
        view = self.make()
        view.add = MagicMock()
        view.success_url = 'there'
        view.find_name = lambda appstruct: 'somename'
        result = view.save_success({'three': 3})
        assert result.status == '302 Found'
        assert result.location == 'there'

    @patch('bookie.views.helpers.form.title_to_name')
    def test_find_name_uses_title_to_name(self, title_to_name):
        view = self.make()
        title_to_name.return_value = 'cafe'
        assert view.find_name({'title': 'Bar'}) == 'cafe'
        title_to_name.assert_called_with('Bar', blacklist=[])
