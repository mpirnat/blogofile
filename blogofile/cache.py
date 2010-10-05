import sys


class Cache(dict):
    """A cache object used for attatching things we want to remember

    This works like a normal object, attributes that are undefined
    raise an AttributeError
    
    >>> c = Cache()
    >>> c.whatever = "whatever"
    >>> c.whatever
    'whatever'
    >>> c.section.subsection.attribute = "whatever"
    Traceback (most recent call last):
      ...
    AttributeError: 'Cache' object has no attribute 'section'
    """
    def __init__(self, **kw):
        dict.__init__(self, kw)
        self.__dict__ = self


class HierarchicalCache(Cache):
    """A cache object used for attatching things we want to remember
    
    This works differently than a normal object, attributes that
    are undefined do *not* raise an AttributeError but are silently
    created as an additional HierarchicalCache object.
    
    >>> c = HierarchicalCache()
    >>> c.whatever = "whatever"
    >>> c.whatever
    'whatever'
    >>> c.section.subsection.attribute = "whatever"
    >>> c.section.subsection.attribute
    'whatever'
    >>> c.sub.d['one'].value.stuff = "whatever"
    >>> c.sub.d.one.value.stuff
    'whatever'
    >>> c.sub.d['one'].value.stuff
    'whatever'
    >>> c.sub.d['one.value.stuff']
    'whatever'
    >>> c.sub.d['one.value.stuff'] = "whatever2"
    >>> c.sub.d.one.value.stuff
    'whatever2'
    >>> c.sub.d.one.value.items()
    [('stuff', 'whatever2')]
    >>> c.sub.d.has_key("doesn't have this")
    False
    """
    def __getattr__(self, attr):
        if not attr.startswith("_") and \
                "(" not in attr and \
                "[" not in attr and \
                attr != "trait_names": 
            c = HierarchicalCache()
            Cache.__setitem__(self, attr, c)
            setattr(c, '_parent', self)
            setattr(c, '_key', attr)
            return c
        else:
            raise AttributeError

    def __getitem__(self, item):
        if not hasattr(item, 'split'):
            hierarchy = self._get_hierarchy()
            raise TypeError("'{0}' object '{1}' is not indexable or sliceable; "
                    "'{2}' may be an empty cache".format(
                            self.__class__.__name__,
                            hierarchy[-1]._key,
                            ".".join([x._key for x in hierarchy[:-1]])))
        dotted_parts = item.split(".")
        try:
            c = self.__getattribute__(dotted_parts[0])
        except AttributeError:
            c = self.__getattr__(item)
        for dotted_part in dotted_parts[1:]:
            c = getattr(c, dotted_part)
        return c

    def __setitem__(self, key, item):
        c = self
        try:
            try:
                dotted_parts = key.split(".")
            except AttributeError:
                return
            if len(dotted_parts) > 1:
                c = self.__getitem__(".".join(dotted_parts[:-1]))
                key = dotted_parts[-1]
        finally:
            Cache.__setitem__(c, key, item)

    def __call__(self, *args, **kwargs):
        hierarchy = self._get_hierarchy()
        raise TypeError("'{0}' object '{1}' is not callable; "
                "'{2}' may be an empty cache".format(
                        self.__class__.__name__,
                        hierarchy[-1]._key,
                        ".".join([x._key for x in hierarchy[:-1]])))

    def _get_hierarchy(self):
        hierarchy = []
        x = self
        while hasattr(x, '_parent'):
            hierarchy.append(x)
            x = x._parent
        hierarchy.reverse()
        return hierarchy


#The main blogofile cache object, transfers state between templates
bf = HierarchicalCache()
sys.modules['blogofile_bf'] = bf
bf.cache = sys.modules['blogofile.cache']
