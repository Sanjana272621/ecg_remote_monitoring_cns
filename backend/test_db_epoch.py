from datetime import datetime, timezone
dt = datetime(2026, 6, 23, 15, 00, 0, tzinfo=timezone.utc)
print(int(dt.timestamp() * 1000))