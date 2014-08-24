from collections import namedtuple
import six

def objMaker(clsName, *fields):
    """
        Return a namedtuple with an init that defaults the fields to specified defaults

        Usage is like::

            class Task(objMaker("Task", ("one", 1), "two", ("three", 2))): pass

        This will create a class called "Task" that can be called as so::

            task = Task()
            task = Task(1, 2, 3)
            task = Task(two=2)
            task = Task(1, three=4)

        And it will set positional arguments in the same order as they are provided to objMaker

        And any missing argument will be defaulted to the value set by calling objMaker,
        Or if no default value is given, it will default to None
    """
    keys = []
    dflts = {}
    for field in fields:
        if isinstance(field, six.string_types):
            keys.append(field)
            dflts[field] = None
        else:
            key, dflt = field
            keys.append(key)
            dflts[key] = dflt

    def __new__(cls, *args, **kwargs):
        for index, key in enumerate(keys):
            if index >= len(args) and key not in kwargs:
                kwargs[key] = dflts[key]
        return super(kls, cls).__new__(cls, *args, **kwargs)
    kls = type(clsName, (namedtuple(clsName, keys), ), {"__new__": __new__})
    return kls

