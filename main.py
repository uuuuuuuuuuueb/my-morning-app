import flet as ft
from datetime import datetime, timedelta
import json
import os
import traceback

DATA_FILE = "streak_data.json"

BLACK = "#0A0A0A"
WHITE = "#FFFFFF"
GREY = "#8A8A8A"
DARK_GREY = "#1C1C1C"
CARD_BG = "#141414"
ACCENT = "#EDEDED"

DESTINATIONS = {
    "Школа": (8, 0),
    "Шарага": (9, 30),
    "Работа": (10, 0),
}


def load_data():
    default = {
        "streak": 0,
        "best_streak": 0,
        "last_wake_date": None,
        "last_wake_time": None,
        "goal_hour": 7,
        "goal_minute": 0,
    }
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            saved = json.load(f)
            default.update(saved)
    return default


def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)


def build_ui(page: ft.Page):
    page.title = "Мое Утро"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = BLACK
    page.padding = 0
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.scroll = ft.ScrollMode.AUTO

    app_data = load_data()
    state = {"dest": "Школа"}

    def card(content, padding=22):
        return ft.Container(
            content=content,
            bgcolor=CARD_BG,
            border_radius=24,
            padding=padding,
            border=ft.border.all(1, DARK_GREY),
            animate=ft.animation.Animation(250, ft.AnimationCurve.EASE_OUT),
        )

    # ---------- HERO: время до выхода ----------
    hero_time = ft.Text("--", size=46, weight=ft.FontWeight.W_900, color=WHITE)
    hero_sub = ft.Text("до выхода", size=13, color=GREY)
    hero_dest = ft.Text("Школа · к 08:00", size=13, weight=ft.FontWeight.W_600, color="#CFCFCF")

    def compute_departure(dest_name):
        now = datetime.now()
        h, m = DESTINATIONS[dest_name]
        target = now.replace(hour=h, minute=m, second=0, microsecond=0)
        if now > target:
            target += timedelta(days=1)
        diff = target - now
        hh, rem = divmod(diff.seconds, 3600)
        mm, _ = divmod(rem, 60)
        return hh, mm

    def refresh_hero():
        hh, mm = compute_departure(state["dest"])
        h, m = DESTINATIONS[state["dest"]]
        hero_time.value = f"{hh} ч {mm} мин"
        hero_dest.value = f"{state['dest']} · к {h:02d}:{m:02d}"
        page.update()

    hero_card = ft.Container(
        content=ft.Column(
            [
                ft.Row(
                    [ft.Icon(ft.icons.SCHEDULE_ROUNDED, color=BLACK, size=18),
                     ft.Text("ВРЕМЯ ВЫХОДА", size=11, weight=ft.FontWeight.W_800, color="#4A4A4A")],
                    spacing=6,
                ),
                hero_time,
                hero_sub,
                ft.Container(height=6),
                hero_dest,
            ],
            spacing=2,
        ),
        bgcolor=WHITE,
        border_radius=28,
        padding=24,
        animate=ft.animation.Animation(250, ft.AnimationCurve.EASE_OUT),
    )
    # исправляем цвета текста внутри hero (на белом фоне нужен темный текст)
    hero_time.color = BLACK
    hero_sub.color = "#555555"

    # ---------- Выбор направления (таблетки) ----------
    dest_chips_row = ft.Row(spacing=8)

    def select_dest(name):
        def handler(e):
            state["dest"] = name
            rebuild_chips()
            refresh_hero()
        return handler

    def rebuild_chips():
        dest_chips_row.controls.clear()
        for name in DESTINATIONS:
            is_selected = state["dest"] == name
            dest_chips_row.controls.append(
                ft.Container(
                    content=ft.Text(
                        name,
                        size=13,
                        weight=ft.FontWeight.W_600,
                        color=BLACK if is_selected else WHITE,
                    ),
                    bgcolor=WHITE if is_selected else DARK_GREY,
                    border_radius=100,
                    padding=ft.padding.symmetric(vertical=10, horizontal=16),
                    on_click=select_dest(name),
                    ink=True,
                    animate=ft.animation.Animation(200, ft.AnimationCurve.EASE_OUT),
                )
            )
        try:
            page.update()
        except Exception:
            pass

    # ---------- Серия и цель подъема ----------
    streak_number = ft.Text(str(app_data["streak"]), size=48, weight=ft.FontWeight.W_900, color=WHITE)
    best_streak_text = ft.Text(f"рекорд: {app_data['best_streak']}", size=12, color=GREY)
    wake_status_text = ft.Text("Ты еще не проснулся", size=13, color=GREY)

    goal_text = ft.Text(
        f"{app_data['goal_hour']:02d}:{app_data['goal_minute']:02d}",
        size=20, weight=ft.FontWeight.W_800, color=WHITE,
    )

    def adjust_goal(delta_minutes):
        def handler(e):
            total = app_data["goal_hour"] * 60 + app_data["goal_minute"] + delta_minutes
            total %= 24 * 60
            app_data["goal_hour"] = total // 60
            app_data["goal_minute"] = total % 60
            save_data(app_data)
            goal_text.value = f"{app_data['goal_hour']:02d}:{app_data['goal_minute']:02d}"
            page.update()
        return handler

    def goal_btn(icon, delta):
        return ft.Container(
            content=ft.Icon(icon, color=WHITE, size=16),
            width=32, height=32,
            bgcolor=DARK_GREY,
            border_radius=10,
            alignment=ft.alignment.center,
            on_click=adjust_goal(delta),
            ink=True,
        )

    goal_row = ft.Row(
        [
            goal_btn(ft.icons.REMOVE_ROUNDED, -15),
            ft.Container(
                content=ft.Column(
                    [ft.Text("ЦЕЛЬ ПОДЪЁМА", size=10, color=GREY, weight=ft.FontWeight.W_700), goal_text],
                    spacing=0, horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                width=110,
                alignment=ft.alignment.center,
            ),
            goal_btn(ft.icons.ADD_ROUNDED, 15),
        ],
        alignment=ft.MainAxisAlignment.CENTER,
        spacing=14,
    )

    def wake_up_click(e):
        now = datetime.now()
        current_date_str = now.strftime("%Y-%m-%d")

        if app_data["last_wake_date"] != current_date_str:
            if app_data["last_wake_date"]:
                last_date = datetime.strptime(app_data["last_wake_date"], "%Y-%m-%d")
                if (now.date() - last_date.date()).days == 1:
                    app_data["streak"] += 1
                else:
                    app_data["streak"] = 1
            else:
                app_data["streak"] = 1

            app_data["best_streak"] = max(app_data["best_streak"], app_data["streak"])
            app_data["last_wake_date"] = current_date_str
            app_data["last_wake_time"] = now.strftime("%H:%M")
            save_data(app_data)

        streak_number.value = str(app_data["streak"])
        best_streak_text.value = f"рекорд: {app_data['best_streak']}"

        goal_minutes = app_data["goal_hour"] * 60 + app_data["goal_minute"]
        now_minutes = now.hour * 60 + now.minute
        on_time = now_minutes <= goal_minutes
        wake_status_text.value = (
            f"Подъём в {now.strftime('%H:%M')} · " + ("вовремя ✓" if on_time else "с опозданием")
        )
        wake_status_text.color = WHITE if on_time else GREY

        wake_up_btn.disabled = True
        wake_up_btn.content.value = "Уже проснулся"
        wake_up_btn.bgcolor = DARK_GREY
        wake_up_btn.content.color = GREY
        page.update()

    wake_up_btn = ft.Container(
        content=ft.Text("Я проснулся", size=17, weight=ft.FontWeight.W_700, color=BLACK),
        bgcolor=WHITE,
        border_radius=100,
        padding=ft.padding.symmetric(vertical=18, horizontal=20),
        alignment=ft.alignment.center,
        width=280,
        on_click=wake_up_click,
        ink=True,
        animate=ft.animation.Animation(200, ft.AnimationCurve.EASE_OUT),
        animate_scale=ft.animation.Animation(150, ft.AnimationCurve.EASE_OUT),
    )

    streak_card = card(
        ft.Column(
            [
                ft.Row(
                    [ft.Icon(ft.icons.LOCAL_FIRE_DEPARTMENT_ROUNDED, color=WHITE, size=22),
                     ft.Text("СЕРИЯ", size=12, color=GREY, weight=ft.FontWeight.W_700)],
                    spacing=6,
                ),
                streak_number,
                best_streak_text,
                ft.Divider(height=20, color=DARK_GREY),
                wake_status_text,
                ft.Container(height=14),
                goal_row,
            ],
            spacing=2,
        )
    )

    header = ft.Column(
        [
            ft.Text("ДОБРОЕ УТРО", size=13, color=GREY, weight=ft.FontWeight.W_600),
            ft.Text("Мое Утро", size=30, weight=ft.FontWeight.W_900, color=WHITE),
        ],
        spacing=2,
        horizontal_alignment=ft.CrossAxisAlignment.START,
    )

    dest_section = ft.Column(
        [
            ft.Text("КУДА СОБИРАЕШЬСЯ", size=11, color=GREY, weight=ft.FontWeight.W_700),
            dest_chips_row,
        ],
        spacing=8,
    )

    wake_section = ft.Container(
        content=wake_up_btn,
        alignment=ft.alignment.center,
        padding=ft.padding.symmetric(vertical=6),
    )

    page.add(
        ft.Container(
            content=ft.Column(
                [
                    header,
                    ft.Container(height=16),
                    hero_card,
                    ft.Container(height=8),
                    dest_section,
                    ft.Container(height=6),
                    streak_card,
                    wake_section,
                ],
                spacing=16,
            ),
            padding=ft.padding.symmetric(horizontal=24, vertical=40),
        )
    )

    rebuild_chips()
    refresh_hero()


def main(page: ft.Page):
    try:
        build_ui(page)
    except Exception as e:
        page.bgcolor = "#FFFFFF"
        page.scroll = ft.ScrollMode.AUTO
        page.add(
            ft.Text("Ошибка запуска приложения:", size=16, weight=ft.FontWeight.BOLD, color="#CC0000"),
            ft.Text(str(e), size=13, color="#000000", selectable=True),
            ft.Text(traceback.format_exc(), size=10, color="#333333", selectable=True),
        )
        page.update()


ft.app(target=main)
