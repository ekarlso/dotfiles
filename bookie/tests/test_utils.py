from unittest import TestCase

from pyramid.registry import Registry

from bookie.testing import DummyRequest
from bookie.testing import UnitTestBase


class TestRequestCache(UnitTestBase):
    def setUp(self):
        from bookie.utils import request_cache

        registry = Registry('testing')
        request = DummyRequest()
        request.registry = registry
        super(TestRequestCache, self).setUp(registry=registry, request=request)
        self.cache_decorator = request_cache

    def test_it(self):
        from bookie.utils import clear_cache

        called = []

        @self.cache_decorator(lambda a, b: (a, b))
        def my_fun(a, b):
            called.append((a, b))

        my_fun(1, 2)
        my_fun(1, 2)
        self.assertEqual(len(called), 1)
        my_fun(2, 1)
        self.assertEqual(len(called), 2)

        clear_cache()
        my_fun(1, 2)
        self.assertEqual(len(called), 3)

    def test_dont_cache(self):
        from bookie.utils import DontCache
        called = []

        def dont_cache(a, b):
            raise DontCache

        @self.cache_decorator(dont_cache)
        def my_fun(a, b):
            called.append((a, b))

        my_fun(1, 2)
        my_fun(1, 2)
        self.assertEqual(len(called), 2)


class TestLRUCache(TestRequestCache):
    def setUp(self):
        from bookie.utils import lru_cache

        super(TestLRUCache, self).setUp()
        self.cache_decorator = lru_cache
