import os

import pytest

pytestmark = pytest.mark.skipif(
    not os.getenv("RUN_DB_TESTS"),
    reason="Set RUN_DB_TESTS=1 with a configured MySQL/Redis environment to run integration tests",
)


def test_integration_environment_enabled():
    assert os.getenv("RUN_DB_TESTS")
