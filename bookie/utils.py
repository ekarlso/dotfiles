import re
import urllib
import uuid

from plone.i18n.normalizer import urlnormalizer
from pyramid.i18n import get_locale_name, TranslationStringFactory
from pyramid.threadlocal import get_current_request
from repoze.lru import LRUCache

_ = TranslationStringFactory('bookie')


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


def disambiguate_name(name):
    parts = name.split(u'-')
    if len(parts) > 1:
        try:
            index = int(parts[-1])
        except ValueError:
            parts.append(u'1')
        else:
            parts[-1] = unicode(index + 1)
    else:
        parts.append(u'1')
    return u'-'.join(parts)


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


def camel_to_name(text, splitter=""):
    """
      >>> camel_case_to_name('FooBar')
      'foo_bar'
      >>> camel_case_to_name('TXTFile')
      'txt_file'
      >>> camel_case_to_name ('MyTXTFile')
      'my_txt_file'
      >>> camel_case_to_name('froBOZ')
      'fro_boz'
      >>> camel_case_to_name('f')
      'f'
    """
    return re.sub(
        r'((?<=[a-z])[A-Z]|(?<!\A)[A-Z](?=[a-z]))', r'_\1', text).lower()


def name_to_camel(string, joiner=""):
    """
    Convert a string with 'test_test' to 'TestTest'
    """
    return joiner.join([i.title() for i in string.split("_")])


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


def generate_uuid():
    return unicode(uuid.uuid4())


