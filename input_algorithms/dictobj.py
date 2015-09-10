from namedlist import namedlist

empty_defaults = namedlist("Defaults", [])
cached_namedlists = {}

class dictobj(dict):
    fields = None
    is_dict = True

    def make_defaults(self):
        """Make a namedtuple for extracting our wanted keys"""
        if not self.fields:
            return empty_defaults
        else:
            fields = []
            end_fields = []
            for field in self.fields:
                if isinstance(field, (tuple, list)):
                    name, dflt = field
                    if callable(dflt):
                        dflt = dflt()
                    end_fields.append((name, dflt))
                else:
                    fields.append(field)

            joined = fields + end_fields
            identifier = str(joined)
            if identifier not in cached_namedlists:
                cached_namedlists[identifier] = namedlist("Defaults", joined)
            return cached_namedlists[identifier]

    def __init__(self, *args, **kwargs):
        super(dictobj, self).__init__()
        self.setup(*args, **kwargs)

    def __nonzero__(self):
        return True

    def setup(self, *args, **kwargs):
        defaults = self.make_defaults()(*args, **kwargs)
        for field in defaults._fields:
            self[field] = getattr(defaults, field)

    def __getattr__(self, key):
        """Pretend object access"""
        key = str(key)
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
        key = str(key)
        if key not in self or hasattr(self.__class__, key):
            return object.__getattribute__(self, key)
        else:
            return super(dictobj, self).__getitem__(key)

    def __setattr__(self, key, val):
        """Pretend object setter access"""
        if hasattr(self.__class__, key):
            object.__setattr__(self, key, val)
        self[key] = val

    def __delattr__(self, key):
        if key in self:
            del self[key]
        else:
            object.__delattr__(self, key)

    def __setitem__(self, key, val):
        if hasattr(self.__class__, key):
            object.__setattr__(self, key, val)
        super(dictobj, self).__setitem__(key, val)

    def clone(self):
        """Return a clone of this object"""
        return self.__class__(**dict((name, self[name]) for name in self.fields))

    def as_dict(self, **kwargs):
        """Return as a deeply nested dictionary"""
        result = {}
        for field in self.fields:
            if isinstance(field, (list, tuple)):
                field, _ = field
            val = self[field]
            if hasattr(val, "as_dict"):
                result[field] = val.as_dict(**kwargs)
            else:
                result[field] = val
        return result

