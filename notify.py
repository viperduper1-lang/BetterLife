#!/usr/bin/env python3
"""BetterLife — remindere de mese și antrenament, trimise ca push pe iPhone (ntfy).

Moduri:
  python notify.py --send-due     # trimite reminderele scadente acum (folosit de GitHub Actions)
  python notify.py --test lunch    # trimite ACUM reminderul unui eveniment (test), ignoră ora/starea
  python notify.py --dry-run       # arată ce s-ar trimite acum, fără să trimită
  python notify.py --list          # arată programul zilei + grupa musculară de azi
"""
import argparse
import datetime
import json
import os
import sys
import urllib.request

import core

# Consola Windows folosește implicit cp1252 și nu poate afișa emoji/diacritice.
# Forțăm UTF-8 la afișare (trimiterea push-ului e UTF-8 oricum, e neafectată).
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

STATE_PATH = core.ROOT / "state.json"
DEFAULT_TOPIC_HINT = "schimba-ma"


class SafeDict(dict):
    """Lasă {placeholder} necunoscut neatins în loc să dea eroare."""
    def __missing__(self, key):
        return "{" + key + "}"


def render(cfg, key, local_dt):
    """Întoarce (title, body, tags, priority) pentru un eveniment."""
    if key == "workout":
        workout = core.load_workout(cfg)
        muscle = core.muscle_for(cfg, local_dt.date())
        details = workout.get("details", {}).get(muscle, "")
        is_rest = str(muscle).strip().lower().startswith("repaus")
        template = workout.get("rest_message" if is_rest else "message", "")
        ctx = SafeDict(muscle=muscle,
                       treadmill_kcal=workout.get("treadmill_kcal_goal"),
                       cardio=workout.get("cardio", ""),
                       details=details)
        title = f"{workout.get('title', '🏋️ Antrenament')} — {muscle}"
        return title, template.format_map(ctx), "weight_lifter", 4

    if key == "day_close":
        day_close = cfg["day_close"]
        tomorrow = core.muscle_for(cfg, local_dt.date() + datetime.timedelta(days=1))
        ctx = SafeDict(tomorrow_muscle=tomorrow)
        return (day_close.get("title", "✅ Ziua închisă"),
                day_close.get("message", "").format_map(ctx),
                day_close.get("tags", "white_check_mark"),
                day_close.get("priority", 3))

    for meal in cfg.get("meals", []):
        if meal["key"] == key:
            ctx = SafeDict(kcal_cap=meal.get("kcal_cap"),
                           options=meal.get("options", ""),
                           daily_kcal_cap=cfg.get("daily_kcal_cap"))
            return (meal.get("title", key),
                    meal.get("message", "").format_map(ctx),
                    meal.get("tags", ""),
                    meal.get("priority", 3))

    return key, "", "", 3


def _icon_url(cfg):
    """URL-ul iconiței pentru notificare (brandare premium pe telefon)."""
    explicit = os.environ.get("NTFY_ICON") or (cfg.get("ntfy", {}) or {}).get("icon")
    if explicit:
        return explicit
    # În GitHub Actions putem construi automat adresa spre icon.png din repo.
    repo = os.environ.get("GITHUB_REPOSITORY")
    if repo:
        branch = os.environ.get("GITHUB_REF_NAME", "main")
        return f"https://raw.githubusercontent.com/{repo}/{branch}/icon.png"
    return None


def send(cfg, title, body, tags, priority):
    """Trimite un push premium prin ntfy (JSON: diacritice/emoji + iconiță + markdown)."""
    topic = os.environ.get("NTFY_TOPIC") or cfg.get("ntfy", {}).get("topic")
    if not topic:
        raise RuntimeError("Niciun topic ntfy setat (config.yaml sau env NTFY_TOPIC).")
    if DEFAULT_TOPIC_HINT in topic:
        print("  ⚠  Folosești topicul implicit — schimbă-l în config.yaml cu unul al tău!",
              file=sys.stderr)
    server = cfg.get("ntfy", {}).get("server", "https://ntfy.sh").rstrip("/")

    payload = {"topic": topic, "title": title, "message": body,
               "priority": int(priority or 3), "markdown": True}
    if tags:
        parts = tags.split(",") if isinstance(tags, str) else tags
        payload["tags"] = [t.strip() for t in parts if str(t).strip()]
    icon = _icon_url(cfg)
    if icon:
        payload["icon"] = icon

    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        server, data=data, method="POST",
        headers={"Content-Type": "application/json; charset=utf-8"})
    with urllib.request.urlopen(request, timeout=15) as response:
        return response.status


def load_state():
    if STATE_PATH.exists():
        try:
            return json.loads(STATE_PATH.read_text(encoding="utf-8"))
        except (ValueError, OSError):
            pass
    return {"date": "", "sent": []}


def save_state(state):
    STATE_PATH.write_text(json.dumps(state, ensure_ascii=False, indent=2),
                          encoding="utf-8")


def due_now(cfg, now):
    """Cheile evenimentelor scadente acum (în fereastra de toleranță)."""
    grace = int(cfg.get("grace_minutes", 45))
    mins_now = now.hour * 60 + now.minute
    return [(key, tstr) for key, mins, tstr in core.events(cfg)
            if mins <= mins_now <= mins + grace]


def run_send_due(cfg):
    now = core.now_local(cfg)
    today = now.date().isoformat()
    state = load_state()
    if state.get("date") != today:
        state = {"date": today, "sent": []}

    sent = []
    for key, _ in due_now(cfg, now):
        if key in state["sent"]:
            continue
        title, body, tags, priority = render(cfg, key, now)
        if not body:
            continue
        try:
            send(cfg, title, body, tags, priority)
            state["sent"].append(key)
            sent.append(key)
            print(f"Trimis: {key} → {title}")
        except Exception as exc:  # noqa: BLE001
            print(f"EROARE la {key}: {exc}", file=sys.stderr)

    save_state(state)
    if not sent:
        print("Nimic de trimis acum.")
    return sent


def run_test(cfg, key):
    valid = {k for k, _, _ in core.events(cfg)}
    if key not in valid:
        sys.exit(f"Cheie necunoscută: {key}. Valide: {', '.join(sorted(valid))}")
    now = core.now_local(cfg)
    title, body, tags, priority = render(cfg, key, now)
    send(cfg, title, body, tags, priority)
    print(f"Test trimis: {key} → {title}\n  {body}")


def run_dry(cfg):
    now = core.now_local(cfg)
    print(f"Ora locală acum: {now:%Y-%m-%d %H:%M} ({cfg.get('timezone')})")
    pending = due_now(cfg, now)
    if not pending:
        print("Nimic scadent acum.")
        return
    for key, tstr in pending:
        title, body, _, _ = render(cfg, key, now)
        print(f"  [{tstr}] {key}: {title} — {body}")


def run_list(cfg):
    now = core.now_local(cfg)
    print(f"Program (ore locale, {cfg.get('timezone')}):")
    for key, _, tstr in core.events(cfg):
        title, body, _, _ = render(cfg, key, now)
        print(f"  {tstr}  {key:10s} {title}")
        print(f"          {body}")
    print(f"\nGrupa de azi:  {core.muscle_for(cfg, now.date())}")
    print(f"Grupa de mâine: {core.muscle_for(cfg, now.date() + datetime.timedelta(days=1))}")
    print(f"Total kcal/zi: {cfg.get('daily_kcal_cap')}")


def main():
    parser = argparse.ArgumentParser(description="BetterLife reminders (ntfy)")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--send-due", action="store_true",
                       help="trimite reminderele scadente (default)")
    group.add_argument("--test", metavar="KEY",
                       help="trimite acum reminderul unui eveniment (test)")
    group.add_argument("--dry-run", action="store_true",
                       help="arată ce s-ar trimite acum, fără să trimită")
    group.add_argument("--list", action="store_true",
                       help="arată programul zilei")
    args = parser.parse_args()

    cfg = core.load_config()
    if args.test:
        run_test(cfg, args.test)
    elif args.dry_run:
        run_dry(cfg)
    elif args.list:
        run_list(cfg)
    else:
        run_send_due(cfg)


if __name__ == "__main__":
    main()
