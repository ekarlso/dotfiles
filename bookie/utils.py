import re
import urllib

from plone.i18n.normalizer import urlnormalizer
from pyramid.i18n import get_locale_name, TranslationStringFactory
from pyramid.threadlocal import get_current_request
from repoze.lru import LRUCache

_ = TranslationStringFactory('bookie')


class DontCache(Exception):
    pass

_CACHE_ATTR = 'kotti_cache'


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


def title_to_name(title, blacklist=()):
    request = get_current_request()
    if request is not None:
        locale_name = get_locale_name(request)
    else:
        locale_name = 'en'
    name = unicode(urlnormalizer.normalize(title, locale_name, max_length=40))
    while name in blacklist:
        name = disambiguate_name(name)
    return name


def cap_to_us(string):
    """
    Converts 'TestTest' to 'test_test'
    """
    underscored = "_".join(re.findall('[A-Z][^A-Z]*', string))
    return underscored.lower()


def us_to_cap(string):
    """
    Convert a string with 'test_test' to 'TestTest'
    """
    return "".join([i.title() for i in string.split("_")])
