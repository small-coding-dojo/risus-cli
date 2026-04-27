"""Test that the stack starts cleanly from scratch."""
import pytest
import urllib.request

from tests.e2e.conftest import SERVER_URL

pytestmark = pytest.mark.e2e


@pytest.mark.asyncio
async def test_stack_starts_clean(risus_stack):
    """Stack reached healthy in <120s via the session fixture; verify healthz responds."""
    assert risus_stack is not None, "Stack failed to start"
    with urllib.request.urlopen(f"{SERVER_URL}/healthz", timeout=5) as resp:
        assert resp.status == 200
        import json
        body = json.loads(resp.read())
        assert body.get("ok") is True
