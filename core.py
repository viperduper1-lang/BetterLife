#!/usr/bin/env python3
"""BetterLife — logică partajată: config, program zilnic și jurnal de calorii.

Folosit atât de aplicația desktop (app.py), cât și de scriptul de
notificări din cloud (notify.py). Un singur loc pentru datele comune.
"""
import datetime
import json
import random
import shutil
import sys
from pathlib import Path

try:
    from zoneinfo import ZoneInfo
except ImportError:  # pragma: no cover
    ZoneInfo = None

import yaml

import foods as _foods

WEEKDAYS = ["monday", "tuesday", "wednesday", "thursday",
            "friday", "saturday", "sunday"]

WEEKDAY_LABELS = {
    "monday": "Luni", "tuesday": "Marți", "wednesday": "Miercuri",
    "thursday": "Joi", "friday": "Vineri", "saturday": "Sâmbătă",
    "sunday": "Duminică",
}


def app_root() -> Path:
    """Folderul unde stau datele. Lângă .exe când e împachetat, altfel lângă sursă."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


ROOT = app_root()
CONFIG_PATH = ROOT / "config.yaml"
LOG_PATH = ROOT / "food_log.json"


def _bundled(name: str) -> Path:
    """Calea unui fișier împachetat în .exe (PyInstaller), altfel lângă sursă."""
    base = getattr(sys, "_MEIPASS", None)
    return (Path(base) / name) if base else (ROOT / name)


def ensure_config():
    """La prima rulare a .exe-ului, creează config.yaml din copia împachetată."""
    if not CONFIG_PATH.exists():
        src = _bundled("config.yaml")
        if src.exists() and src.resolve() != CONFIG_PATH.resolve():
            shutil.copy(src, CONFIG_PATH)


# ================================================================
#  ANTRENAMENT (workout.json — editabil din app, trimis la cloud)
# ================================================================
WORKOUT_PATH = ROOT / "workout.json"

MUSCLE_GROUPS = ["Piept", "Spate", "Picioare", "Umeri", "Biceps", "Triceps",
                 "Abdomen", "Full body", "Repaus"]

_WORKOUT_DEFAULT = {
    "reminder_time": "19:45",
    "title": "🏋️ Antrenament",
    "treadmill_kcal_goal": 300,
    "cardio": "🏃 Bandă 30 min (~300 kcal)",
    "schedule": {
        "monday": "Biceps", "tuesday": "Triceps", "wednesday": "Piept",
        "thursday": "Spate", "friday": "Picioare", "saturday": "Umeri",
        "sunday": "Repaus",
    },
    "details": {
        "Piept": "gantere: 4x10 împins + 3x12 flotări",
        "Spate": "gantere: 4x10 ramat + 3x12 pullover",
        "Picioare": "genuflexiuni 4x12 + fandări 3x12",
        "Umeri": "gantere: 4x12 împins + 3x15 ridicări laterale",
        "Biceps": "gantere: 4x12 curl + 3x12 hammer",
        "Triceps": "gantere: 4x12 extensii + 3x12 kickback",
        "Abdomen": "crunch 4x20 + planșă 3x45s",
        "Full body": "circuit total: 3 ture, 8 exerciții",
        "Repaus": "",
    },
    "message": "Azi: {muscle}. {details}. Cardio: {cardio}. Goal bandă ~{treadmill_kcal} kcal.",
    "rest_message": "Azi repaus pentru mușchi — dar cardio rămâne: {cardio}.",
}


def ensure_workout():
    """Creează workout.json (din copia împachetată sau din default) dacă lipsește."""
    if not WORKOUT_PATH.exists():
        src = _bundled("workout.json")
        if src.exists() and src.resolve() != WORKOUT_PATH.resolve():
            shutil.copy(src, WORKOUT_PATH)
        else:
            _write_json(WORKOUT_PATH, _WORKOUT_DEFAULT)


def load_workout(cfg=None) -> dict:
    ensure_workout()
    data = _read_json(WORKOUT_PATH, None)
    if not isinstance(data, dict):
        data = dict(_WORKOUT_DEFAULT)
    # completează câmpurile lipsă din default
    merged = dict(_WORKOUT_DEFAULT)
    merged.update(data)
    for key in ("schedule", "details"):
        base = dict(_WORKOUT_DEFAULT[key])
        base.update(data.get(key) or {})
        merged[key] = base
    return merged


def save_workout(workout: dict):
    _write_json(WORKOUT_PATH, workout)


def set_workout_day(weekday: str, muscle: str) -> dict:
    workout = load_workout()
    if weekday in WEEKDAYS:
        workout["schedule"][weekday] = muscle
        save_workout(workout)
    return workout


def set_cardio(text: str) -> dict:
    workout = load_workout()
    workout["cardio"] = text
    save_workout(workout)
    return workout


def workout_conflicts(workout=None) -> list:
    """Zilele care au aceeași grupă (ne-repaus) ca ziua precedentă — de evitat."""
    workout = workout or load_workout()
    schedule = workout.get("schedule", {})
    conflicts = []
    for i in range(1, len(WEEKDAYS)):
        prev, cur = schedule.get(WEEKDAYS[i - 1]), schedule.get(WEEKDAYS[i])
        if cur and cur == prev and not str(cur).lower().startswith("repaus"):
            conflicts.append(WEEKDAYS[i])
    return conflicts


def auto_arrange_workout() -> dict:
    """Rearanjează grupele ca să nu apară două zile la rând aceeași (cardio rămâne zilnic)."""
    workout = load_workout()
    schedule = workout.get("schedule", {})
    groups = [g for g in (schedule.get(wd) for wd in WEEKDAYS)
              if g and not str(g).lower().startswith("repaus")]
    seen, distinct = set(), []
    for g in groups:
        if g not in seen:
            seen.add(g)
            distinct.append(g)
    if not distinct:
        distinct = ["Piept", "Spate", "Picioare", "Umeri", "Biceps", "Triceps"]
    rest_days = [wd for wd in WEEKDAYS
                 if str(schedule.get(wd, "")).lower().startswith("repaus")]
    new_schedule, idx = {}, 0
    for wd in WEEKDAYS:
        if wd in rest_days:
            new_schedule[wd] = "Repaus"
        else:
            new_schedule[wd] = distinct[idx % len(distinct)]
            idx += 1
    workout["schedule"] = new_schedule
    save_workout(workout)
    return workout


# ------------------------------------------------------------------ config
def load_config() -> dict:
    ensure_config()
    with open(CONFIG_PATH, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


# ------------------------------------------------------------------ timp
def tz_of(cfg):
    if ZoneInfo is None:
        return None
    try:
        return ZoneInfo(cfg.get("timezone", "Europe/Bucharest"))
    except Exception:  # noqa: BLE001
        return None


def now_local(cfg) -> datetime.datetime:
    tz = tz_of(cfg)
    return datetime.datetime.now(tz) if tz else datetime.datetime.now()


def today_str(cfg) -> str:
    return now_local(cfg).date().isoformat()


# ------------------------------------------------------------------ program
def parse_hhmm(value) -> int:
    hours, minutes = str(value).split(":")
    return int(hours) * 60 + int(minutes)


def muscle_for(cfg, date) -> str:
    schedule = load_workout(cfg).get("schedule", {})
    return schedule.get(WEEKDAYS[date.weekday()], "Repaus")


def events(cfg):
    """Listă de (key, minute_de_la_miezul_nopții, "HH:MM") sortată după oră."""
    result = []
    for meal in cfg.get("meals", []):
        result.append((meal["key"], parse_hhmm(meal["time"]), meal["time"]))
    workout = load_workout(cfg)
    if workout.get("reminder_time"):
        result.append(("workout", parse_hhmm(workout["reminder_time"]),
                       workout["reminder_time"]))
    day_close = cfg.get("day_close") or {}
    if day_close.get("time"):
        result.append(("day_close", parse_hhmm(day_close["time"]),
                       day_close["time"]))
    result.sort(key=lambda item: item[1])
    return result


# ------------------------------------------------------------------ jurnal calorii
def load_log() -> dict:
    if LOG_PATH.exists():
        try:
            return json.loads(LOG_PATH.read_text(encoding="utf-8"))
        except (ValueError, OSError):
            pass
    return {}


def save_log(log: dict):
    LOG_PATH.write_text(json.dumps(log, ensure_ascii=False, indent=2),
                        encoding="utf-8")


def entries_for(day: str) -> list:
    return load_log().get(day, [])


def total_for(day: str) -> int:
    return sum(int(entry.get("kcal", 0)) for entry in entries_for(day))


def daily_cap(cfg) -> int:
    return int(cfg.get("daily_kcal_cap", 0) or 0)


def remaining(cfg, day: str) -> int:
    return daily_cap(cfg) - total_for(day)


def add_entry(day: str, name: str, amount: str, kcal: float):
    log = load_log()
    log.setdefault(day, []).append({
        "name": name, "amount": amount, "kcal": int(round(kcal)),
    })
    save_log(log)


def remove_entry(day: str, index: int):
    log = load_log()
    items = log.get(day, [])
    if 0 <= index < len(items):
        items.pop(index)
        log[day] = items
        save_log(log)


def clear_day(day: str):
    log = load_log()
    if day in log:
        log[day] = []
        save_log(log)


# ================================================================
#  SETĂRI (limite kcal per zi), FRIGIDER (pantry) și PLAN 7 ZILE
# ================================================================
SETTINGS_PATH = ROOT / "settings.json"
PANTRY_PATH = ROOT / "pantry.json"
PLAN_PATH = ROOT / "plan.json"


def _read_json(path: Path, default):
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (ValueError, OSError):
            pass
    return default


def _write_json(path: Path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


# ---------------------------------------------------------- setări/limite
def load_settings(cfg) -> dict:
    base = daily_cap(cfg) or 1800
    data = _read_json(SETTINGS_PATH, {})
    dcap = int(data.get("daily_cap", base) or base)
    day_caps_in = data.get("day_caps") or {}
    caps = {wd: int(day_caps_in.get(wd, dcap) or dcap) for wd in WEEKDAYS}
    return {"daily_cap": dcap, "day_caps": caps}


def save_settings(settings: dict):
    SETTINGS_PATH.write_text(json.dumps(settings, ensure_ascii=False, indent=2),
                             encoding="utf-8")


def set_daily_cap(cfg, value: int) -> dict:
    settings = load_settings(cfg)
    old = settings["daily_cap"]
    settings["daily_cap"] = int(value)
    # zilele care erau egale cu vechiul default urmează noul default
    for wd in WEEKDAYS:
        if settings["day_caps"][wd] == old:
            settings["day_caps"][wd] = int(value)
    save_settings(settings)
    return settings


def set_day_cap(cfg, weekday: str, value: int) -> dict:
    settings = load_settings(cfg)
    if weekday in settings["day_caps"]:
        settings["day_caps"][weekday] = int(value)
        save_settings(settings)
    return settings


def day_cap_for(cfg, date) -> int:
    settings = load_settings(cfg)
    return settings["day_caps"].get(WEEKDAYS[date.weekday()], settings["daily_cap"])


def today_cap(cfg) -> int:
    return day_cap_for(cfg, now_local(cfg).date())


def remaining_today(cfg) -> int:
    return today_cap(cfg) - total_for(today_str(cfg))


def weekly_budget(cfg) -> int:
    return sum(load_settings(cfg)["day_caps"].values())


# ---------------------------------------------------------- frigider (cu cantități)
_DEFAULT_PIECE_G = 100  # grame implicite dacă un aliment n-are piece_g


def _to_grams(key: str, qty: float, unit: str) -> float:
    unit = (unit or "g").lower()
    if unit == "kg":
        return qty * 1000
    if unit == "buc":
        piece = _foods.BY_KEY.get(key, {}).get("piece_g") or _DEFAULT_PIECE_G
        return qty * piece
    return qty  # grame


def load_pantry_full() -> dict:
    """{key: {"g": grame, "q": cantitate, "u": unitate}} — pentru interfață."""
    data = _read_json(PANTRY_PATH, {"items": {}})
    items = data.get("items", {})
    result = {}
    if isinstance(items, list):  # format vechi (doar chei) → grame implicite
        for key in items:
            if key in _foods.BY_KEY:
                result[key] = {"g": 300.0, "q": 300, "u": "g"}
        return result
    for key, value in items.items():
        if key not in _foods.BY_KEY:
            continue
        if isinstance(value, dict):
            grams = float(value.get("g", 0) or 0)
            result[key] = {"g": grams, "q": value.get("q", grams), "u": value.get("u", "g")}
        else:  # număr simplu = grame
            result[key] = {"g": float(value or 0), "q": float(value or 0), "u": "g"}
    return {k: v for k, v in result.items() if v["g"] > 0}


def load_pantry() -> dict:
    """{key: grame} — pentru planificator."""
    return {k: v["g"] for k, v in load_pantry_full().items()}


def save_pantry_full(items: dict):
    _write_json(PANTRY_PATH, {"items": items})


def set_pantry_amount(key: str, qty, unit: str = "g") -> dict:
    if key not in _foods.BY_KEY:
        return load_pantry_full()
    items = load_pantry_full()
    try:
        qty = float(str(qty).replace(",", "."))
    except (TypeError, ValueError):
        qty = 0
    if qty <= 0:
        items.pop(key, None)
    else:
        items[key] = {"g": round(_to_grams(key, qty, unit)), "q": qty, "u": unit}
    save_pantry_full(items)
    return items


def remove_pantry(key: str) -> dict:
    items = load_pantry_full()
    items.pop(key, None)
    save_pantry_full(items)
    return items


def clear_pantry() -> dict:
    save_pantry_full({})
    return {}


# ---------------------------------------------------------- generator plan
# Porții tipice (grame) per categorie: (minim, maxim).
_PORTION = {
    "legume": (100, 250), "fructe": (80, 200), "cartofi": (120, 250),
    "carne": (100, 180), "peste": (100, 180), "oua": (50, 150),
    "lactate": (100, 200), "cereale": (40, 120), "nuci": (15, 40),
    "grasimi": (5, 15),
}

# Ce categorii intră în fiecare „slot" al unei mese.
_MEAL_SLOTS = {
    "breakfast": [["lactate", "cereale", "oua"], ["fructe"]],
    "snack_am": [["fructe", "lactate", "nuci"]],
    "lunch": [["carne", "peste", "oua"], ["cartofi", "cereale"], ["legume"]],
    "snack_pm": [["fructe", "lactate", "nuci"]],
    "dinner": [["carne", "peste", "oua", "lactate"], ["legume"]],
}
_DEFAULT_SLOTS = [["carne", "peste", "oua", "lactate"],
                  ["legume", "cartofi", "cereale"], ["fructe"]]


def _pick_item(slot_cats, stock, target_kcal, rng, used):
    """Alege un aliment din categoriile slotului care mai are stoc; scade din stoc."""
    pool = [_foods.BY_KEY[k] for k, grams in stock.items()
            if grams >= 20 and _foods.BY_KEY[k]["cat"] in slot_cats]
    if not pool:
        return None
    fresh = [f for f in pool if f["key"] not in used] or pool
    food = rng.choice(fresh)
    lo, hi = _PORTION.get(food["cat"], (80, 200))
    kcal_per_g = food["kcal"] / 100.0
    grams = (target_kcal / kcal_per_g) if kcal_per_g else lo
    grams = max(lo, min(hi, grams))
    grams = min(grams, stock[food["key"]])            # niciodată peste cât ai
    grams = int(round(grams / 10.0) * 10)
    if grams < 10:
        return None
    stock[food["key"]] -= grams
    return {"key": food["key"], "name": food["name"], "emoji": food["emoji"],
            "grams": grams, "kcal": int(round(grams * kcal_per_g)),
            "frozen": food["frozen"]}


def generate_plan(cfg, seed=None) -> dict:
    settings = load_settings(cfg)
    stock = load_pantry()          # {key: grame} — se consumă pe parcursul săptămânii
    initial_count = len(stock)
    workout = load_workout(cfg)
    meals_cfg = list(cfg.get("meals", []))
    rng = random.Random(seed if seed is not None else random.randrange(1_000_000))

    days = []
    for weekday in WEEKDAYS:
        cap = settings["day_caps"][weekday]
        raw_targets = [max(int(m.get("kcal_cap", 0) or 0), 1) for m in meals_cfg]
        scale = min(1.0, cap / (sum(raw_targets) or 1))

        day_meals = []
        used = set()
        for meal, raw in zip(meals_cfg, raw_targets):
            target = raw * scale
            slots = _MEAL_SLOTS.get(meal["key"], _DEFAULT_SLOTS)
            share = target / len(slots)
            items = []
            for slot_cats in slots:
                item = _pick_item(slot_cats, stock, share, rng, used)
                if item:
                    items.append(item)
                    used.add(item["key"])
            day_meals.append({
                "key": meal["key"], "title": meal.get("title", meal["key"]),
                "time": meal.get("time", ""), "target": int(round(target)),
                "items": items, "kcal": sum(it["kcal"] for it in items),
            })

        muscle = workout["schedule"].get(weekday, "Repaus")
        day_workout = {
            "muscle": muscle,
            "cardio": workout.get("cardio", ""),
            "details": workout.get("details", {}).get(muscle, ""),
            "rest": str(muscle).lower().startswith("repaus"),
        }
        days.append({
            "weekday": weekday, "label": WEEKDAY_LABELS[weekday], "cap": cap,
            "meals": day_meals, "workout": day_workout,
            "total": sum(mm["kcal"] for mm in day_meals),
        })

    plan = {
        "days": days,
        "weekly_total": sum(d["total"] for d in days),
        "weekly_budget": sum(settings["day_caps"].values()),
        "pantry_count": initial_count,
        "stock_left_g": int(round(sum(stock.values()))),
    }
    _write_json(PLAN_PATH, plan)
    return plan


def load_plan():
    return _read_json(PLAN_PATH, None)


# ================================================================
#  SINCRONIZARE GITHUB (ține notificările pe telefon actualizate)
# ================================================================
import subprocess  # noqa: E402


def _git(args, timeout=60):
    return subprocess.run(["git"] + args, cwd=str(ROOT),
                          capture_output=True, text=True, timeout=timeout)


def _git_out(args, timeout=30):
    try:
        res = _git(args, timeout=timeout)
        return res.stdout.strip() if res.returncode == 0 else ""
    except Exception:  # noqa: BLE001
        return ""


def _ensure_identity():
    if not _git_out(["config", "user.email"]):
        _git(["config", "user.email", "betterlife@local"])
    if not _git_out(["config", "user.name"]):
        _git(["config", "user.name", "BetterLife"])


def git_status() -> dict:
    """Starea legăturii cu GitHub din folderul aplicației."""
    try:
        version = _git(["--version"], timeout=10)
    except Exception:  # noqa: BLE001
        return {"installed": False}
    if version.returncode != 0:
        return {"installed": False}

    is_repo = _git_out(["rev-parse", "--is-inside-work-tree"]) == "true"
    if not is_repo:
        return {"installed": True, "is_repo": False}

    remote_url = _git_out(["remote", "get-url", "origin"])
    branch = _git_out(["rev-parse", "--abbrev-ref", "HEAD"]) or "main"
    dirty = bool(_git_out(["status", "--porcelain"]))
    return {"installed": True, "is_repo": True, "has_remote": bool(remote_url),
            "remote_url": remote_url, "branch": branch, "dirty": dirty}


def git_sync(message=None) -> dict:
    """git add + commit + push. Trimite programul actual în cloud."""
    status = git_status()
    if not status.get("installed"):
        return {"ok": False, "msg": "Git nu e instalat pe acest calculator."}
    if not status.get("is_repo"):
        return {"ok": False, "msg": "Folderul nu e conectat la GitHub. Folosește «Conectează» întâi."}
    if not status.get("has_remote"):
        return {"ok": False, "msg": "Nu există un repo GitHub legat. Conectează-l în Setări."}

    _ensure_identity()
    _git(["add", "-A"])
    msg = message or ("BetterLife: actualizare " +
                      now_local(load_config()).strftime("%Y-%m-%d %H:%M"))
    _git(["commit", "-m", msg])  # poate întoarce nonzero dacă nu e nimic nou — ok
    branch = status.get("branch", "main")
    try:
        push = _git(["push", "origin", branch], timeout=180)
    except subprocess.TimeoutExpired:
        return {"ok": False, "msg": "Push-ul a durat prea mult (posibil aștepta login în browser)."}
    if push.returncode == 0:
        return {"ok": True, "msg": "Trimis pe GitHub ✓ Notificările folosesc ultimul program."}
    return {"ok": False, "msg": "Push eșuat:\n" + (push.stderr or push.stdout or "")[-500:]}


def git_setup(remote_url: str) -> dict:
    """Conectează folderul la un repo GitHub gol și face primul push."""
    remote_url = (remote_url or "").strip()
    status = git_status()
    if not status.get("installed"):
        return {"ok": False, "msg": "Git nu e instalat pe acest calculator."}
    if not remote_url:
        return {"ok": False, "msg": "Scrie adresa repo-ului GitHub (ex: https://github.com/user/betterlife.git)."}

    if not status.get("is_repo"):
        _git(["init"])
        _git(["branch", "-M", "main"])
    if _git_out(["remote", "get-url", "origin"]):
        _git(["remote", "set-url", "origin", remote_url])
    else:
        _git(["remote", "add", "origin", remote_url])

    _ensure_identity()
    _git(["add", "-A"])
    _git(["commit", "-m", "BetterLife: configurare inițială"])
    try:
        push = _git(["push", "-u", "origin", "main"], timeout=240)
    except subprocess.TimeoutExpired:
        return {"ok": False, "msg": "Conectarea a durat prea mult (posibil aștepta login GitHub în browser)."}
    if push.returncode == 0:
        return {"ok": True, "msg": "Conectat și trimis pe GitHub ✓"}
    return {"ok": False, "msg": "Conectare eșuată:\n" + (push.stderr or push.stdout or "")[-600:]}
