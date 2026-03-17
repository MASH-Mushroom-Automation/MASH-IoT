"""M.A.S.H. IoT - Sensor Aggregator

In-memory per-hour accumulator that writes to one Firebase path:

  - historical_aggregates/{device_id}/{room}/{YYYY-MM}/{DD}/{HH:00}
      Flushed once per UTC hour (and on shutdown) with per-bucket stats:
      avg/min/max for temp, humidity, CO₂ + sample_count + first/last timestamp.

Real-time live readings are handled separately by main.py which already writes
``devices/{device_id}/latest_reading`` on every incoming sensor reading.

This schema is dramatically cheaper in RTDB bandwidth and read latency compared
to the raw `sensor_data/{device_id}/{room}/{timestamp_key}` writes.

Usage::

    from cloud.sensor_aggregator import SensorAggregator

    agg = SensorAggregator(firebase_sync=firebase, device_id="MASH-B2-CAL26-CE637C")

    # Call on every reading (thread-safe)
    agg.add_reading("fruiting", temp=23.5, hum=85.0, co2=800)
    agg.add_reading("spawning", temp=24.0, hum=90.0, co2=1200)

    # Call on shutdown to persist the partial current-hour bucket
    agg.flush_all()
"""

import time
import threading
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Internal bucket
# ---------------------------------------------------------------------------

class _HourBucket:
    """Accumulates sensor readings within a single UTC hour."""

    def __init__(self) -> None:
        self.temps: List[float] = []
        self.hums: List[float] = []
        self.co2s: List[float] = []
        self.first_ts: Optional[float] = None
        self.last_ts: Optional[float] = None

    def add(
        self,
        temp: Optional[float],
        hum: Optional[float],
        co2: Optional[float],
        ts: float,
    ) -> None:
        if temp is not None:
            self.temps.append(float(temp))
        if hum is not None:
            self.hums.append(float(hum))
        if co2 is not None:
            self.co2s.append(float(co2))
        if self.first_ts is None:
            self.first_ts = ts
        self.last_ts = ts

    def to_dict(self) -> Dict:
        def avg(lst: List[float]) -> Optional[float]:
            return round(sum(lst) / len(lst), 2) if lst else None

        def mn(lst: List[float]) -> Optional[float]:
            return round(min(lst), 2) if lst else None

        def mx(lst: List[float]) -> Optional[float]:
            return round(max(lst), 2) if lst else None

        n = max(len(self.temps), len(self.hums), len(self.co2s), 0)
        return {
            "avg_temp": avg(self.temps),
            "min_temp": mn(self.temps),
            "max_temp": mx(self.temps),
            "avg_hum": avg(self.hums),
            "min_hum": mn(self.hums),
            "max_hum": mx(self.hums),
            "avg_co2": avg(self.co2s),
            "min_co2": mn(self.co2s),
            "max_co2": mx(self.co2s),
            "sample_count": n,
            "first_ts": self.first_ts,
            "last_ts": self.last_ts,
        }

    @property
    def is_empty(self) -> bool:
        return not self.temps and not self.hums and not self.co2s


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _hour_label(ts: float):
    """Return (year_month, day, hour_key) for a UNIX timestamp (UTC)."""
    dt = datetime.fromtimestamp(ts, tz=timezone.utc)
    return (
        dt.strftime("%Y-%m"),   # "2026-03"
        f"{dt.day:02d}",        # "11"
        f"{dt.hour:02d}:00",    # "14:00"
    )


# ---------------------------------------------------------------------------
# Public class
# ---------------------------------------------------------------------------

class SensorAggregator:
    """
    Thread-safe in-memory sensor aggregator.

    On every call to :meth:`add_reading`:
      1. Accumulates the value into the current UTC-hour bucket.
      2. If the UTC hour has rolled over since the last reading for this room,
         the completed bucket is serialised and pushed to
         ``historical_aggregates/{device_id}/{room}/{YYYY-MM}/{DD}/{HH:00}``
         in a background daemon thread (non-blocking).

    Call :meth:`flush_all` on shutdown to persist the partial bucket for the
    current (incomplete) hour so no data is lost.
    """

    def __init__(self, firebase_sync, device_id: str) -> None:
        self.firebase = firebase_sync
        self.device_id = device_id
        self._lock = threading.Lock()

        # Per-room state
        self._buckets: Dict[str, _HourBucket] = {}
        # room → "YYYY-MM/DD/HH:00"
        self._labels: Dict[str, str] = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def add_reading(
        self,
        room: str,
        temp: Optional[float],
        hum: Optional[float],
        co2: Optional[float],
        ts: Optional[float] = None,
    ) -> None:
        """Record a single sensor reading for one room."""
        ts = ts or time.time()
        year_month, day, hour_key = _hour_label(ts)
        new_label = f"{year_month}/{day}/{hour_key}"

        with self._lock:
            old_label = self._labels.get(room)

            # Hour boundary crossed → flush old bucket asynchronously
            if old_label and old_label != new_label:
                old_bucket = self._buckets.get(room)
                if old_bucket and not old_bucket.is_empty:
                    self._async_flush(room, old_label, old_bucket.to_dict())

            # Rotate bucket if needed
            if room not in self._labels or self._labels[room] != new_label:
                self._buckets[room] = _HourBucket()
                self._labels[room] = new_label

            self._buckets[room].add(temp, hum, co2, ts)

    def flush_all(self) -> None:
        """Flush all partial buckets synchronously.  Call this on shutdown."""
        with self._lock:
            items = list(self._labels.items())

        for room, label in items:
            with self._lock:
                bucket = self._buckets.get(room)
                if not bucket or bucket.is_empty:
                    continue
                data = bucket.to_dict()

            year_month, day, hour_key = label.split("/")
            try:
                self.firebase.push_hourly_aggregate(
                    self.device_id, room, year_month, day, hour_key, data
                )
                logger.info(
                    "[AGG] ✅ Final flush: %s %s (%d samples)",
                    room, label, data.get("sample_count", 0),
                )
            except Exception as exc:
                logger.error("[AGG] ❌ Final flush failed: %s %s: %s", room, label, exc)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _async_flush(self, room: str, label: str, data: Dict) -> None:
        """Flush a completed bucket in a background daemon thread."""
        year_month, day, hour_key = label.split("/")
        threading.Thread(
            target=self._do_flush,
            args=(room, year_month, day, hour_key, data),
            daemon=True,
        ).start()

    def _do_flush(
        self, room: str, year_month: str, day: str, hour_key: str, data: Dict
    ) -> None:
        try:
            self.firebase.push_hourly_aggregate(
                self.device_id, room, year_month, day, hour_key, data
            )
            logger.info(
                "[AGG] ✅ Flushed %s %s/%s/%s (%d samples)",
                room, year_month, day, hour_key, data.get("sample_count", 0),
            )
        except Exception as exc:
            logger.error(
                "[AGG] ❌ Flush failed %s %s/%s/%s: %s",
                room, year_month, day, hour_key, exc,
            )
