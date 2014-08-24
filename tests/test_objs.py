# coding: spec

from input_algorithms.objs import objMaker

from tests.helpers import TestCase

import mock

describe TestCase, "objMaker":
    it "makes a class that sets default attributes on instantiation":
        kls = objMaker("Thing", ("one", 1), ("two", 2), "three")
        self.assertEqual(kls.__name__, "Thing")
        instance = kls()
        self.assertEqual(instance.one, 1)
        self.assertEqual(instance.two, 2)
        self.assertEqual(instance.three, None)

    it "allows options to be overridden with positional args":
        kls = objMaker("Thing", ("one", 1), ("two", 2), "three")
        self.assertEqual(kls.__name__, "Thing")
        instance = kls(3, 4, 5)
        self.assertEqual(instance.one, 3)
        self.assertEqual(instance.two, 4)
        self.assertEqual(instance.three, 5)

        kls = objMaker("Thing", "three", ("one", 1), ("two", 2))
        self.assertEqual(kls.__name__, "Thing")
        instance = kls(3, 4, 5)
        self.assertEqual(instance.one, 4)
        self.assertEqual(instance.two, 5)
        self.assertEqual(instance.three, 3)

    it "allows options to be overridden with keyword args":
        kls = objMaker("Thing", ("one", 1), ("two", 2), "three")
        self.assertEqual(kls.__name__, "Thing")
        instance = kls(one=3, two=4, three=5)
        self.assertEqual(instance.one, 3)
        self.assertEqual(instance.two, 4)
        self.assertEqual(instance.three, 5)

        kls = objMaker("Thing", "three", ("one", 1), ("two", 2))
        self.assertEqual(kls.__name__, "Thing")
        instance = kls(one=3, two=4, three=5)
        self.assertEqual(instance.one, 3)
        self.assertEqual(instance.two, 4)
        self.assertEqual(instance.three, 5)

    it "allows options to be overridden with positional and keyword args":
        kls = objMaker("Thing", ("one", 1), ("two", 2), "three")
        self.assertEqual(kls.__name__, "Thing")
        instance = kls(3, two=4, three=5)
        self.assertEqual(instance.one, 3)
        self.assertEqual(instance.two, 4)
        self.assertEqual(instance.three, 5)

        kls = objMaker("Thing", "three", ("one", 1), ("two", 2))
        self.assertEqual(kls.__name__, "Thing")
        instance = kls(3, two=4, one=5)
        self.assertEqual(instance.one, 5)
        self.assertEqual(instance.two, 4)
        self.assertEqual(instance.three, 3)

