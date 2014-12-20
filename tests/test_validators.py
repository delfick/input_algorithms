# coding: spec

from input_algorithms.errors import BadSpec, BadSpecValue, DeprecatedKey
from input_algorithms.spec_base import Spec, NotSpecified
from input_algorithms.validators import Validator
from input_algorithms import validators as va

from tests.helpers import TestCase

from noseOfYeti.tokeniser.support import noy_sup_setUp
import mock

describe TestCase, "Validator":
    before_each:
        self.val = mock.Mock(name="val")
        self.meta = mock.Mock(name="meta")

    it "is a subclass of Spec":
        assert issubclass(Validator, Spec)

    it "returns NotSpecified if not specified":
        self.assertIs(Validator().normalise(self.meta, NotSpecified), NotSpecified)

    it "uses validate if value is specified":
        result = mock.Mock(name="result")
        validate = mock.Mock(name="validate")
        validate.return_value = result

        validator = type("Validator", (Validator, ), {"validate": validate})()
        self.assertIs(validator.normalise(self.meta, self.val), result)
        validate.assert_called_once_with(self.meta, self.val)

describe TestCase, "no_whitesapce":
    before_each:
        self.meta = mock.Mock(name="meta")

    it "Sets up a whitespace regex":
        fake_compile = mock.Mock(name="fake_compile")
        compiled_regex = mock.Mock(name="compiled_regex")

        with mock.patch("re.compile", fake_compile):
            fake_compile.return_value = compiled_regex
            validator = va.no_whitespace()
            self.assertIs(validator.regex, compiled_regex)

        fake_compile.assert_called_once_with("\s+")

    it "has a regex that finds whitespace":
        validator = va.no_whitespace()
        assert validator.regex.search("  \t\n")
        assert validator.regex.search("\t\n")
        assert validator.regex.search("\n")
        assert validator.regex.search("\n ")
        assert not validator.regex.match("d")

    it "complains if the value has whitespace":
        val = "adf "
        with self.fuzzyAssertRaisesError(BadSpecValue, "Expected no whitespace", meta=self.meta, val=val):
            va.no_whitespace().normalise(self.meta, val)

    it "lets through values that don't have whitespace":
        self.assertEqual(va.no_whitespace().normalise(self.meta, "asdf"), "asdf")

describe TestCase, "no_dots":
    before_each:
        self.meta = mock.Mock(name="meta")

    it "takes in a reason":
        reason = mock.Mock(name="reason")
        self.assertIs(va.no_dots().reason, None)
        self.assertIs(va.no_dots(reason=reason).reason, reason)

    it "lets the value through if it has no dot":
        val = "no dots here"
        self.assertEqual(va.no_dots().normalise(self.meta, val), val)

    describe "When there is a dot":
        it "uses the provided reason when complaining":
            val = "a.dot.in.this.one"
            reason = mock.Mock(name="reason")
            with self.fuzzyAssertRaisesError(BadSpecValue, reason, meta=self.meta, val=val):
                va.no_dots(reason).normalise(self.meta, val)

        it "defaults the reason when no reason is provided":
            val = "a.dot"
            with self.fuzzyAssertRaisesError(BadSpecValue, "Expected no dots", meta=self.meta, val=val):
                va.no_dots().normalise(self.meta, val)

describe TestCase, "regexed":
    before_each:
        self.meta = mock.Mock(name="meta")

    it "takes in regexes which it will compile":
        regex1 = mock.Mock(name="regex1")
        regex2 = mock.Mock(name="regex2")
        regex3 = mock.Mock(name="regex3")
        regex4 = mock.Mock(name="regex4")
        compiled_regex1 = mock.Mock(name="compiled_regex1")
        compiled_regex2 = mock.Mock(name="compiled_regex2")
        compiled_regex3 = mock.Mock(name="compiled_regex3")
        compiled_regex4 = mock.Mock(name="compiled_regex4")

        matched = {
              regex1: compiled_regex1, regex2: compiled_regex2
            , regex3: compiled_regex3, regex4: compiled_regex4
            }

        fake_compile = mock.Mock(name="compile")
        fake_compile.side_effect = lambda reg: matched[reg]
        with mock.patch("re.compile", fake_compile):
            validator = va.regexed(regex1, regex2, regex3, regex4)
            self.assertEqual(
                  validator.regexes
                , [ (regex1, compiled_regex1)
                  , (regex2, compiled_regex2)
                  , (regex3, compiled_regex3)
                  , (regex4, compiled_regex4)
                  ]
                )

    it "returns the value if it matches all the regexes":
        self.assertEqual(va.regexed("[a-z]+", "asdf", "a.+").normalise(self.meta, "asdf"), "asdf")

    it "complains if the value doesn't match any of the regexes":
        val = "meh"
        with self.fuzzyAssertRaisesError(BadSpecValue, "Expected value to match regex, it didn't", spec="blah", meta=self.meta, val=val):
            va.regexed("meh", "m.+", "blah", "other").normalise(self.meta, val)

describe TestCase, "deprecated_key":
    before_each:
        self.meta = mock.Mock(name="meta")

    it "takes in key and a reason":
        key = mock.Mock(name="key")
        reason = mock.Mock(name="reason")
        dk = va.deprecated_key(key, reason)
        self.assertIs(dk.key, key)
        self.assertIs(dk.reason, reason)

    it "complains if the key is in the value":
        key = mock.Mock(name="key")
        reason = mock.Mock(name="reason")
        with self.fuzzyAssertRaisesError(DeprecatedKey, key=key, reason=reason):
            va.deprecated_key(key, reason).normalise(self.meta, {key: 1})

    it "doesn't complain if the key is not in the value":
        key = mock.Mock(name="key")
        reason = mock.Mock(name="reason")
        va.deprecated_key(key, reason).normalise(self.meta, {})
        assert True

    it "doesn't fail if the val is not iterable":
        key = mock.Mock(name="key")
        reason = mock.Mock(name="reason")
        va.deprecated_key(key, reason).normalise(self.meta, None)
        assert True

