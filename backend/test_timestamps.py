from datetime import datetime

# Convert datetime to epoch milliseconds like the frontend does
dt_str = "2026-06-24T11:20:00"
dt = datetime.fromisoformat(dt_str)
epoch_ms = int(dt.timestamp() * 1000)
print(f"{dt_str} -> {epoch_ms} ms")

# A 30-second range
start_ms = epoch_ms
end_ms = epoch_ms + 30000
print(f"30s range: {start_ms} to {end_ms}")

# Now test the query with these timestamps
start_dt = datetime.fromtimestamp(start_ms / 1000.0)
end_dt = datetime.fromtimestamp(end_ms / 1000.0)
print(f"As datetime: {start_dt} to {end_dt}")

from db.queries import select_ecg_waveforms
rows = select_ecg_waveforms(start_dt, end_dt)
print(f"Query returned {len(rows)} rows")
