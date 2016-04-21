Input Algorithms
================

A DSL to assist with writing specifications describing valid data and testing
that inputted data meets those defined specifications.

.. image:: https://travis-ci.org/delfick/input_algorithms.png?branch=master
    :target: https://travis-ci.org/delfick/input_algorithms

Why the name?
=============

I got the inspiration from the movie Transcendence when a character says
something to the effect of "We could do this if we had better input
algorithms".

Installation
------------

Use pip!:

.. code-block:: bash

    pip install input_algorithms

Or if you're developing it:

.. code-block:: bash

    pip install -e .
    pip install -e ".[tests]"

USAGE
-------

Here is an example to help you use the library.

.. code-block:: python

    from input_algorithms.validators import Validator
    from input_algorithms.dictobj import dictobj
    from input_algorithms import spec_base as sb
    from input_algorithms.meta import Meta
    import re

    meta = Meta({},[])

    # 1. Create a class defining your fields.
    class PersonDictObj(dictobj):
        fields = ["name", "age"]

    # 2. Create custom validate methods as required.
    class ValidName(Validator):
        def validate(self, meta, val):
            matcher = re.compile("^[A-Za-z\ ]+$")
            if not matcher.match(val):
                raise Exception("{0} doesn't look like a name.".format(val))
            return val

    class ValidAge(Validator):
        def validate(self, meta, val):
            if val > 120:
                raise Exception("I don't believe you are that old")
            return val

    # 3. Tie together the pieces.
    person_spec = sb.create_spec(
        PersonDictObj,
        name = sb.required(sb.valid_string_spec(ValidName())),
        age = sb.and_spec(sb.integer_spec(), ValidAge()),
    )

    # 4. Have some data
    data = {"name": "Ralph", "age": 23}

    # 5. Normalise the data into your object
    normalised = person_spec.normalise(meta, data)

    # 6. Use the object!
    print("Name is {0}".format(normalised.name))
    print("Age is {0}".format(normalised.age))

Tests
-----

To run the tests in this project, just use the helpful script:

.. code-block:: bash

    ./test.sh

Or run tox:

.. code-block:: bash

    tox

