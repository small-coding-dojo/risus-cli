import pytest
from server.locks import LockManager


@pytest.fixture
def mgr():
    return LockManager()


@pytest.mark.asyncio
async def test_acquire_returns_true(mgr):
    ok = await mgr.acquire("Goblin", "client-1", "Alice")
    assert ok is True


@pytest.mark.asyncio
async def test_acquire_contention(mgr):
    await mgr.acquire("Goblin", "client-1", "Alice")
    ok = await mgr.acquire("Goblin", "client-2", "Bob")
    assert ok is False


@pytest.mark.asyncio
async def test_holder(mgr):
    await mgr.acquire("Goblin", "client-1", "Alice")
    assert mgr.holder("Goblin") == "client-1"
    assert mgr.holder("Nobody") is None


@pytest.mark.asyncio
async def test_holder_display(mgr):
    await mgr.acquire("Goblin", "client-1", "Alice")
    assert mgr.holder_display("Goblin") == "Alice"


@pytest.mark.asyncio
async def test_release(mgr):
    await mgr.acquire("Goblin", "client-1", "Alice")
    released = await mgr.release("Goblin", "client-1")
    assert released is True
    assert mgr.holder("Goblin") is None


@pytest.mark.asyncio
async def test_release_wrong_client(mgr):
    await mgr.acquire("Goblin", "client-1", "Alice")
    released = await mgr.release("Goblin", "client-2")
    assert released is False
    assert mgr.holder("Goblin") == "client-1"


@pytest.mark.asyncio
async def test_release_all(mgr):
    await mgr.acquire("Goblin", "client-1", "Alice")
    await mgr.acquire("Orc", "client-1", "Alice")
    await mgr.acquire("Dragon", "client-2", "Bob")
    freed = await mgr.release_all("client-1")
    assert set(freed) == {"Goblin", "Orc"}
    assert mgr.holder("Dragon") == "client-2"
    assert mgr.holder("Goblin") is None


@pytest.mark.asyncio
async def test_snapshot(mgr):
    await mgr.acquire("Goblin", "client-1", "Alice")
    snap = mgr.snapshot()
    assert snap == {"Goblin": "Alice"}


@pytest.mark.asyncio
async def test_reacquire_after_release(mgr):
    await mgr.acquire("Goblin", "client-1", "Alice")
    await mgr.release("Goblin", "client-1")
    ok = await mgr.acquire("Goblin", "client-2", "Bob")
    assert ok is True
