from unittest.mock import patch, MagicMock

from django.test import TestCase

from core.types import HandledErrors


class HandledErrorsTest(TestCase):

    def test_handlederrors_missing_property(self):
        with self.assertRaises(AssertionError):
            class Foo(metaclass=HandledErrors):
                # No HANDLED_ERRORS property
                pass

    def test_handlederrors_missing_method(self):
        with self.assertRaises(ValueError):
            class Foo(metaclass=HandledErrors):
                # Foo doesn't exist as a method
                HANDLED_ERRORS = [('foo', Exception)]

    @patch('core.types.logging')
    def test_handlederrors_caught_exception(self, logging):
        mock_logger = MagicMock()
        logging.getLogger.return_value = mock_logger

        class Foo(metaclass=HandledErrors):
            HANDLED_ERRORS = [('foo', ValueError)]

            def foo(self):
                raise ValueError("This should be caught")

        Foo().foo()
        logging.getLogger.assert_called_once_with(self.__module__)
        mock_logger.exception.assert_called_once_with(
            "Silenced cache failure at {}.{}.{}()"
            "".format(self.__module__, 'Foo', 'foo')
        )

    @patch('core.types.logging')
    def test_handlederrors_many_caught_exceptions(self, logging):
        """
        Ensure HandledErrors can accept multiple allowed exceptions
        """
        mock_logger = MagicMock()
        logging.getLogger.return_value = mock_logger
        caught_exceptions = (ValueError, AssertionError)

        class Foo(metaclass=HandledErrors):
            HANDLED_ERRORS = [('foo', caught_exceptions)]

            def foo(self, exception):
                raise exception("Error")

        # Handled exceptions
        for exception in caught_exceptions:
            Foo().foo(exception)
            logging.getLogger.assert_called_once_with(self.__module__)
            mock_logger.exception.assert_called_once_with(
                "Silenced cache failure at {}.{}.{}()"
                "".format(self.__module__, 'Foo', 'foo')
            )

            logging.getLogger.reset_mock()
            mock_logger.exception.reset_mock()

        # Not handled exceptions
        with self.assertRaises(NotImplementedError):
            Foo().foo(NotImplementedError)
        assert not logging.getLogger.called
        assert not mock_logger.exception.called

    @patch('core.types.logging')
    def test_handlederrors_uncaught_exception(self, logging):
        mock_logger = MagicMock()
        logging.getLogger.return_value = mock_logger

        class Foo(metaclass=HandledErrors):
            HANDLED_ERRORS = [
                ('foo', ValueError),
                ('bar', ValueError),
            ]

            def foo(self):
                raise TypeError("This should not be caught")

            def bar(self):
                raise ValueError("This should be caught")

            def baz(self):
                raise NotImplementedError("This should not be caught")

        with self.assertRaises(TypeError):
            Foo().foo()

        with self.assertRaises(NotImplementedError):
            Foo().baz()

        Foo().bar()
        logging.getLogger.assert_called_once_with(self.__module__)
        mock_logger.exception.assert_called_once_with(
            "Silenced cache failure at {}.{}.{}()"
            "".format(self.__module__, 'Foo', 'bar')
        )
