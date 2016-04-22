"""
Validators are the same as any other subclass of
:class:`input_algorithms.spec_base.Spec` in that it has a ``normalise`` method
that takes in ``meta`` and ``val`` and returns a new ``val``.

It is convention that a validator subclasses ``input_algorithms.validators.Validator``
and implements a ``validate`` method. This means ``NotSpecified`` values are
ignored and any specified value goes through the ``validate`` method.

It is the job of the validator to raise a sublcass of ``input_algorithms.errors.BadSpec``
if something is wrong, otherwise just return ``val``.
"""
from input_algorithms.errors import BadSpecValue, DeprecatedKey
from input_algorithms.spec_base import Spec, NotSpecified

import re

default_validators = []

def register(func):
    """For the documentations!"""
    default_validators.append((func.__name__, func))
    return func

class Validator(Spec):
    """
    A specification that either returns ``NotSpecified`` if ``val`` is
    ``NotSpecified`` or simply calls ``self.validate``.

    ``validate``
        A method to do validation on a value. if the value is invalid, it is best
        to raise an instance of ``input_algorithms.errors.BadSpec``.
    """
    def validate(meta, val):
        raise NotImplementedError()

    def normalise_either(self, meta, val):
        if val is NotSpecified:
            return val
        else:
            return self.validate(meta, val)

@register
class has_either(Validator):
    """
    Usage
        .. code-block:: python

            has_either([key1, ..., keyn]).normalise(meta, val)

    Will complain if the ``val.get(key, NotSpecified)`` returns ``NotSpecified``
    for all the choices.

    I.e. A valid dictionary has either one of the specified keys!
    """
    def setup(self, choices):
        self.choices = choices

    def validate(self, meta, val):
        """Complain if we have none of the choices"""
        if all(val.get(key, NotSpecified) is NotSpecified for key in self.choices):
            raise BadSpecValue("Need to specify atleast one of the required keys", choices=self.choices, meta=meta)
        return val

@register
class no_whitespace(Validator):
    """
    Usage
        .. code-block:: python

            no_whitespace().normalise(meta, val)

    Raises an error if we can find the regex ``\s+`` in the ``val``.
    """
    def setup(self):
        self.regex = re.compile("\s+")

    def validate(self, meta, val):
        """Complain about whitespace"""
        if self.regex.search(val):
            raise BadSpecValue("Expected no whitespace", meta=meta, val=val)
        return val

@register
class no_dots(Validator):
    """
    Usage
        .. code-block:: python

            no_dots().normalise(meta, val)

            # or

            no_dots(reason="dots are evil!").normalise(meta, val)

    This will complain if ``val`` contains any dots

    It will use the ``reason`` to explain why it's an error if it's provided.
    """
    def setup(self, reason=None):
        self.reason = reason

    def validate(self, meta, val):
        """Complain about dots"""
        if '.' in val:
            reason = self.reason
            if not reason:
                reason = "Expected no dots"
            raise BadSpecValue(reason, meta=meta, val=val)
        return val

@register
class regexed(Validator):
    """
    Usage
        .. code-block:: python

            regexed(regex1, ..., regexn).normalise(meta, val)

    This will match the ``val`` against all the ``regex``s and will complain if
    any of them fail, otherwise the ``val`` is returned.
    """
    def setup(self, *regexes):
        self.regexes = [(regex, re.compile(regex)) for regex in regexes]

    def validate(self, meta, val):
        """Complain if the value doesn't match the regex"""
        for spec, regex in self.regexes:
            if not regex.match(val):
                raise BadSpecValue("Expected value to match regex, it didn't", spec=spec, meta=meta, val=val)
        return val

@register
class deprecated_key(Validator):
    """
    Usage
        .. code-block:: python

            deprecated_key(key, reason).normalise(meta, val)

    This will raise an error if ``val`` is nonempty and contains ``key``. The
    error will use ``reason`` in it's message.
    """
    def setup(self, key, reason):
        self.key = key
        self.reason = reason

    def validate(self, meta, val):
        """Complain if the key is in val"""
        if val and self.key in val:
            raise DeprecatedKey(key=self.key, reason=self.reason, meta=meta)

@register
class choice(Validator):
    """
    Usage
        .. code-block:: python

            choice(choice1, ..., choicen).normalise(meta, val)
    """
    def setup(self, *choices):
        self.choices = choices

    def validate(self, meta, val):
        """Complain if the key is not one of the correct choices"""
        if val not in self.choices:
            raise BadSpecValue("Expected the value to be one of the valid choices", got=val, choices=self.choices, meta=meta)
        return val

