from setuptools import setup, find_packages
from input_algorithms import VERSION

setup(
      name = "input_algorithms"
    , version = VERSION
    , packages = ['input_algorithms'] + ['input_algorithms.%s' % pkg for pkg in find_packages('input_algorithms')]
    , include_package_data = True

     , install_requires =
       [ 'delfick_error>=1.6'
       , "namedlist"
       ]

    , extras_require =
      { "tests":
        [ "nose"
        , "mock"
        , "noseOfYeti"
        ]
      }

    # metadata for upload to PyPI
    , url = "http://input_algorithms.readthedocs.org"
    , author = "Stephen Moore"
    , author_email = "stephen@delfick.com"
    , description = "Thin DSL for creating input_algorithms"
    , license = "MIT"
    , keywords = "yaml specification"
    )

