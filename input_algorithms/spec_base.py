from input_algorithms.errors import BadSpec, BadSpecValue, BadDirectory, BadFilename

import operator
import six
import os

class NotSpecified(object):
    """Tell the difference between None and not specified"""

    def __repr__(self):
        return "<NotSpecified>"

def apply_validators(meta, val, validators, chain_value=True):
    errors = []
    for validator in validators:
        try:
            nxt = validator.normalise(meta, val)
            if chain_value:
                val = nxt
        except BadSpecValue as e:
            errors.append(e)

    if errors:
        raise BadSpecValue("Failed to validate", meta=meta, _errors=errors)

    return val

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
                return self.default(meta)
            else:
                return val
        elif hasattr(self, "normalise_filled"):
            return self.normalise_filled(meta, val)

        raise BadSpec("Spec doesn't know how to deal with this value", spec=self, meta=meta, val=val)

    def fake_filled(self, meta, with_non_defaulted=False):
        """Return this spec as if it was filled with the defaults"""
        if hasattr(self, "fake"):
            return self.fake(meta, with_non_defaulted=with_non_defaulted)
        if hasattr(self, "default"):
            return self.default(meta)
        return NotSpecified

class pass_through_spec(Spec):
    def normalise_either(self, meta, val):
        return val

class always_same_spec(Spec):
    def setup(self, result):
        self.result = result

    def normalise_either(self, meta, val):
        return self.result

class dictionary_spec(Spec):
    def default(self, meta):
        return {}

    def normalise_filled(self, meta, val):
        """Make sure it's a dictionary"""
        if not isinstance(val, dict) and not getattr(val, "is_dict", False):
            raise BadSpecValue("Expected a dictionary", meta=meta, got=type(val))

        return val

class dictof(dictionary_spec):
    def setup(self, name_spec, value_spec, nested=False):
        self.nested = nested
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
                    if self.nested and (isinstance(value, dict) or getattr(value, "is_dict", False)):
                        normalised = self.__class__(self.name_spec, self.value_spec, nested=self.nested).normalise(meta.at(key), value)
                    else:
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

    def default(self, meta):
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

    def default(self, meta):
        return {}

    def normalise_filled(self, meta, val):
        """Fill out a dictionary with what we want as well as the remaining extra"""
        if not isinstance(val, dict) and not getattr(val, "is_dict", False):
            raise BadSpecValue("Expected a dictionary", meta=meta, got=type(val))

        result = {}
        errors = []

        for key, spec in self.options.items():
            nxt = val.get(key, NotSpecified)

            try:
                normalised = spec.normalise(meta.at(key), nxt)
                result[key] = normalised
            except (BadSpec, BadSpecValue) as error:
                errors.append(error)

        if errors:
            raise BadSpecValue(meta=meta, _errors=errors)

        return result

    def fake(self, meta, with_non_defaulted=False):
        """Return a dict with the defaults from the keys that have them"""
        result = {}
        for key, spec in self.options.items():
            fake = spec.fake_filled(meta, with_non_defaulted=with_non_defaulted)
            if fake is not NotSpecified or with_non_defaulted:
                result[key] = fake
        return result

class defaulted(Spec):
    def setup(self, spec, dflt):
        self.spec = spec
        self.default = lambda m: dflt

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

    def fake(self, meta, with_non_defaulted=False):
        return self.spec.fake_filled(meta, with_non_defaulted=with_non_defaulted)

class boolean(Spec):
    def normalise_filled(self, meta, val):
        """Complain if not already a boolean"""
        if not isinstance(val, bool):
            raise BadSpecValue("Expected a boolean", meta=meta, got=type(val))
        else:
            return val

class directory_spec(Spec):
    def setup(self, spec=NotSpecified):
        self.spec = spec
        if self.spec is NotSpecified:
            self.spec = string_spec()

    def fake(self, meta, with_non_defaulted=False):
        return self.spec.fake_filled(meta, with_non_defaulted=with_non_defaulted)

    def normalise_either(self, meta, val):
        """Complain if not a meta to a directory"""
        if self.spec is not NotSpecified:
            val = self.spec.normalise(meta, val)

        if not isinstance(val, six.string_types):
            raise BadDirectory("Didn't even get a string", meta=meta, got=type(val))
        elif not os.path.exists(val):
            raise BadDirectory("Got something that didn't exist", meta=meta, directory=val)
        elif not os.path.isdir(val):
            raise BadDirectory("Got something that exists but isn't a directory", meta=meta, directory=val)
        else:
            return val

class filename_spec(Spec):
    def setup(self, may_not_exist=False):
        self.may_not_exist = may_not_exist

    def normalise_filled(self, meta, val):
        """Complain if not a meta to a filename"""
        if not isinstance(val, six.string_types):
            raise BadFilename("Didn't even get a string", meta=meta, got=type(val))

        if not os.path.exists(val):
            if self.may_not_exist:
                return val

            raise BadFilename("Got something that didn't exist", meta=meta, filename=val)

        if not os.path.isfile(val):
            raise BadFilename("Got something that exists but isn't a file", meta=meta, filename=val)

        return val

class file_spec(Spec):
    def normalise_filled(self, meta, val):
        """Complain if not a file object"""
        bad = False
        if six.PY2:
            if not isinstance(val, file):
                bad = True
        else:
            import io
            if not isinstance(val, io.TextIOBase):
                bad = True

        if bad:
            raise BadSpecValue("Didn't get a file object", meta=meta, got=val)
        return val

class string_spec(Spec):
    def default(self, meta):
        return ""

    def normalise_filled(self, meta, val):
        """Make sure it's a string"""
        if not isinstance(val, six.string_types):
            raise BadSpecValue("Expected a string", meta=meta, got=type(val))

        return val

class integer_spec(Spec):
    def normalise_filled(self, meta, val):
        """Make sure it's an integer and convert into one if it's a string"""
        if not isinstance(val, bool) and (isinstance(val, int) or hasattr(val, "isdigit") and val.isdigit()):
            return int(val)
        raise BadSpecValue("Expected an integer", meta=meta, got=type(val))

class float_spec(Spec):
    def normalise_filled(self, meta, val):
        """Make sure it's a float"""
        try:
            if not isinstance(val, bool):
                return float(val)
            else:
                raise BadSpecValue("Expected a float", meta=meta, got=bool)
        except (TypeError, ValueError) as error:
            raise BadSpecValue("Expected a float", meta=meta, got=type(val), error=error)

class string_or_int_as_string_spec(Spec):
    def default(self, meta):
        return ""

    def normalise_filled(self, meta, val):
        """Make sure it's a string or integer"""
        if isinstance(val, bool) or (not isinstance(val, six.string_types) and not isinstance(val, six.integer_types)):
            raise BadSpecValue("Expected a string or integer", meta=meta, got=type(val))
        return str(val)

class valid_string_spec(string_spec):
    def setup(self, *validators):
        self.validators = validators

    def normalise_filled(self, meta, val):
        """Make sure if there is a value, that it is valid"""
        val = super(valid_string_spec, self).normalise_filled(meta, val)
        return apply_validators(meta, val, self.validators)

class integer_choice_spec(integer_spec):
    def setup(self, choices, reason=NotSpecified):
        self.choices = choices
        self.reason = reason
        if self.reason is NotSpecified:
            self.reason = "Expected one of the available choices"

    def normalise_filled(self, meta, val):
        """Complain if val isn't one of the available"""
        val = super(integer_choice_spec, self).normalise_filled(meta, val)

        if val not in self.choices:
            raise BadSpecValue(self.reason, available=self.choices, got=val, meta=meta)

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
    def setup(self, kls, *validators, **expected):
        self.kls = kls
        self.expected = expected
        self.validators = validators
        self.expected_spec = set_options(**expected)

    def default(self, meta):
        return self.kls(**self.expected_spec.normalise(meta, {}))

    def fake(self, meta, with_non_defaulted=False):
        return self.kls(**self.expected_spec.fake_filled(meta, with_non_defaulted=with_non_defaulted))

    def normalise_filled(self, meta, val):
        """If val is already our expected kls, return it, otherwise instantiate it"""
        if isinstance(val, self.kls):
            return val

        apply_validators(meta, val, self.validators, chain_value=False)
        values = self.expected_spec.normalise(meta, val)
        result = getattr(meta, 'base', {})
        for key in self.expected:
            result[key] = None
            result[key] = values.get(key, NotSpecified)
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
        raise BadSpecValue("Value doesn't match any of the options", meta=meta, val=val, _errors=errors)

class match_spec(Spec):
    def setup(self, *specs, **kwargs):
        self.specs = specs
        self.fallback = kwargs.get("fallback")

    def normalise_filled(self, meta, val):
        """Try the specs given the type of val"""
        for expected_typ, spec in self.specs:
            if isinstance(val, expected_typ):
                return spec.normalise(meta, val)

        if self.fallback is not None:
            return self.fallback.normalise(meta, val)

        # If made it this far, none of the specs matched
        raise BadSpecValue("Value doesn't match any of the options", meta=meta, got=type(val), expected=[expected_typ for expected_typ, _ in self.specs])

class and_spec(Spec):
    def setup(self, *specs):
        self.specs = specs

    def normalise_filled(self, meta, val):
        """Try all the specs"""
        errors = []
        transformations = [val]
        for spec in self.specs:
            try:
                val = spec.normalise(meta, val)
                transformations.append(val)
            except BadSpec as error:
                errors.append(error)
                break

        if errors:
            raise BadSpecValue("Value didn't match one of the options", meta=meta, transformations=transformations, _errors=errors)
        else:
            return val

class optional_spec(Spec):
    def setup(self, spec):
        self.spec = spec

    def fake(self, meta, with_non_defaulted=False):
        return self.spec.fake_filled(meta, with_non_defaulted=with_non_defaulted)

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

    def fake(self, meta, with_non_defaulted=False):
        return self.spec.fake_filled(meta, with_non_defaulted=with_non_defaulted)

    def normalise_filled(self, meta, val):
        """Proxy the spec"""
        if isinstance(val, bool):
            val = self.dict_maker(meta, val)
        return self.spec.normalise(meta, val)

class formatted(Spec):
    def setup(self, spec, formatter, expected_type=NotSpecified):
        self.spec = spec
        self.formatter = formatter
        self.expected_type = expected_type
        self.has_expected_type = self.expected_type and self.expected_type is not NotSpecified

    def fake(self, meta, with_non_defaulted=False):
        if with_non_defaulted:
            return self.normalise_either(meta, NotSpecified)
        else:
            return NotSpecified

    def normalise_either(self, meta, val):
        """Format the value"""
        options_opts = {}
        if hasattr(meta.everything, "converters"):
            options_opts['converters'] = meta.everything.converters
        if hasattr(meta.everything, "dont_prefix"):
            options_opts["dont_prefix"] = meta.everything.dont_prefix
        options = meta.everything.__class__(**options_opts)
        options.update(meta.key_names())
        options.update(meta.everything)

        specd = self.spec.normalise(meta, val)
        formatted = self.formatter(options, meta.path, value=specd).format()

        if self.has_expected_type:
            if not isinstance(formatted, self.expected_type):
                raise BadSpecValue("Expected a different type", got=type(formatted), expected=self.expected_type)

        return formatted

class many_format(Spec):
    def setup(self, spec, formatter, expected_type=NotSpecified):
        self.spec = spec
        self.formatter = formatter
        self.expected_type = expected_type

    def fake(self, meta, with_non_defaulted=False):
        return self.spec.fake_filled(meta, with_non_defaulted=with_non_defaulted)

    def normalise_either(self, meta, val):
        """Format the formatted spec"""
        val = self.spec.normalise(meta, val)
        done = []

        while True:
            fm = formatted(string_spec(), formatter=self.formatter, expected_type=six.string_types)
            normalised = fm.normalise(meta, val)
            if normalised == val:
                break

            if normalised in done:
                done.append(normalised)
                raise BadSpecValue("Recursive formatting", done=done, meta=meta)
            else:
                done.append(normalised)
                val = normalised

        return formatted(string_spec(), formatter=self.formatter, expected_type=self.expected_type).normalise(meta, "{{{0}}}".format(val))

class overridden(Spec):
    def setup(self, value):
        self.value = value

    def normalise(self, meta, val):
        return self.value

    def default(self, meta):
        return self.value

class any_spec(Spec):
    def normalise(self, meta, val):
        return val

class container_spec(Spec):
    def setup(self, kls, spec):
        self.kls = kls
        self.spec = spec

    def fake(self, meta, with_non_defaulted=False):
        return self.kls(self.spec.fake_filled(meta, with_non_defaulted=with_non_defaulted))

    def normalise_either(self, meta, val):
        return self.kls(self.spec.normalise(meta, val))

class delayed(Spec):
    def setup(self, spec):
        self.spec = spec

    def normalise_either(self, meta, val):
        return lambda: self.spec.normalise(meta, val)

    def fake(self, meta, with_non_defaulted=False):
        return lambda: self.spec.fake_filled(meta, with_non_defaulted=with_non_defaulted)

