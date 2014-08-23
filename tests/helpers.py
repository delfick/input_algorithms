from delfick_error import DelfickErrorTestMixin, safe_repr
from unittest import TestCase as UnitTestTestCase
from contextlib import contextmanager
import tempfile
import shutil
import os

class TestCase(UnitTestTestCase, DelfickErrorTestMixin):
    @contextmanager
    def a_temp_file(self, body=None, removed=False):
        """
        Yield a temporary file and ensure it's deleted
        """
        filename = None
        try:
            filename = tempfile.NamedTemporaryFile(delete=False).name
            if body:
                with open(filename, 'w') as fle:
                    fle.write(body)
            if removed:
                os.remove(filename)
            yield filename
        finally:
            if filename and os.path.exists(filename):
                os.remove(filename)

    @contextmanager
    def a_temp_dir(self, removed=False):
        """
        Yield a temporary directory and ensure it is deleted
        """
        directory = None
        try:
            directory = tempfile.mkdtemp()
            if removed:
                shutil.rmtree(directory)
            yield directory
        finally:
            if directory and os.path.exists(directory):
                shutil.rmtree(directory)

