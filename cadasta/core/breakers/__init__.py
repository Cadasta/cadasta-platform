from kombu.exceptions import OperationalError

from .breaker import CircuitBreaker


celery = CircuitBreaker(
    'celery', fail_max=1,
    expected_errors=(OperationalError,))
