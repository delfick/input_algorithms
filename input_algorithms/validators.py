from input_algorithms.spec_base import Spec, NotSpecified
from input_algorithms.errors import BadSpecValue

import re

class Validator(Spec):
    def normalise_either(self, meta, val):
        if val is NotSpecified:
            return val
        else:
            return self.validate(meta, val)

class no_whitespace(Validator):
    def setup(self):
        self.regex = re.compile("\s+")

    def validate(self, meta, val):
        """Complain about whitespace"""
        if self.regex.search(val):
            raise BadSpecValue("Expected no whitespace", meta=meta, val=val)
        return val

class no_dots(Validator):
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

class regexed(Validator):
    def setup(self, *regexes):
        self.regexes = [(regex, re.compile(regex)) for regex in regexes]

    def validate(self, meta, val):
        """Complain if the value doesn't match the regex"""
        for spec, regex in self.regexes:
            if not regex.match(val):
                raise BadSpecValue("Expected value to match regex, it didn't", spec=spec, meta=meta, val=val)
        return val

class deprecated_key(Validator):
    def setup(self, key, reason):
        self.key = key
        self.reason = reason

    def validate(self, meta, val):
        """Complain if the key is in val"""
        if self.key in val:
            raise DeprecationWarning("The key {0} is deprecated: {1}".format(self.key, self.reason))

