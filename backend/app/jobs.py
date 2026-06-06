"""In-memory job store สำหรับผลการตรวจ (MVP — ยังไม่ใช้ DB).

เก็บผลตรวจไว้ใน process เดียว มี 2 กลไกกันหน่วยความจำโตไม่จำกัด:
  - TTL       ผลตรวจอยู่ได้ไม่เกิน JOB_TTL_SECONDS นับจากตอนสร้าง แล้วถูกกวาดทิ้ง
  - ความจุ    เก็บได้ไม่เกิน JOB_MAX_ENTRIES รายการ เกินกว่านั้นทิ้งตัวเก่าสุด (FIFO)

กวาดของหมดอายุแบบ lazy ทุกครั้งที่ put/get จึงไม่ต้องมี background task แยก
thread-safe ด้วย Lock เผื่อ background task รันคนละ thread

ค่า TTL/ความจุปรับได้ด้วย env (ดู .env.example) — default พอสำหรับ demo
"""

from __future__ import annotations

import os
import threading
import time
from collections import OrderedDict
from collections.abc import Callable
from dataclasses import dataclass

from app.schemas import CheckResult

JOB_TTL_SECONDS = int(os.getenv("JOB_TTL_SECONDS", str(60 * 60)))  # 1 ชั่วโมง
JOB_MAX_ENTRIES = int(os.getenv("JOB_MAX_ENTRIES", "1000"))


@dataclass
class _Entry:
    created_at: float
    job: CheckResult


class JobStore:
    """เก็บผลตรวจในหน่วยความจำ มี TTL + จำกัดจำนวน (กันหน่วยความจำรั่ว).

    clock แยกออกมาเป็น parameter เพื่อให้เทสต์ TTL ได้โดยไม่ต้อง sleep จริง
    """

    def __init__(
        self,
        ttl_seconds: int = JOB_TTL_SECONDS,
        max_entries: int = JOB_MAX_ENTRIES,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._ttl = ttl_seconds
        self._max = max_entries
        self._clock = clock
        self._entries: OrderedDict[str, _Entry] = OrderedDict()
        self._lock = threading.Lock()

    def put(self, job: CheckResult) -> None:
        """เพิ่ม/แทนที่ผลตรวจตาม check_id แล้วกวาดของหมดอายุ + บังคับความจุ."""
        with self._lock:
            now = self._clock()
            self._sweep(now)
            self._entries[job.check_id] = _Entry(created_at=now, job=job)
            self._entries.move_to_end(job.check_id)
            self._evict()

    def get(self, check_id: str) -> CheckResult | None:
        """คืนผลตรวจ หรือ None ถ้าไม่พบ/หมดอายุแล้ว."""
        with self._lock:
            self._sweep(self._clock())
            entry = self._entries.get(check_id)
            return entry.job if entry else None

    def update(self, check_id: str, **fields: object) -> CheckResult | None:
        """อัปเดตฟิลด์ของผลตรวจแบบ read-modify-write (ไม่รีเซ็ต TTL).

        คืน None ถ้า job ถูกกวาด/ไม่พบแล้ว (เช่นโดน evict ระหว่างประมวลผล)
        """
        with self._lock:
            entry = self._entries.get(check_id)
            if entry is None:
                return None
            entry.job = entry.job.model_copy(update=fields)
            return entry.job

    def __len__(self) -> int:
        with self._lock:
            return len(self._entries)

    # --- internal: เรียกใต้ lock เท่านั้น ---

    def _sweep(self, now: float) -> None:
        """ทิ้งรายการที่อายุเกิน TTL (ttl <= 0 = ไม่หมดอายุ)."""
        if self._ttl <= 0:
            return
        cutoff = now - self._ttl
        stale = [cid for cid, e in self._entries.items() if e.created_at < cutoff]
        for cid in stale:
            del self._entries[cid]

    def _evict(self) -> None:
        """ทิ้งตัวเก่าสุด (insert ก่อน) จนเหลือไม่เกินความจุ."""
        while len(self._entries) > self._max:
            self._entries.popitem(last=False)
