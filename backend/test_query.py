from db.queries import select_ecg_waveforms
from datetime import datetime

# The data range the user is requesting
start = datetime.fromisoformat("2026-06-24T06:57:29")
end = datetime.fromisoformat("2026-06-24T06:59:29")

print(f"Querying for: {start} to {end}")

rows = select_ecg_waveforms(start, end)
print(f"Returned {len(rows)} rows")
if rows:
    print(f"First row: {rows[0]}")
    print(f"Last row: {rows[-1]}")
