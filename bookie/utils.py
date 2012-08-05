import re
import urllib

from pyramid.i18n import get_locale_name, TranslationStringFactory, \
    get_localizer, make_localizer
from pyramid.threadlocal import get_current_request
from repoze.lru import LRUCache
from webhelpers_extra.utils import *

tsf = TranslationStringFactory('bookie')
_ = tsf


"""
What to put in here?

"Generic" utilities that are not View / HTML specific
See <pkg>.views.helpers.utils for more info.
"""

class DontCache(Exception):
    pass

_CACHE_ATTR = 'bookie_cache'


def request_container():
    request = get_current_request()
    if request is None:
        return None
    cache = getattr(request, _CACHE_ATTR, None)
    if cache is None:
        cache = {}
        setattr(request, _CACHE_ATTR, cache)
    return cache


def cache(compute_key, container_factory):
    marker = object()

    def decorator(func):
        def replacement(*args, **kwargs):
            cache = container_factory()
            if cache is None:
                return func(*args, **kwargs)
            try:
                key = compute_key(*args, **kwargs)
            except DontCache:
                return func(*args, **kwargs)
            key = '%s.%s:%s' % (func.__module__, func.__name__, key)
            cached_value = cache.get(key, marker)
            if cached_value is marker:
                #print "\n*** MISS %r ***" % key
                cached_value = cache[key] = func(*args, **kwargs)
            else:
                #print "\n*** HIT %r ***" % key
                pass
            return cached_value
        replacement.__doc__ = func.__doc__
        return replacement
    return decorator


def request_cache(compute_key):
    return cache(compute_key, request_container)


class LRUCacheSetItem(LRUCache):
    __setitem__ = LRUCache.put

_lru_cache = LRUCacheSetItem(1000)


def lru_cache(compute_key):
    return cache(compute_key, lambda: _lru_cache)


def clear_cache():  # only useful for tests really
    request = get_current_request()
    if request is not None:
        setattr(request, _CACHE_ATTR, None)
    _lru_cache.clear()


def add_renderer_globals(event):
    request = event["request"]
    event['_'] = request.translate
    event['localizer'] = request.localizer


def add_localizer(event):
    request = event.request
    localizer = get_localizer(request)
    def auto_translate(string, mapping={}):
        return localizer.translate(tsf(string, mapping=mapping))
    request.localizer = localizer
    request.translate = auto_translate


def get_localizer_for_locale_name(locale_name):
    registry = get_current_registry()
    tdirs = registry.queryUtility(ITranslationDirectories, default=[])
    return make_localizer(locale_name, tdirs)


def translate(*args, **kwargs):
    request = get_current_request()
    if request is None:
        localizer = get_localizer_for_locale_name('en')
    else:
        localizer = get_localizer(request)
    return localizer.translate(*args, **kwargs)
