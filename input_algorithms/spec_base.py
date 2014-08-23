from input_algorithms.errors import BadSpec, BadSpecValue, BadDirectory, BadFilename

from option_merge import MergedOptions
import operator
import six
import os

class NotSpecified(object):
    """Tell the difference between None and not specified"""

class Spec(object):
    def __init__(self, *pargs, **kwargs):
        self.pargs = pargs
        self.kwargs = kwargs
        if hasattr(self, "setup"):
            self.setup(*pargs, **kwargs)

    def normalise(self, meta, val):
        """Use this spec to normalise our value"""
        if hasattr(self, "normalise_either"):
            result = self.normalise_either(meta, val)
            if result is not NotSpecified:
                return result

        if val is NotSpecified:
            if hasattr(self, "normalise_empty"):
                return self.normalise_empty(meta)
            elif hasattr(self, "default"):
                return self.default
            else:
                return val
        elif hasattr(self, "normalise_filled"):
            return self.normalise_filled(meta, val)

        raise BadSpec("Spec doesn't know how to deal with this value", spec=self, meta=meta, val=val)

class pass_through_spec(Spec):
    def normalise_either(self, meta, val):
        return val

class always_same_spec(Spec):
    def setup(self, result):
        self.result = result

    def normalise_either(self, meta, val):
        return self.result

class dictionary_spec(Spec):
    @property
    def default(self):
        return {}

    def normalise_filled(self, meta, val):
        """Make sure it's a dictionary or MergedOptions"""
        if not isinstance(val, dict) and not isinstance(val, MergedOptions):
            raise BadSpecValue("Expected a dictionary", meta=meta, got=type(val))

        return val

class dictof(dictionary_spec):
    def setup(self, name_spec, value_spec):
        self.name_spec = name_spec
        self.value_spec = value_spec

    def normalise_filled(self, meta, val):
        """Make sure all the names match the spec and normalise the values"""
        val = super(dictof, self).normalise_filled(meta, val)

        result = {}
        errors = []
        for key, value in val.items():
            try:
                name = self.name_spec.normalise(meta.at(key), key)
            except BadSpec as error:
                errors.append(error)
            else:
                try:
                    normalised = self.value_spec.normalise(meta.at(key), value)
                except BadSpec as error:
                    errors.append(error)
                else:
                    result[name] = normalised

        if errors:
            raise BadSpecValue(meta=meta, _errors=errors)

        return result

class listof(Spec):
    def setup(self, spec, expect=NotSpecified):
        self.spec = spec
        self.expect = expect

    @property
    def default(self):
        return []

    def normalise_filled(self, meta, val):
        """Turn this into a list of it's not and normalise all the items in the list"""
        if self.expect is not NotSpecified and isinstance(val, self.expect):
            return [val]

        if not isinstance(val, list):
            val = [val]

        result = []
        errors = []
        for index, item in enumerate(val):
            if isinstance(item, self.expect):
                result.append((index, item))
            else:
                try:
                    result.append((index, self.spec.normalise(meta.indexed_at(index), item)))
                except BadSpec as error:
                    errors.append(error)

        if self.expect is not NotSpecified:
            for index, value in result:
                if not isinstance(value, self.expect):
                    errors.append(BadSpecValue("Expected normaliser to create a specific object", expected=self.expect, meta=meta.indexed_at(index), got=value))

        if errors:
            raise BadSpecValue(meta=meta, _errors=errors)

        return list(map(operator.itemgetter(1), result))

class set_options(Spec):
    def setup(self, **options):
        self.options = options

    @property
    def default(self):
        return {}

    def normalise_filled(self, meta, val):
        """Fill out a dictionary with what we want as well as the remaining extra"""
        if not isinstance(val, dict) and not isinstance(val, MergedOptions):
            raise BadSpecValue("Expected a dictionary", meta=meta, got=type(val))

        result = val
        errors = []

        for key, spec in self.options.items():
            val = result.get(key, NotSpecified)

            try:
                result[key] = spec.normalise(meta.at(key), val)
            except BadSpec as error:
                errors.append(error)

        if errors:
            raise BadSpecValue(meta=meta, _errors=errors)

        return result

class defaulted(Spec):
    def setup(self, spec, dflt):
        self.spec = spec
        self.default = dflt

    def normalise_filled(self, meta, val):
        """Proxy our spec"""
        return self.spec.normalise(meta, val)

class required(Spec):
    def setup(self, spec):
        self.spec = spec

    def normalise_empty(self, meta):
        """Complain that we have no value"""
        raise BadSpecValue("Expected a value but got none", meta=meta)

    def normalise_filled(self, meta, val):
        """Proxy our spec"""
        return self.spec.normalise(meta, val)

class boolean(Spec):
    def normalise_filled(self, meta, val):
        """Complain if not already a boolean"""
        if not isinstance(val, bool):
            raise BadSpecValue("Expected a boolean", meta=meta, got=type(val))
        else:
            return val

class directory_spec(Spec):
    def normalise_filled(self, meta, val):
        """Complain if not a meta to a directory"""
        if not isinstance(val, six.string_types):
            raise BadDirectory("Didn't even get a string", meta=meta, got=type(val))
        elif not os.path.exists(val):
            raise BadDirectory("Got something that didn't exist", meta=meta, directory=val)
        elif not os.path.isdir(val):
            raise BadDirectory("Got something that exists but isn't a directory", meta=meta, directory=val)
        else:
            return val

class filename_spec(Spec):
    def normalise_filled(self, meta, val):
        """Complain if not a meta to a filename"""
        if not isinstance(val, six.string_types):
            raise BadFilename("Didn't even get a string", meta=meta, got=type(val))
        elif not os.path.exists(val):
            raise BadFilename("Got something that didn't exist", meta=meta, filename=val)
        elif not os.path.isfile(val):
            raise BadFilename("Got something that exists but isn't a file", meta=meta, filename=val)
        else:
            return val

class string_spec(Spec):
    @property
    def default(self):
        return ""

    def normalise_filled(self, meta, val):
        """Make sure it's a string"""
        if not isinstance(val, six.string_types):
            raise BadSpecValue("Expected a string", meta=meta, got=type(val))

        return val

class valid_string_spec(string_spec):
    def setup(self, *validators):
        self.validators = validators

    def normalise_filled(self, meta, val):
        """Make sure if there is a value, that it is valid"""
        val = super(valid_string_spec, self).normalise_filled(meta, val)

        for validator in self.validators:
            val = validator.normalise(meta, val)

        return val

class string_choice_spec(string_spec):
    def setup(self, choices, reason=NotSpecified):
        self.choices = choices
        self.reason = reason
        if self.reason is NotSpecified:
            self.reason = "Expected one of the available choices"

    def normalise_filled(self, meta, val):
        """Complain if val isn't one of the available"""
        val = super(string_choice_spec, self).normalise_filled(meta, val)

        if val not in self.choices:
            raise BadSpecValue(self.reason, available=self.choices, got=val, meta=meta)

        return val

class create_spec(Spec):
    def setup(self, kls, **expected):
        self.kls = kls
        self.expected = expected
        self.expected_spec = set_options(**expected)

    def normalise_filled(self, meta, val):
        """If val is already our expected kls, return it, otherwise instantiate it"""
        if isinstance(val, self.kls):
            return val

        values = self.expected_spec.normalise(meta, val)
        result = dict((key, values[key]) for key in self.expected)
        return self.kls(**result)

class or_spec(Spec):
    def setup(self, *specs):
        self.specs = specs

    def normalise_filled(self, meta, val):
        """Try all the specs till one doesn't raise a BadSpec"""
        errors = []
        for spec in self.specs:
            try:
                return spec.normalise(meta, val)
            except BadSpec as error:
                errors.append(error)

        # If made it this far, none of the specs passed :(
        raise BadSpecValue("Value doesn't match any of the options", meta=meta, val=val,  _errors=errors)

class optional_spec(Spec):
    def setup(self, spec):
        self.spec = spec

    def normalise_empty(self, meta):
        """Just return NotSpecified"""
        return NotSpecified

    def normalise_filled(self, meta, val):
        """Proxy the spec"""
        return self.spec.normalise(meta, val)

class dict_from_bool_spec(Spec):
    def setup(self, dict_maker, spec):
        self.spec = spec
        self.dict_maker = dict_maker

    def normalise_empty(self, meta):
        """Use an empty dict with the spec if not specified"""
        return self.normalise_filled(meta, {})

    def normalise_filled(self, meta, val):
        """Proxy the spec"""
        if isinstance(val, bool):
            val = self.dict_maker(meta, val)
        return self.spec.normalise(meta, val)

