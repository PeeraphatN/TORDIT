"""เทสต์ JobStore — TTL, ความจุ, read-modify-write (app/jobs.py)."""

from app.jobs import JobStore
from app.schemas import CheckResult, CheckStatus


class FakeClock:
    """นาฬิกาปลอมไว้เลื่อนเวลาเองในเทสต์ TTL โดยไม่ต้อง sleep จริง."""

    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        return self.now


def _job(check_id: str, status: CheckStatus = CheckStatus.PROCESSING) -> CheckResult:
    return CheckResult(check_id=check_id, status=status)


def test_get_missing_returns_none():
    store = JobStore()
    assert store.get("nope") is None


def test_put_then_get_roundtrip():
    store = JobStore()
    store.put(_job("chk_1"))
    got = store.get("chk_1")
    assert got is not None
    assert got.check_id == "chk_1"
    assert got.status is CheckStatus.PROCESSING


def test_update_changes_fields_in_place():
    store = JobStore()
    store.put(_job("chk_1"))
    updated = store.update("chk_1", status=CheckStatus.COMPLETED)
    assert updated is not None
    assert updated.status is CheckStatus.COMPLETED
    # อ่านซ้ำต้องได้ค่าใหม่
    assert store.get("chk_1").status is CheckStatus.COMPLETED


def test_update_missing_returns_none():
    store = JobStore()
    assert store.update("ghost", status=CheckStatus.FAILED) is None


def test_capacity_evicts_oldest_first():
    store = JobStore(max_entries=2)
    store.put(_job("a"))
    store.put(_job("b"))
    store.put(_job("c"))  # เกินความจุ → "a" (เก่าสุด) ถูกทิ้ง
    assert store.get("a") is None
    assert store.get("b") is not None
    assert store.get("c") is not None
    assert len(store) == 2


def test_ttl_sweeps_expired_entries():
    clock = FakeClock()
    store = JobStore(ttl_seconds=100, clock=clock)
    store.put(_job("old"))

    clock.now = 101  # เลยอายุ TTL
    assert store.get("old") is None
    assert len(store) == 0


def test_ttl_keeps_fresh_entries():
    clock = FakeClock()
    store = JobStore(ttl_seconds=100, clock=clock)
    store.put(_job("fresh"))

    clock.now = 99  # ยังไม่หมดอายุ
    assert store.get("fresh") is not None


def test_update_does_not_reset_ttl():
    clock = FakeClock()
    store = JobStore(ttl_seconds=100, clock=clock)
    store.put(_job("chk"))

    clock.now = 50
    store.update("chk", status=CheckStatus.COMPLETED)  # ไม่รีเซ็ตอายุ
    clock.now = 101  # นับจากตอนสร้าง (t=0) → หมดอายุแล้ว
    assert store.get("chk") is None


def test_ttl_zero_means_no_expiry():
    clock = FakeClock()
    store = JobStore(ttl_seconds=0, clock=clock)
    store.put(_job("immortal"))
    clock.now = 10**9
    assert store.get("immortal") is not None
