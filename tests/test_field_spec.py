# coding: spec

from input_algorithms.field_spec import FieldSpec, Field, FieldSpecMixin, FieldSpecMetakls
from input_algorithms import spec_base as sb
from input_algorithms.dictobj import dictobj
from input_algorithms.errors import BadSpec
from input_algorithms.meta import Meta

from noseOfYeti.tokeniser.support import noy_sup_setUp
from tests.helpers import TestCase
import mock
import six

describe TestCase, "FieldSpec":
    describe "make_spec":
        before_each:
            self.ret = mock.Mock(name="spec")
            self.inp = mock.Mock(name="inp")
            self.spec = mock.NonCallableMock(name="spec")
            self.spec.normalise.return_value = self.ret
            self.meta = Meta({}, [])

        it "handles field that is a callable to a spec":
            class MyKls(dictobj):
                fields = {"one": lambda: self.spec}

            spec = FieldSpec(MyKls).make_spec(self.meta)
            self.assertEqual(
                  spec.normalise(self.meta, {"one": self.inp})
                , {"one": self.ret}
                )

        it "handles field that is a callable to a Field":
            class MyKls(dictobj):
                fields = {"one": lambda: Field(lambda: self.spec)}

            spec = FieldSpec(MyKls).make_spec(self.meta)
            self.assertEqual(
                  spec.normalise(self.meta, {"one": self.inp})
                , {"one": self.ret}
                )

        it "handles field that is a callable with a description":
            class MyKls(dictobj):
                fields = {"one": ("description", lambda: Field(lambda: self.spec))}

            spec = FieldSpec(MyKls).make_spec(self.meta)
            self.assertEqual(
                  spec.normalise(self.meta, {"one": self.inp})
                , {"one": self.ret}
                )

            class MyKls2(dictobj):
                fields = {"two": ("description", lambda: self.spec)}

            spec = FieldSpec(MyKls2).make_spec(self.meta)
            self.assertEqual(
                  spec.normalise(self.meta, {"two": self.inp})
                , {"two": self.ret}
                )

        it "handles a field that is not callable with a description":
            class MyKls(dictobj):
                fields = {"one": ("description", Field(lambda: self.spec))}

            spec = FieldSpec(MyKls).make_spec(self.meta)
            self.assertEqual(
                  spec.normalise(self.meta, {"one": self.inp})
                , {"one": self.ret}
                )

            class MyKls2(dictobj):
                fields = {"two": ("description", self.spec)}

            spec = FieldSpec(MyKls2).make_spec(self.meta)
            self.assertEqual(
                  spec.normalise(self.meta, {"two": self.inp})
                , {"two": self.ret}
                )

        it "handles a field that is not callable":
            class MyKls(dictobj):
                fields = {"one": Field(lambda: self.spec)}

            spec = FieldSpec(MyKls).make_spec(self.meta)
            self.assertEqual(
                  spec.normalise(self.meta, {"one": self.inp})
                , {"one": self.ret}
                )

            class MyKls2(dictobj):
                fields = {"two": self.spec}

            spec = FieldSpec(MyKls2).make_spec(self.meta)
            self.assertEqual(
                  spec.normalise(self.meta, {"two": self.inp})
                , {"two": self.ret}
                )

    describe "normalise":
        it "complains about a class that has no fields":
            class MyKls(object):
                pass

            spec = FieldSpec(MyKls)
            with self.fuzzyAssertRaisesError(BadSpec, "No fields on the class!", kls=MyKls):
                spec.normalise(Meta({}, []), {})

        it "complains if any field has no spec":
            class MyKls(object):
                fields = {"one": "one!", "two": type("blah", (object, ), {"normalise": lambda:1})(), "three": ("three!", )}

            meta = Meta({}, [])
            error1 = BadSpec("No spec found for option", meta=meta.at("one"), option="one")
            error2 = BadSpec("No spec found for option", meta=meta.at("three"), option="three")

            spec = FieldSpec(MyKls)
            with self.fuzzyAssertRaisesError(BadSpec, _errors=[error1, error2]):
                spec.normalise(Meta({}, []), {})

        it "handles a class with empty fields":
            class MyKls(object):
                fields = {}

            spec = FieldSpec(MyKls)
            instance = spec.normalise(Meta({}, []), {})
            self.assertEqual(type(instance), MyKls)

describe TestCase, "FieldSpecMixin":
    it "provides FieldSpec which passes the class to an instance of FieldSpec":
        class MyKls(FieldSpecMixin):
            fields = {}

        formatter = mock.Mock(name="formatter")
        spec = MyKls.FieldSpec(formatter=formatter)
        self.assertIs(type(spec), FieldSpec)
        self.assertIs(spec.kls, MyKls)
        self.assertIs(spec.formatter, formatter)

describe TestCase, "FieldSpecMetaKls":
    it "convert fields into a fields dictionary":
        inp_field1 = mock.Mock(name="inp_field1", is_input_algorithms_field=True, help="")
        inp_field2 = mock.Mock(name="inp_field2", is_input_algorithms_field=True, help="")

        class MyKls(six.with_metaclass(FieldSpecMetakls)):
            field1 = inp_field1
            field2 = inp_field2

            one = "something else"

        self.assertEqual(MyKls.fields, {"field1": inp_field1, "field2": inp_field2})

    it "convert fields into a fields dictionary with tuple of help and field":
        help1 = mock.Mock(name="help1")
        help2 = mock.Mock(name="help2")
        inp_field1 = mock.Mock(name="inp_field1", is_input_algorithms_field=True, help=help1)
        inp_field2 = mock.Mock(name="inp_field2", is_input_algorithms_field=True, help=help2)

        class MyKls(six.with_metaclass(FieldSpecMetakls)):
            field1 = inp_field1
            field2 = inp_field2

            one = "something else"

        self.assertEqual(MyKls.fields, {"field1": (help1, inp_field1), "field2": (help2, inp_field2)})

    it "Adds FieldSpecMixin as a baseclass":
        class MyKls(six.with_metaclass(FieldSpecMetakls)):
            pass

        assert hasattr(MyKls, "FieldSpec")

describe TestCase, "Field":
    it "references mixin and metaclass":
        self.assertIs(Field.mixin, FieldSpecMixin)
        self.assertIs(Field.metaclass, FieldSpecMetakls)

    it "has is_input_algorithms_field set to True":
        self.assertEqual(Field.is_input_algorithms_field, True)
        self.assertEqual(Field(lambda: 1).is_input_algorithms_field, True)

    it "takes in several things like spec, help, formatted, wrapper and default":
        spec = mock.Mock(name="spec")
        help = mock.Mock(name="help")
        formatted = mock.Mock(name="formatted")
        wrapper = mock.Mock(name="wrapper")
        default = mock.Mock(name="default")

        field = Field(spec, help=help, formatted=formatted, wrapper=wrapper, default=default)

        self.assertIs(field.spec, spec)
        self.assertIs(field.help, help)
        self.assertIs(field.formatted, formatted)
        self.assertIs(field.wrapper, wrapper)
        self.assertIs(field.default, default)

    describe "make_spec":
        before_each:
            self.meta = Meta({}, [])
            self.formatter = mock.Mock(name="formatter")

        it "calls the spec if callable":
            instance = mock.Mock(name="instance")
            spec = mock.Mock(name="spec", return_value=instance)
            self.assertIs(Field(spec).make_spec(self.meta, self.formatter), instance)

        it "wraps spec in a defaulted if default is specified":
            ret = mock.Mock(name="ret")
            inp = mock.Mock(name="inp")
            dflt = mock.Mock(name="dflt")
            instance = mock.Mock(name="instance")
            instance.normalise.return_value = ret
            spec = mock.Mock(name="spec", return_value=instance)
            spec = Field(spec, default=dflt).make_spec(self.meta, self.formatter)

            self.assertIs(spec.normalise(self.meta, sb.NotSpecified), dflt)
            self.assertIs(spec.normalise(self.meta, inp), ret)

        it "wraps default in a formatted if default and formatted are defined":
            ret = mock.Mock(name="ret")
            inp = mock.Mock(name="inp")
            dflt = mock.Mock(name="dflt")

            class Formatter(object):
                def __init__(self, options, path, value):
                    self.value = value

                def format(self):
                    return ("formatted", self.value)

            instance = mock.Mock(name="instance")
            instance.normalise.return_value = ret
            spec = mock.Mock(name="spec", return_value=instance)
            spec = Field(spec, default=dflt, formatted=True).make_spec(self.meta, Formatter)

            self.assertEqual(spec.normalise(self.meta, sb.NotSpecified), ("formatted", dflt))
            self.assertEqual(spec.normalise(self.meta, inp), ("formatted", ret))

        it "wraps everything in wrapper if it's defined":
            spec = Field(sb.string_or_int_as_string_spec, wrapper=sb.listof).make_spec(self.meta, self.formatter)
            self.assertEqual(spec.normalise(self.meta, 1), ["1"])

