"""One-time Slack post of every upcoming event in docs/events.json, one message per month.

Reads the already-filtered snapshot, so it matches the calendar exactly. Run by the manual
"Post full event list to Slack" workflow. Does not touch the scraper or change tracking.
"""
import datetime as dt
import json
import os
import sys
import time
import urllib.request

from sdic_events_to_ics import page_url_from_env, slack_line

LIMIT = 35  # events per message, to stay well under Slack's text limits


def post(url, text):
    req = urllib.request.Request(url, data=json.dumps({"text": text}).encode(),
                                 headers={"Content-type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode()


def main():
    url = os.environ.get("SLACK_WEBHOOK_URL", "")
    if not url:
        sys.exit("SLACK_WEBHOOK_URL is not set.")
    today = dt.date.today().isoformat()
    events = [e for e in json.load(open("docs/events.json"))["events"] if e["end"] >= today]
    events.sort(key=lambda e: (e["start"], e["title"]))
    months = {}
    for e in events:
        months.setdefault(e["start"][:7], []).append(e)
    page = page_url_from_env()
    messages = [f"*Upcoming SDIC events for the troop* ({len(events)} total, filtered to BSA Scouts, Training and "
                f"Council / District). Posted once so the channel starts with the full list; after this, only "
                f"changes are posted." + (f"\n<{page}|Full calendar page>" if page else "")]
    for ym, evs in months.items():
        label = dt.date.fromisoformat(ym + "-01").strftime("%B %Y")
        for i in range(0, len(evs), LIMIT):
            part = evs[i:i + LIMIT]
            more = f" (cont.)" if i else ""
            messages.append(f"*{label}{more}*\n" + "\n".join(slack_line(e) for e in part))
    for m in messages:
        print(post(url, m))
        time.sleep(1.2)  # Slack allows about one message per second per webhook
    print(f"Posted {len(messages)} messages, {len(events)} events.")


if __name__ == "__main__":
    main()
