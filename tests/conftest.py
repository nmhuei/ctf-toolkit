import os
import pytest

@pytest.fixture(autouse=True, scope="session")
def _isolate_test_environment():
    """Ensure runner ambient NO_COLOR does not suppress ANSI color assertions in tests."""
    old_no_color = os.environ.pop("NO_COLOR", None)
    try:
        yield
    finally:
        if old_no_color is not None:
            os.environ["NO_COLOR"] = old_no_color
