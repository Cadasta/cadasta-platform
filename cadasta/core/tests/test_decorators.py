import unittest
from unittest.mock import patch

from ..decorators import handle_exc


@patch('core.decorators.logger')
class HandleExcTest(unittest.TestCase):

    def test_requires_arguments(self, logger):
        with self.assertRaises(TypeError) as e:
            @handle_exc
            def asdf():
                pass
        assert e.exception.args[0].endswith(
            "> not an instance of BaseException")
        assert not logger.called

    def test_requires_valid_exceptions(self, logger):
        with self.assertRaises(TypeError) as e:
            @handle_exc('foo')
            def asdf():
                pass
        assert e.exception.args == ("'foo' not an instance of BaseException", )
        assert not logger.called

    def test_handles_exception(self, logger):
        class MyException(Exception):
            pass

        @handle_exc(MyException)
        def asdf():
            raise MyException("OH NO!")

        output = asdf()
        assert output is None
        logger.exception.assert_called_once_with(
            "Handling failure for %r", asdf.__name__)

    def test_handles_exceptions(self, logger):
        class MyException(Exception):
            pass

        @handle_exc(MyException, ValueError)
        def asdf(val):
            if val:
                raise MyException("OH NO!")
            raise ValueError("Value Error!")

        for b in (True, False):
            output = asdf(b)
            assert output is None
            logger.exception.assert_called_once_with(
                "Handling failure for %r", asdf.__name__)
            logger.exception.reset_mock()

    def test_handles_fallback(self, logger):
        @handle_exc(ValueError, fallback="foo")
        def asdf():
            raise ValueError("Value Error!")

        output = asdf()
        assert output == "foo"
        logger.exception.assert_called_once_with(
            "Handling failure for %r", asdf.__name__)
