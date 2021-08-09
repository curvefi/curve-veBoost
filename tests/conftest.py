import pytest

pytest_plugins = [
    "fixtures.accounts",
    "fixtures.constants",
    "fixtures.deployments",
    "fixtures.functions",
]


@pytest.fixture(scope="module")
def module_isolation(chain):
    """Custom module level isolation, preserves session level fixtures."""
    chain.snapshot()
    yield
    chain.revert()


@pytest.fixture(autouse=True)
def function_isolation(chain, history, module_isolation):
    """Custom function level isolation."""
    start = len(history)
    yield
    if (undo_count := len(history) - start) > 0:
        chain.undo(undo_count)
