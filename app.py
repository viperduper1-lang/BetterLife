#!/usr/bin/env python3
"""BetterLife — aplicație desktop (interfață web premium prin pywebview).

Secțiuni: Azi · Frigider · Plan 7 zile · Calculator · Setări.
Rulează:  python app.py       |  Împachetare .exe: build_exe.bat
"""
import os
import sys

import core
import foods as _foods

# --selftest rulează logica fără interfață (verificare automată, fără fereastră).
if "--selftest" in sys.argv:
    cfg = core.load_config()
    core.clear_pantry()
    core.set_pantry_amount("piept_pui", 500, "g")
    core.set_pantry_amount("ou", 6, "buc")
    core.set_pantry_amount("orez", 400, "g")
    plan = core.generate_plan(cfg, seed=1)
    assert len(plan["days"]) == 7, "planul nu are 7 zile"
    assert "workout" in plan["days"][0], "lipsește antrenamentul din zi"
    assert plan["weekly_budget"] > 0
    core.clear_pantry()
    day = "1999-01-01"
    core.clear_day(day)
    core.add_entry(day, "Test", "100 g", 250)
    assert core.total_for(day) == 250
    core.clear_day(day)
    print(f"selftest OK - foods={len(_foods.FOODS)}, "
          f"workout={len(core.load_workout(cfg)['schedule'])} zile, "
          f"plan_total={plan['weekly_total']}/{plan['weekly_budget']}")
    sys.exit(0)

import webview


class Api:
    """Interfața Python apelată din JavaScript (window.pywebview.api.*)."""

    def __init__(self):
        self.cfg = core.load_config()
        self._window = None

    # ------------------------------------------------ helpers interne
    def _reload_cfg(self):
        try:
            self.cfg = core.load_config()
        except Exception:  # noqa: BLE001
            pass

    def _today(self):
        cfg = self.cfg
        day = core.today_str(cfg)
        now = core.now_local(cfg)
        cap = core.today_cap(cfg)
        eaten = core.total_for(day)
        return {
            "date": day,
            "weekday": core.WEEKDAY_LABELS[core.WEEKDAYS[now.weekday()]],
            "muscle": core.muscle_for(cfg, now.date()),
            "cap": cap, "eaten": eaten, "remaining": cap - eaten,
            "entries": core.entries_for(day),
        }

    def _int(self, value, fallback=0):
        try:
            return max(0, int(round(float(str(value).replace(",", ".")))))
        except (TypeError, ValueError):
            return fallback

    # ------------------------------------------------ API public
    def get_state(self):
        self._reload_cfg()
        settings = core.load_settings(self.cfg)
        return {
            "today": self._today(),
            "settings": settings,
            "weekday_order": core.WEEKDAYS,
            "weekday_labels": core.WEEKDAY_LABELS,
            "weekly_budget": sum(settings["day_caps"].values()),
            "foods": _foods.FOODS,
            "categories": [{"key": k, "label": l, "emoji": e}
                           for k, l, e in _foods.CATEGORIES],
            "pantry": core.load_pantry_full(),
            "plan": core.load_plan(),
            "workout": core.load_workout(self.cfg),
            "muscle_groups": core.MUSCLE_GROUPS,
            "workout_conflicts": core.workout_conflicts(),
        }

    # ------------------------------------------------ frigider (cantități)
    def set_pantry_amount(self, key, qty, unit):
        items = core.set_pantry_amount(key, qty, unit)
        return {"pantry": items, "count": len(items)}

    def remove_pantry(self, key):
        items = core.remove_pantry(key)
        return {"pantry": items, "count": len(items)}

    def clear_pantry(self):
        core.clear_pantry()
        return {"pantry": {}, "count": 0}

    # ------------------------------------------------ antrenament
    def set_workout_day(self, weekday, muscle):
        workout = core.set_workout_day(weekday, muscle)
        return {"workout": workout, "conflicts": core.workout_conflicts(workout)}

    def set_cardio(self, text):
        workout = core.set_cardio(text)
        return {"workout": workout, "conflicts": core.workout_conflicts(workout)}

    def auto_arrange_workout(self):
        workout = core.auto_arrange_workout()
        return {"workout": workout, "conflicts": core.workout_conflicts(workout)}

    def generate_plan(self):
        return core.generate_plan(self.cfg)

    def set_daily_cap(self, value):
        settings = core.set_daily_cap(self.cfg, self._int(value, 1800))
        return {"settings": settings,
                "weekly_budget": sum(settings["day_caps"].values()),
                "today": self._today()}

    def set_day_cap(self, weekday, value):
        settings = core.set_day_cap(self.cfg, weekday, self._int(value, 1800))
        return {"settings": settings,
                "weekly_budget": sum(settings["day_caps"].values()),
                "today": self._today()}

    def add_entry(self, name, amount, kcal):
        core.add_entry(core.today_str(self.cfg), (name or "Produs").strip(),
                       (amount or "").strip(), self._int(kcal))
        return self._today()

    def remove_entry(self, index):
        core.remove_entry(core.today_str(self.cfg), self._int(index))
        return self._today()

    def clear_day(self):
        core.clear_day(core.today_str(self.cfg))
        return self._today()

    def open_config(self):
        core.ensure_config()
        try:
            os.startfile(str(core.CONFIG_PATH))  # Windows
        except AttributeError:
            import subprocess
            subprocess.Popen(["xdg-open", str(core.CONFIG_PATH)])
        except Exception:  # noqa: BLE001
            return False
        return True

    # ------------------------------------------------ GitHub
    def github_status(self):
        return core.git_status()

    def github_sync(self):
        return core.git_sync()

    def github_setup(self, url):
        return core.git_setup(url)


def _read_ui() -> str:
    path = core._bundled("ui.html")
    if not path.exists():
        path = core.ROOT / "ui.html"
    return path.read_text(encoding="utf-8")


def main():
    core.ensure_config()
    core.ensure_workout()
    api = Api()
    window = webview.create_window(
        "BetterLife", html=_read_ui(), js_api=api,
        width=1140, height=800, min_size=(920, 640),
        background_color="#0f1420",
    )
    api._window = window
    webview.start()


if __name__ == "__main__":
    main()
