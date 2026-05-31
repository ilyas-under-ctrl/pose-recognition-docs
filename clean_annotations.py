import csv
from pathlib import Path

from annotation_tool import EVENTS_CSV, EVENT_HEADERS, SEGMENTS_CSV, SEGMENT_HEADERS


def read_csv(path, headers):
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8") as handle:
        return [{header: row.get(header, "") for header in headers} for row in csv.DictReader(handle)]


def write_csv(path, headers, rows):
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)


def clean_segments():
    seen = set()
    cleaned = []
    for row in read_csv(SEGMENTS_CSV, SEGMENT_HEADERS):
        key = tuple(row.get(header, "") for header in SEGMENT_HEADERS)
        if key in seen:
            continue
        seen.add(key)
        cleaned.append(row)
    write_csv(SEGMENTS_CSV, SEGMENT_HEADERS, cleaned)
    return len(cleaned)


def clean_events():
    by_key = {}
    order = []
    for row in read_csv(EVENTS_CSV, EVENT_HEADERS):
        video_id = row.get("video_id", "")
        event_type = row.get("event_type", "")
        role = row.get("event_role", "")
        if event_type == "no_danger_event":
            role = "no_danger"
        elif not role:
            role = "risk_onset"
        key = (video_id, role)
        if key not in by_key:
            order.append(key)
        by_key[key] = row
    cleaned = [by_key[key] for key in order if key[0]]
    write_csv(EVENTS_CSV, EVENT_HEADERS, cleaned)
    return len(cleaned)


def main():
    segment_count = clean_segments()
    event_count = clean_events()
    print(f"segments={segment_count}")
    print(f"events={event_count}")


if __name__ == "__main__":
    main()
