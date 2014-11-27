# coding: spec

from input_algorithms.spec_base import Spec, NotSpecified, pass_through_spec, always_same_spec
from input_algorithms.errors import BadSpec, BadSpecValue, BadDirectory, BadFilename
from input_algorithms import spec_base as sb
from input_algorithms.meta import Meta

from tests.helpers import TestCase

from noseOfYeti.tokeniser.support import noy_sup_setUp
from namedlist import namedlist
import mock
import six

describe TestCase, "Spec":
    it "takes in positional arguments and keyword arguments":
        m1 = mock.Mock("m1")
        m2 = mock.Mock("m2")
        m3 = mock.Mock("m3")
        m4 = mock.Mock("m4")
        spec = Spec(m1, m2, a=m3, b=m4)
        self.assertEqual(spec.pargs, (m1, m2))
        self.assertEqual(spec.kwargs, dict(a=m3, b=m4))

    it "calls setup if one is defined":
        called = []
        m1 = mock.Mock("m1")
        m2 = mock.Mock("m2")
        m3 = mock.Mock("m3")
        m4 = mock.Mock("m4")
        class Specd(Spec):
            def setup(sp, *pargs, **kwargs):
                self.assertEqual(pargs, (m1, m2))
                self.assertEqual(sp.pargs, (m1, m2))

                self.assertEqual(kwargs, dict(a=m3, b=m4))
                self.assertEqual(sp.kwargs, dict(a=m3, b=m4))
                called.append(sp)

        spec = Specd(m1, m2, a=m3, b=m4)
        self.assertEqual(called, [spec])

    describe "normalise":
        describe "When normalise_either is defined":
            it "uses it's value if it returns a non NotSpecified value":
                val = mock.Mock(name="val")
                meta = mock.Mock(name="meta")
                result = mock.Mock(name="result")
                normalise_either = mock.Mock(name="normalise_either", return_value=result)

                Specd = type("Specd", (Spec, ), {"normalise_either": normalise_either})
                self.assertIs(Specd().normalise(meta, val), result)
                normalise_either.assert_called_once_with(meta, val)

        describe "When normalise_either returns NotSpecified":

            it "uses normalise_filled if the value is not NotSpecified":
                val = mock.Mock(name="val")
                meta = mock.Mock(name="meta")
                result = mock.Mock(name="result")
                normalise_either = mock.Mock(name="normalise_either", return_value=NotSpecified)
                normalise_filled = mock.Mock(name="normalise_either", return_value=result)

                Specd = type("Specd", (Spec, ), {"normalise_either": normalise_either, "normalise_filled": normalise_filled})
                self.assertIs(Specd().normalise(meta, val), result)
                normalise_either.assert_called_once_with(meta, val)
                normalise_filled.assert_called_once_with(meta, val)

            it "uses normalise_empty if val is NotSpecified":
                val = NotSpecified
                meta = mock.Mock(name="meta")
                result = mock.Mock(name="result")
                normalise_either = mock.Mock(name="normalise_either", return_value=NotSpecified)
                normalise_empty = mock.Mock(name="normalise_empty", return_value=result)

                Specd = type("Specd", (Spec, ), {"normalise_either": normalise_either, "normalise_empty": normalise_empty})
                self.assertIs(Specd().normalise(meta, val), result)
                normalise_either.assert_called_once_with(meta, val)
                normalise_empty.assert_called_once_with(meta)

        describe "When no normalise_either":
            describe "When value is NotSpecified":
                it "Uses normalise_empty if defined":
                    val = NotSpecified
                    meta = mock.Mock(name="meta")
                    result = mock.Mock(name="result")
                    normalise_empty = mock.Mock(name="normalise_empty", return_value=result)

                    Specd = type("Specd", (Spec, ), {"normalise_empty": normalise_empty})
                    self.assertIs(Specd().normalise(meta, val), result)
                    normalise_empty.assert_called_once_with(meta)

                it "uses default if defined and no normalise_empty":
                    val = NotSpecified
                    meta = mock.Mock(name="meta")
                    default = mock.Mock(name="default")
                    default_method = mock.Mock(name="default_method", return_value=default)

                    Specd = type("Specd", (Spec, ), {"default": default_method})
                    self.assertIs(Specd().normalise(meta, val), default)
                    default_method.assert_called_once_with(meta)

                it "returns NotSpecified otherwise":
                    val = NotSpecified
                    meta = mock.Mock(name="meta")
                    Specd = type("Specd", (Spec, ), {})
                    self.assertIs(Specd().normalise(meta, val), NotSpecified)

            describe "When value is not NotSpecified":
                it "Uses normalise_filled if defined":
                    val = mock.Mock(name="val")
                    meta = mock.Mock(name="meta")
                    result = mock.Mock(name="result")
                    normalise_filled = mock.Mock(name="normalise_filled", return_value=result)

                    Specd = type("Specd", (Spec, ), {"normalise_filled": normalise_filled})
                    self.assertIs(Specd().normalise(meta, val), result)
                    normalise_filled.assert_called_once_with(meta, val)

                it "complains if no normalise_filled":
                    val = mock.Mock(name="val")
                    meta = mock.Mock(name="meta")
                    Specd = type("Specd", (Spec, ), {})
                    with self.fuzzyAssertRaisesError(BadSpec, "Spec doesn't know how to deal with this value", meta=meta, val=val):
                        Specd().normalise(meta, val)

describe TestCase, "pass_through_spec":
    it "just returns whatever it is given":
        val = mock.Mock(name="val")
        meta = mock.Mock(name="meta")

        spec = pass_through_spec()
        self.assertIs(spec.normalise(meta, val), val)
        self.assertIs(spec.normalise(meta, NotSpecified), NotSpecified)

describe TestCase, "dictionary specs":
    __only_run_tests_in_children__ = True

    def make_spec(self):
        raise NotImplementedError()

    before_each:
        self.meta = mock.Mock(name="meta")

    it "has a default value of an empty dictionary":
        self.assertEqual(self.make_spec().default(self.meta), {})

    it "complains if the value being normalised is not a dict":
        meta = mock.Mock(name="meta")
        for opt in (0, 1, True, False, [], [1], lambda: 1, "", "asdf", type("blah", (object, ), {})()):
            with self.fuzzyAssertRaisesError(BadSpecValue, "Expected a dictionary", meta=meta, got=type(opt)):
                self.make_spec().normalise(meta, opt)

    it "works with a dict":
        meta = mock.Mock(name="meta")
        dictoptions = {"a": 1, "b": 2}
        self.assertEqual(self.make_spec().normalise(meta, dictoptions), dictoptions)

    describe "dictionary_spec":
        make_spec = sb.dictionary_spec

    describe "dictof":

        def make_spec(self, name_spec=NotSpecified, value_spec=NotSpecified):
            name_spec = pass_through_spec() if name_spec is NotSpecified else name_spec
            value_spec = pass_through_spec() if value_spec is NotSpecified else value_spec
            return sb.dictof(name_spec, value_spec)

        it "takes in a name_spec and a value_spec":
            name_spec = mock.Mock(name="name_spec")
            value_spec = mock.Mock(name="value_spec")
            do = sb.dictof(name_spec, value_spec)
            self.assertEqual(do.name_spec, name_spec)
            self.assertEqual(do.value_spec, value_spec)

        it "complains if a key doesn't match the name_spec":
            meta = mock.Mock(name="meta")
            at_one = mock.Mock(name="at_one")
            at_two = mock.Mock(name="at_two")
            at_three = mock.Mock(name="at_three")
            def at(val):
                if val == "one":
                    return at_one
                elif val == "two":
                    return at_two
                elif val == "three":
                    return at_three
                else:
                    assert False, "Unexpected value into at: {0}".format(val)
            meta.at.side_effect = at

            name_spec = mock.Mock(name="name_spec")
            error_one = BadSpecValue("one")
            error_three = BadSpecValue("three")
            def normalise(meta, val):
                if val == "one":
                    raise error_one
                elif val == "three":
                    raise error_three
                else:
                    return val
            name_spec.normalise.side_effect = normalise

            spec = self.make_spec(name_spec=name_spec)
            with self.fuzzyAssertRaisesError(BadSpecValue, meta=meta, _errors=[error_one, error_three]):
                spec.normalise(meta, {"one": 1, "two": 2, "three": 3})

        it "complains if a value doesn't match the value_spec":
            meta = mock.Mock(name="meta")
            value_spec = mock.Mock(name="value_spec")
            error_two = BadSpecValue("two")
            error_four = BadSpecValue("four")
            def normalise(meta, val):
                if val == 2:
                    raise error_two
                elif val == 4:
                    raise error_four
                else:
                    return val
            value_spec.normalise.side_effect = normalise

            spec = self.make_spec(value_spec=value_spec)
            with self.fuzzyAssertRaisesError(BadSpecValue, meta=meta, _errors=[error_two, error_four]):
                spec.normalise(meta, {"one": 1, "two": 2, "three": 3, "four": 4})

describe TestCase, "listof":
    before_each:
        self.meta = mock.Mock(name="meta", spec_set=Meta)
        self.spec = pass_through_spec()
        self.lo = sb.listof(self.spec)

    it "takes in a spec and possible expect":
        spec = mock.Mock(name="spec")
        expect = mock.Mock(name="expect")
        lo = sb.listof(spec, expect=expect)
        self.assertEqual(lo.spec, spec)
        self.assertEqual(lo.expect, expect)

        lo = sb.listof(spec)
        self.assertEqual(lo.spec, spec)
        self.assertEqual(lo.expect, NotSpecified)

    it "has a default value of an empty list":
        self.assertEqual(self.lo.default(self.meta), [])

    it "turns the value into a list if not already a list":
        for opt in (0, 1, True, False, {}, {1:1}, lambda: 1, "", "asdf", type("blah", (object, ), {})()):
            self.assertEqual(self.lo.normalise(self.meta, opt), [opt])

    it "doesn't turn a list into a list of itself":
        self.assertEqual(self.lo.normalise(self.meta, []), [])
        self.assertEqual(self.lo.normalise(self.meta, [1, 2]), [1, 2])

    it "returns the value if already the type specified by expect":
        class Value(object): pass
        val = Value()
        self.assertEqual(sb.listof(self.spec, expect=Value).normalise(self.meta, val), [val])

    it "only normalises values not already the expected type":
        class Value(object): pass
        val_same = Value()
        spec = always_same_spec(val_same)
        proxied_spec = mock.Mock(name="spec", spec_set=["normalise"])
        proxied_spec.normalise.side_effect = spec.normalise

        indexed_one = mock.Mock(name="indexed_one")
        indexed_three = mock.Mock(name="indexed_three")
        def indexed_at(val):
            if val == 1:
                return indexed_one
            elif val == 3:
                return indexed_three
            else:
                assert False, "Unexpected value into indexed_at: {0}".format(val)
        self.meta.indexed_at.side_effect = indexed_at

        val1 = Value()
        val2 = Value()
        result = sb.listof(proxied_spec, expect=Value).normalise(self.meta, [val1, "stuff", val2, "blah"])
        self.assertEqual(proxied_spec.normalise.mock_calls, [mock.call(indexed_one, "stuff"), mock.call(indexed_three, "blah")])
        self.assertEqual(result, [val1, val_same, val2, val_same])

    it "complains about values that don't match the spec":
        meta = mock.Mock(name="meta")
        spec = mock.Mock(name="spec")
        error_two = BadSpecValue("two")
        error_four = BadSpecValue("four")
        def normalise(meta, val):
            if val == 2:
                raise error_two
            elif val == 4:
                raise error_four
            else:
                return val
        spec.normalise.side_effect = normalise

        self.lo.spec = spec
        with self.fuzzyAssertRaisesError(BadSpecValue, meta=meta, _errors=[error_two, error_four]):
            self.lo.normalise(meta, [1, 2, 3, 4])

    it "complains about values that aren't instances of expect":
        spec = mock.Mock(name="spec")
        meta_indexed_0 = mock.Mock(name="meta_indexed_0")
        meta_indexed_1 = mock.Mock(name="meta_indexed_1")
        meta_indexed_2 = mock.Mock(name="meta_indexed_2")
        meta_indexed_3 = mock.Mock(name="meta_indexed_3")

        def indexed_at(val):
            if val == 0:
                return meta_indexed_0
            elif val == 1:
                return meta_indexed_1
            elif val == 2:
                return meta_indexed_2
            elif val == 3:
                return meta_indexed_3
            else:
                assert False, "Don't expect indexed_at with value {0}".format(val)
        self.meta.indexed_at.side_effect = indexed_at

        class Value(object): pass
        class Other(object):
            def __eq__(self, other):
                return False
            def __lt__(self, other):
                return False

        other_2 = Other()
        other_4 = Other()
        error_two = BadSpecValue("Expected normaliser to create a specific object", expected=Value, meta=meta_indexed_1, got=other_2)
        error_four = BadSpecValue("Expected normaliser to create a specific object", expected=Value, meta=meta_indexed_3, got=other_4)

        def normalise(meta, val):
            if val == 2:
                return other_2
            elif val == 4:
                return other_4
            else:
                return Value()
        spec.normalise.side_effect = normalise

        self.lo.spec = spec
        self.lo.expect = Value
        with self.fuzzyAssertRaisesError(BadSpecValue, meta=self.meta, _errors=[error_two, error_four]):
            self.lo.normalise(self.meta, [1, 2, 3, 4])

describe TestCase, "set_options":
    before_each:
        self.meta = mock.Mock(name="meta", spec_set=Meta)
        self.so = sb.set_options()

    it "takes in the options":
        m1 = mock.Mock("m1")
        m2 = mock.Mock("m2")
        spec = sb.set_options(a=m1, b=m2)
        self.assertEqual(spec.options, dict(a=m1, b=m2))

    it "defaults to an empty dictionary":
        self.assertEqual(self.so.default(self.meta), {})

    it "complains if the value being normalised is not a dict":
        meta = mock.Mock(name="meta")
        for opt in (0, 1, True, False, [], [1], lambda: 1, "", "asdf", type("blah", (object, ), {})()):
            with self.fuzzyAssertRaisesError(BadSpecValue, "Expected a dictionary", meta=meta, got=type(opt)):
                self.so.normalise(meta, opt)

    it "Ignores options that aren't specified":
        meta = mock.Mock(name="meta")
        dictoptions = {"a": "1", "b": "2"}
        self.assertEqual(self.so.normalise(meta, dictoptions), {})

        self.so.options = {"a": sb.string_spec()}
        self.assertEqual(self.so.normalise(meta, dictoptions), {"a": "1"})

        self.so.options = {"a": sb.string_spec(), "b": sb.string_spec()}
        self.assertEqual(self.so.normalise(meta, dictoptions), {"a": "1", "b": "2"})

    it "checks the value of our known options":
        one_spec_result = mock.Mock(name="one_spec_result")
        one_spec = mock.Mock(name="one_spec", spec_set=["normalise"])
        one_spec.normalise.return_value = one_spec_result

        two_spec_result = mock.Mock(name="two_spec_result")
        two_spec = mock.Mock(name="two_spec", spec_set=["normalise"])
        two_spec.normalise.return_value = two_spec_result

        self.so.options = {"one": one_spec, "two": two_spec}
        self.assertEqual(self.so.normalise(self.meta, {"one": 1, "two": 2}), {"one": one_spec_result, "two": two_spec_result})

    it "collects errors":
        one_spec_error = BadSpecValue("Bad one")
        one_spec = mock.Mock(name="one_spec", spec_set=["normalise"])
        one_spec.normalise.side_effect = one_spec_error

        two_spec_error = BadSpecValue("Bad two")
        two_spec = mock.Mock(name="two_spec", spec_set=["normalise"])
        two_spec.normalise.side_effect = two_spec_error

        self.so.options = {"one": one_spec, "two": two_spec}
        with self.fuzzyAssertRaisesError(BadSpecValue, meta=self.meta, _errors=[one_spec_error, two_spec_error]):
            self.so.normalise(self.meta, {"one": 1, "two": 2, "three": 3})

describe TestCase, "defaulted":
    before_each:
        self.meta = mock.Mock(name="meta", spec_set=Meta)
        self.spec = mock.Mock(name="spec", spec_set=["normalise"])
        self.dflt = mock.Mock(name="dflt")
        self.dfltd = sb.defaulted(self.spec, self.dflt)

    it "takes in a spec and a default":
        dflt = mock.Mock(name="dflt")
        spec = mock.Mock(name="spec")
        dfltd = sb.defaulted(spec, dflt)
        self.assertEqual(dfltd.spec, spec)
        self.assertEqual(dfltd.default(self.meta), dflt)

    it "defaults to the dflt":
        self.assertIs(self.dfltd.default(self.meta), self.dflt)
        self.assertIs(self.dfltd.normalise(self.meta, NotSpecified), self.dflt)

    it "proxies the spec if a value is provided":
        val = mock.Mock(name="val")
        result = mock.Mock(name="result")
        self.spec.normalise.return_value = result
        self.assertIs(self.dfltd.normalise(self.meta, val), result)
        self.spec.normalise.assert_called_once_with(self.meta, val)

describe TestCase, "required":
    before_each:
        self.meta = mock.Mock(name="meta", spec_set=Meta)
        self.spec = mock.Mock(name="spec", spec_set=["normalise"])
        self.rqrd = sb.required(self.spec)

    it "takes in a spec":
        spec = mock.Mock(name="spec")
        rqrd = sb.required(spec)
        self.assertEqual(rqrd.spec, spec)

    it "Complains if there is no value":
        with self.fuzzyAssertRaisesError(BadSpecValue, "Expected a value but got none", meta=self.meta):
            self.rqrd.normalise(self.meta, NotSpecified)

    it "proxies the spec if a value is provided":
        val = mock.Mock(name="val")
        result = mock.Mock(name="result")
        self.spec.normalise.return_value = result
        self.assertIs(self.rqrd.normalise(self.meta, val), result)
        self.spec.normalise.assert_called_once_with(self.meta, val)

describe TestCase, "boolean":
    before_each:
        self.meta = mock.Mock(name="meta", spec_set=Meta)

    it "complains if the value is not a boolean":
        for opt in (0, 1, {}, {1:1}, [], [1], lambda: 1, "", "asdf", type("blah", (object, ), {})()):
            with self.fuzzyAssertRaisesError(BadSpecValue, "Expected a boolean", meta=self.meta, got=type(opt)):
                sb.boolean().normalise(self.meta, opt)

    it "returns value as is if a boolean":
        self.assertIs(sb.boolean().normalise(self.meta, True), True)
        self.assertIs(sb.boolean().normalise(self.meta, False), False)

describe TestCase, "directory_spec":
    before_each:
        self.meta = mock.Mock(name="meta", spec_set=Meta)

    it "complains if the value is not a string":
        for opt in (0, 1, True, False, {}, {1:1}, [], [1], lambda: 1, type("blah", (object, ), {})()):
            with self.fuzzyAssertRaisesError(BadDirectory, "Didn't even get a string", meta=self.meta, got=type(opt)):
                sb.directory_spec().normalise(self.meta, opt)

    it "complains if the meta doesn't exist":
        with self.a_temp_dir(removed=True) as directory:
            with self.fuzzyAssertRaisesError(BadDirectory, "Got something that didn't exist", meta=self.meta, directory=directory):
                sb.directory_spec().normalise(self.meta, directory)

    it "complains if the meta isn't a directory":
        with self.a_temp_file() as filename:
            with self.fuzzyAssertRaisesError(BadDirectory, "Got something that exists but isn't a directory", meta=self.meta, directory=filename):
                sb.directory_spec().normalise(self.meta, filename)

    it "returns directory as is if is a directory":
        with self.a_temp_dir() as directory:
            self.assertEqual(sb.directory_spec().normalise(self.meta, directory), directory)

describe TestCase, "filename_spec":
    before_each:
        self.meta = mock.Mock(name="meta", spec_set=Meta)

    it "complains if the value is not a string":
        for opt in (0, 1, True, False, {}, {1:1}, [], [1], lambda: 1, type("blah", (object, ), {})()):
            with self.fuzzyAssertRaisesError(BadFilename, "Didn't even get a string", meta=self.meta, got=type(opt)):
                sb.filename_spec().normalise(self.meta, opt)

    it "complains if the meta doesn't exist":
        with self.a_temp_file(removed=True) as filename:
            with self.fuzzyAssertRaisesError(BadFilename, "Got something that didn't exist", meta=self.meta, filename=filename):
                sb.filename_spec().normalise(self.meta, filename)

    it "complains if the meta isn't a file":
        with self.a_temp_dir() as directory:
            with self.fuzzyAssertRaisesError(BadFilename, "Got something that exists but isn't a file", meta=self.meta, filename=directory):
                sb.filename_spec().normalise(self.meta, directory)

    it "returns filename as is if is a filename":
        with self.a_temp_file() as filename:
            self.assertEqual(sb.filename_spec().normalise(self.meta, filename), filename)

describe TestCase, "string_specs":
    __only_run_tests_in_children__ = True

    before_each:
        self.meta = mock.Mock(name="meta", spec_set=Meta)

    def make_spec(self):
        raise NotImplementedError()

    it "defaults to an empty string":
        self.assertEqual(sb.string_spec().default(self.meta), "")

    it "complains if the value isn't a string":
        for opt in (0, 1, True, False, {}, {1:1}, [], [1], lambda: 1, type("blah", (object, ), {})()):
            with self.fuzzyAssertRaisesError(BadSpecValue, "Expected a string", meta=self.meta, got=type(opt)):
                self.make_spec().normalise(self.meta, opt)

    it "returns string as is if it is a string":
        for opt in ("", "asdf", u"adsf"):
            self.assertEqual(self.make_spec().normalise(self.meta, opt), opt)

    describe "string_spec":
        make_spec = sb.string_spec

    describe "valid_string_spec":
        make_spec = sb.valid_string_spec

        it "takes in a list of validators":
            validator1 = mock.Mock(name="validator1")
            validator2 = mock.Mock(name="validator2")
            spec = self.make_spec(validator1, validator2)
            self.assertEqual(spec.validators, (validator1, validator2))

        it "uses each validator to get the final value":
            result1 = mock.Mock(name="result1")
            result2 = mock.Mock(name="result2")

            validator1 = mock.Mock(name="validator1", spec_set=["normalise"])
            validator1.normalise.return_value = result1
            validator2 = mock.Mock(name="validator2", spec_set=["normalise"])
            validator2.normalise.return_value = result2

            self.assertIs(self.make_spec(validator1, validator2).normalise(self.meta, "blah"), result2)
            validator1.normalise.assert_called_once_with(self.meta, "blah")
            validator2.normalise.assert_called_once_with(self.meta, result1)

    describe "string_choice_spec":
        def make_spec(self, choices=NotSpecified, reason=NotSpecified):
            choices = ["", "adsf", "asdf"] if choices is NotSpecified else choices
            return sb.string_choice_spec(choices, reason=reason)

        it "takes in a list of choices and a reason":
            choice1 = mock.Mock(name="choice1")
            choice2 = mock.Mock(name="choice2")
            reason = mock.Mock(name="reason")
            spec = self.make_spec([choice1, choice2], reason=reason)
            self.assertEqual(spec.choices, [choice1, choice2])
            self.assertEqual(spec.reason, reason)

        it "defaults reason":
            self.assertEqual(self.make_spec([]).reason, "Expected one of the available choices")

        it "complains if the value isn't one of the choices":
            choices = ["one", "two", "three"]
            reason = mock.Mock(name="reason")
            with self.fuzzyAssertRaisesError(BadSpecValue, reason, available=choices, got="blah", meta=self.meta):
                self.make_spec(choices, reason=reason).normalise(self.meta, "blah")

describe TestCase, "create_spec":
    before_each:
        self.meta = mock.Mock(name="meta", spec_set=Meta)

    it "takes in a kls and specs for options we will instantiate it with":
        kls = mock.Mock(name="kls")
        opt1 = mock.Mock(name="opt1")
        opt2 = mock.Mock(name="opt2")

        set_options = mock.Mock(name="set_options")
        set_options_instance = mock.Mock(name="set_options_instance")
        set_options.return_value = set_options_instance

        with mock.patch.object(sb, "set_options", set_options):
            spec = sb.create_spec(kls, a=opt1, b=opt2)

        self.assertIs(spec.kls, kls)
        self.assertEqual(spec.expected, {"a": opt1, "b": opt2})
        self.assertEqual(spec.expected_spec, set_options_instance)
        set_options.assert_called_once_with(a=opt1, b=opt2)

    it "validates using provided validators":
        v1 = mock.Mock(name="v1")
        v2 = mock.Mock(name="v2")
        called = []

        v1.normalise.side_effect = lambda m, v: called.append(1)
        v2.normalise.side_effect = lambda m, v: called.append(2)

        kls = namedlist("kls", "blah")
        val = {"blah": "stuff"}

        spec = sb.create_spec(kls, v1, v2, blah=sb.string_spec())
        self.assertEqual(spec.validators, (v1, v2))

        # Normalising with the create_spec will call validators first
        spec.normalise(self.meta, val)

        v1.normalise.assert_called_once_with(self.meta, val)
        v2.normalise.assert_called_once_with(self.meta, val)
        self.assertEqual(called, [1, 2])

    it "returns value as is if already an instance of our kls":
        kls = type("kls", (object, ), {})
        spec = sb.create_spec(kls)
        instance = kls()
        self.assertIs(spec.normalise(self.meta, instance), instance)

    it "uses expected to normalise the val and passes that in as kwargs to kls constructor":
        class Blah(object): pass
        instance = sb.create_spec(Blah).normalise(self.meta, {})
        self.assertIs(instance.__class__, Blah)

        class Meh(object):
            def __init__(self, a, b):
                self.a = a
                self.b = b

        a_val = mock.Mock(name="a_val")
        b_val = mock.Mock(name="b_val")
        c_val = mock.Mock(name="c_val")
        instance = sb.create_spec(Meh, a=pass_through_spec(), b=pass_through_spec()).normalise(self.meta, {"a": a_val, "b": b_val, "c": c_val})
        self.assertIs(instance.__class__, Meh)
        self.assertIs(instance.a, a_val)
        self.assertIs(instance.b, b_val)

    it "passes through errors from expected_spec":
        class Meh(object):
            def __init__(self, a):
                self.a = a

        a_val = mock.Mock(name="a_val")
        spec_error = BadSpecValue("nope!")
        a_spec = mock.Mock(name="a_spec", spec_set=["normalise"])
        a_spec.normalise.side_effect = spec_error
        with self.fuzzyAssertRaisesError(BadSpecValue, meta=self.meta, _errors=[spec_error]):
            sb.create_spec(Meh, a=a_spec).normalise(self.meta, {"a": a_val})

describe TestCase, "or_spec":
    before_each:
        self.val = mock.Mock(name="val")
        self.meta = mock.Mock(name="meta", spec_set=Meta)
        self.spec1 = mock.Mock(name="spec1")
        self.spec2 = mock.Mock(name="spec2")
        self.spec3 = mock.Mock(name="spec3")

    it "takes in specs as positional arguments":
        spec = sb.or_spec(self.spec1, self.spec3, self.spec2)
        self.assertEqual(spec.specs, (self.spec1, self.spec3, self.spec2))

    it "tries each spec until one succeeds":
        error1 = BadSpecValue("error1")
        error2 = BadSpecValue("error2")
        result = mock.Mock(name="result")
        self.spec1.normalise.side_effect = error1
        self.spec2.normalise.side_effect = error2
        self.spec3.normalise.return_value = result
        self.assertIs(sb.or_spec(self.spec1, self.spec2, self.spec3).normalise(self.meta, self.val), result)

        self.spec1.normalise.assert_called_once_with(self.meta, self.val)
        self.spec2.normalise.assert_called_once_with(self.meta, self.val)
        self.spec3.normalise.assert_called_once_with(self.meta, self.val)

    it "doesn't try more specs than it needs to":
        error1 = BadSpecValue("error1")
        result = mock.Mock(name="result")
        self.spec1.normalise.side_effect = error1
        self.spec2.normalise.return_value = result
        self.assertIs(sb.or_spec(self.spec1, self.spec2, self.spec3).normalise(self.meta, self.val), result)

        self.spec1.normalise.assert_called_once_with(self.meta, self.val)
        self.spec2.normalise.assert_called_once_with(self.meta, self.val)
        self.assertEqual(len(self.spec3.normalise.mock_calls), 0)

    it "raises all the errors if none of the specs pass":
        error1 = BadSpecValue("error1")
        error2 = BadSpecValue("error2")
        error3 = BadSpecValue("error3")
        self.spec1.normalise.side_effect = error1
        self.spec2.normalise.side_effect = error2
        self.spec3.normalise.side_effect = error3

        with self.fuzzyAssertRaisesError(BadSpecValue, "Value doesn't match any of the options", meta=self.meta, val=self.val, _errors=[error1, error2, error3]):
            sb.or_spec(self.spec1, self.spec2, self.spec3).normalise(self.meta, self.val)

        self.spec1.normalise.assert_called_once_with(self.meta, self.val)
        self.spec2.normalise.assert_called_once_with(self.meta, self.val)
        self.spec3.normalise.assert_called_once_with(self.meta, self.val)

describe TestCase, "and_spec":
    before_each:
        self.val = mock.Mock(name="val")
        self.meta = mock.Mock(name="meta", spec_set=Meta)
        self.spec1 = mock.Mock(name="spec1")
        self.spec2 = mock.Mock(name="spec2")
        self.spec3 = mock.Mock(name="spec3")

    it "takes in specs as positional arguments":
        spec = sb.or_spec(self.spec1, self.spec3, self.spec2)
        self.assertEqual(spec.specs, (self.spec1, self.spec3, self.spec2))

    it "puts successive values through all specs":
        val1 = mock.Mock(name="val1")
        val2 = mock.Mock(name="val2")
        result = mock.Mock(name="result")
        self.spec1.normalise.return_value = val1
        self.spec2.normalise.return_value = val2
        self.spec3.normalise.return_value = result
        self.assertIs(sb.and_spec(self.spec1, self.spec2, self.spec3).normalise(self.meta, self.val), result)

        self.spec1.normalise.assert_called_once_with(self.meta, self.val)
        self.spec2.normalise.assert_called_once_with(self.meta, val1)
        self.spec3.normalise.assert_called_once_with(self.meta, val2)

    it "raises an error with all transformations if one of them fails":
        val1 = mock.Mock(name="val1")
        error = BadSpecValue("error1")
        self.spec1.normalise.return_value = val1
        self.spec2.normalise.side_effect = error

        with self.fuzzyAssertRaisesError(BadSpecValue, "Value didn't match one of the options", meta=self.meta, transformations=[self.val, val1], _errors=[error]):
            sb.and_spec(self.spec1, self.spec2, self.spec3).normalise(self.meta, self.val)

        self.spec1.normalise.assert_called_once_with(self.meta, self.val)
        self.spec2.normalise.assert_called_once_with(self.meta, val1)
        self.assertEqual(self.spec3.normalise.mock_calls, [])

describe TestCase, "optional_spec":
    before_each:
        self.val = mock.Mock(name="val")
        self.meta = mock.Mock(name="meta", spec_set=Meta)
        self.spec = mock.Mock(name="spec")

    it "takes in a spec":
        spec = sb.optional_spec(self.spec)
        self.assertIs(spec.spec, self.spec)

    it "returns NotSpecified if there is no value":
        self.assertIs(sb.optional_spec(self.spec).normalise(self.meta, NotSpecified), NotSpecified)

    it "Proxies the spec if there is a value":
        result = mock.Mock(name="result")
        self.spec.normalise.return_value = result
        self.assertIs(sb.optional_spec(self.spec).normalise(self.meta, self.val), result)
        self.spec.normalise.assert_called_once_with(self.meta, self.val)

describe TestCase, "dict_from_bool_spec":
    before_each:
        self.val = mock.Mock(name="val")
        self.meta = mock.Mock(name="meta", spec_set=Meta)
        self.spec = mock.Mock(name="spec")

    it "takes in a dict_maker and a spec":
        dict_maker = mock.Mock(name="dict_maker")
        spec = sb.dict_from_bool_spec(dict_maker, self.spec)
        self.assertIs(spec.dict_maker, dict_maker)
        self.assertIs(spec.spec, self.spec)

    it "proxies to the spec with an empty dictionary if no value":
        result = mock.Mock(name="result")
        self.spec.normalise.return_value = result
        self.assertIs(sb.dict_from_bool_spec(lambda: 1, self.spec).normalise(self.meta, NotSpecified), result)
        self.spec.normalise.assert_called_once_with(self.meta, {})

    it "uses dict_maker if the value is a boolean":
        val = mock.Mock(name="val")
        result = mock.Mock(name="result")

        dict_maker = mock.Mock(name="dict_maker")
        dict_maker.return_value = val

        self.spec.normalise.return_value = result
        self.assertIs(sb.dict_from_bool_spec(dict_maker, self.spec).normalise(self.meta, False), result)
        dict_maker.assert_called_once_with(self.meta, False)
        self.spec.normalise.assert_called_once_with(self.meta, val)

    it "uses the value itself if not a boolean":
        val = mock.Mock(name="val")
        result = mock.Mock(name="result")
        self.spec.normalise.return_value = result
        self.assertIs(sb.dict_from_bool_spec(lambda: 1, self.spec).normalise(self.meta, val), result)
        self.spec.normalise.assert_called_once_with(self.meta, val)

describe TestCase, "formatted":
    before_each:
        self.val = mock.Mock(name="val")
        self.meta = mock.Mock(name="meta", spec_set=Meta)
        self.spec = mock.Mock(name="spec")

    it "takes in spec, formatter and expected_type":
        spec = mock.Mock(name="spec")
        formatter = mock.Mock(name="formatter")
        expected_type = mock.Mock(name="expected_type")
        formatted = sb.formatted(spec, formatter, expected_type)
        self.assertIs(formatted.spec, spec)
        self.assertIs(formatted.formatter, formatter)
        self.assertIs(formatted.expected_type, expected_type)

    it "uses the formatter":
        meta_path = mock.Mock(name="path")
        options = mock.Mock(name="options")
        meta_class = mock.Mock(name="meta_class")
        meta_class.return_value = options

        self.meta.path = meta_path
        self.meta.everything = mock.Mock(name="everything", __class__=meta_class)

        key_names = mock.Mock(name="key_names")
        self.meta.key_names = key_names

        formatter = mock.Mock(name="formatter")
        formatter_instance = mock.Mock(name="formatter_instance")
        formatter.return_value = formatter_instance

        formatted = mock.Mock(name="formatted")
        formatter_instance.format.return_value = formatted

        specd = mock.Mock(name="specd")
        self.spec.normalise.return_value = specd

        self.assertIs(sb.formatted(self.spec, formatter, expected_type=mock.Mock).normalise(self.meta, self.val), formatted)
        formatter_instance.format.assert_called_once()
        formatter.assert_called_once_with(options, meta_path, value=specd)

        meta_class.assert_called_once()
        self.assertEqual(len(options.update.mock_calls), 2)

        self.spec.normalise.assert_called_once_with(self.meta, self.val)

    it "complains if formatted value has wrong type":
        formatter = lambda *args, **kwargs: "asdf"
        spec = sb.any_spec()
        self.meta.everything = {}
        self.meta.key_names.return_value = {}
        with self.fuzzyAssertRaisesError(BadSpecValue, "Expected a different type", expected=mock.Mock, got=str):
            sb.formatted(spec, formatter, expected_type=mock.Mock).normalise(self.meta, self.val)

    it "works with normal dictionary meta.everything":
        formatter = lambda *args, **kwargs: "asdf"
        spec = sb.any_spec()
        self.meta.everything = {"blah": 1}
        self.meta.key_names.return_value = {}
        res = sb.formatted(spec, formatter).normalise(self.meta, self.val)
        self.assertEqual(res, "asdf")

describe TestCase, "overridden":
    it "returns the value it's initialised with":
        meta = mock.Mock(name="meta", spec=[])
        value = mock.Mock(name="value", spec=[])
        override = mock.Mock(name="override", spec=[])
        self.assertIs(sb.overridden(override).normalise(meta, value), override)

describe TestCase, "any_spec":
    it "returns the value it's given":
        meta = mock.Mock(name="meta", spec=[])
        value = mock.Mock(name="value", spec=[])
        self.assertIs(sb.any_spec().normalise(meta, value), value)

