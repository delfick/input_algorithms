"""
This is an object that behaves like both an object (dot notation access to
attributes) and like a dictionary (square bracket notation access to attrs).

It is a subclass of ``dict`` and has ``is_dict`` set to True.

It will also generate an ``__init__`` for you based on what you specify as the
``fields`` attribute.

.. code-block:: python

    class MyAmazingKls(dictobj):
        fields = ["one", "two", ("three", 4)]

Creates an ``__init__`` that behaves like:

.. code-block:: python

    def __init__(self, one, two, three=4):
        self.one = one
        self.two = two
        self.three = three

``fields``
    Must be an iterable of strings where each string is a valid variable name.

    Or a tuple of ``(<variable_name>, <dflt_value>)`` where the ``<dflt_value>``
    is used if that variable is not passed into ``__init__``.

    Because it must be an iterable, it can also be a dictionary where the values
    are docstrings for the attributes!

    .. code-block:: python

        class MyAmazingKls(dictobj):
            fields = {
                  "one": "The first argument"
                , "two": "The second argument"
                , ("three", 4): "Optional third argument"
                }

    Is a perfectly valid example.

    Internally, ``dictobj`` uses a library called ``namedlist`` to validate the
    fields and work out the default values when an option isn't specified.

Once an instance of ``dictobj`` is created you may access the attributes however
you wish!

.. code-block:: python

    instance = MyAmazingKls(one=1, two=2)

    instance.one == 1
    instance["one"] == 1

    instance.three == 4

    list(instance.items()) == [("one", 1), ("two", 2), ("three", 4)]

    instance.as_dict() == {"one": 1, "two": 2, "three": 4}
"""
from input_algorithms.field_spec import Field, FieldSpecMetakls

from namedlist import namedlist
import six

empty_defaults = namedlist("Defaults", [])
cached_namedlists = {}

class dictobj(dict):
    fields = None
    is_dict = True

    Field = Field

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
        """
        Dictionaries are Falsey when empty, whereas we want this to be Truthy
        like a normal object
        """
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
        """
        If the key is on the class, then return that attribute, otherwise do a
        super call to ``dict.__getitem__``.
        """
        key = str(key)
        if key not in self or hasattr(self.__class__, key):
            return object.__getattribute__(self, key)
        else:
            return super(dictobj, self).__getitem__(key)

    def __setattr__(self, key, val):
        """
        If the key is on the class already, then set the value on the instance
        directly.

        We also do the equivalent of ``dict.__setitem__`` on this instance.
        """
        if hasattr(self.__class__, key):
            object.__setattr__(self, key, val)
        self[key] = val

    def __delattr__(self, key):
        """
        If the key is on the class itself, then delete the attribute from the
        instance, otherwise do a super call to ``dict.__delitem__`` on this
        instance.
        """
        if key in self:
            del self[key]
        else:
            object.__delattr__(self, key)

    def __setitem__(self, key, val):
        """
        If the key is on the class itself, then set the value as an attribute on
        the class, otherwise, use a super call to ``dict.__setitem__`` on this
        instance.
        """
        if hasattr(self.__class__, key):
            object.__setattr__(self, key, val)
        super(dictobj, self).__setitem__(key, val)

    def clone(self):
        """Return a clone of this object"""
        return self.__class__(**dict((name, self[name]) for name in self.fields))

    def as_dict(self, **kwargs):
        """
        Return as a deeply nested dictionary

        This will call ``as_dict`` on values if they have such an attribute.
        """
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

dictobj.Spec = six.with_metaclass(FieldSpecMetakls, dictobj)
