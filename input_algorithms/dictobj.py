from namedlist import namedlist

class dictobj(dict):
    fields = None

    def make_defaults(self):
        """Make a namedtuple for extracting our wanted keys"""
        if not self.fields:
            return namedlist("Defaults", [])
        else:
            fields = []
            for field in self.fields:
                if isinstance(field, (tuple, list)):
                    name, dflt = field
                    if callable(dflt):
                        dflt = dflt()
                    fields.append((name, dflt))
                else:
                    fields.append(field)
            return namedlist("Defaults", fields)

    def __init__(self, *args, **kwargs):
        super(dictobj, self).__init__()
        self.setup(*args, **kwargs)

    def setup(self, *args, **kwargs):
        defaults = self.make_defaults()(*args, **kwargs)
        for field in defaults._fields:
            self[field] = getattr(defaults, field)

    def __getattr__(self, key):
        """Pretend object access"""
        key = unicode(key)
        if key not in self or hasattr(self.__class__, key):
            return object.__getattribute__(self, key)

        try:
            return super(dictobj, self).__getitem__(key)
        except KeyError as e:
            if e.message == key:
                raise AttributeError(key)
            else:
                raise

    def __getitem__(self, key):
        key = unicode(key)
        if key not in self or hasattr(self.__class__, key):
            return object.__getattribute__(self, key)
        else:
            return super(dictobj, self).__getitem__(key)

    def __setattr__(self, key, val):
        """Pretend object setter access"""
        if hasattr(self.__class__, key):
            object.__setattr__(self, key, val)
        self[key] = val

    def __setitem__(self, key, val):
        if hasattr(self.__class__, key):
            object.__setattr__(self, key, val)
        super(dictobj, self).__setitem__(key, val)

