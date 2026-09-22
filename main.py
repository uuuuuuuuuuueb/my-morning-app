import flet as ft
from datetime import datetime, timedelta
import json
import os
import threading

DATA_FILE = "streak_data.json"

BLACK = "#0A0A0A"
WHITE = "#FFFFFF"
GREY = "#8A8A8A"
DARK_GREY = "#1C1C1C"
CARD_BG = "#141414"


def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {"streak": 0, "last_wake_date": None}


def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)


def main(page: ft.Page):
    page.title = "Мое Утро"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = BLACK
    page.padding = 0
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.window_width = 400
    page.window_height = 800
    page.fonts = {}

    app_data = load_data()

    def card(content, padding=24):
        return ft.Container(
            content=content,
            bgcolor=CARD_BG,
            border_radius=24,
            padding=padding,
            border=ft.border.all(1, DARK_GREY),
        )

    streak_number = ft.Text(
        str(app_data["streak"]), size=64, weight=ft.FontWeight.W_900, color=WHITE
    )
    streak_label = ft.Text("дней подряд", size=14, color=GREY, weight=ft.FontWeight.W_500)
    time_text = ft.Text("Ты еще не проснулся", size=13, color=GREY)

    # --- Баннер-уведомление (имитация push-уведомления) ---
    notif_title = ft.Text("МОЕ УТРО", size=11, weight=ft.FontWeight.W_800, color="#555555")
    notif_time = ft.Text("сейчас", size=11, color="#8A8A8A")
    notif_body = ft.Text("Выбери направление, чтобы увидеть время выхода", size=14, weight=ft.FontWeight.W_600, color=BLACK)

    notif_banner = ft.Container(
        content=ft.Row(
            [
                ft.Container(
                    content=ft.Icon(ft.icons.NOTIFICATIONS_ROUNDED, color=WHITE, size=18),
                    bgcolor=BLACK,
                    width=32,
                    height=32,
                    border_radius=8,
                    alignment=ft.alignment.center,
                ),
                ft.Column(
                    [
                        ft.Row(
                            [notif_title, notif_time],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        ),
                        notif_body,
                    ],
                    spacing=2,
                    expand=True,
                ),
            ],
            spacing=10,
            vertical_alignment=ft.CrossAxisAlignment.START,
        ),
        bgcolor="#EDEDED",
        border_radius=18,
        padding=14,
        animate=ft.animation.Animation(250, ft.AnimationCurve.EASE_OUT),
    )

    countdown_timer = {"handle": None}

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

            app_data["last_wake_date"] = current_date_str
            save_data(app_data)

        streak_number.value = str(app_data["streak"])
        time_text.value = f"Подъём в {now.strftime('%H:%M')}"
        time_text.color = WHITE
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
        animate=ft.animation.Animation(200, ft.AnimationCurve.EASE_OUT),
        ink=True,
    )

    destinations = {
        "Школа": (8, 0),
        "Шарага": (9, 30),
        "Работа": (10, 0),
    }

    def refresh_notification():
        if not dest_dropdown.value:
            return
        now = datetime.now()
        h, m = destinations[dest_dropdown.value]
        target_time = now.replace(hour=h, minute=m, second=0, microsecond=0)

        if now > target_time:
            target_time += timedelta(days=1)

        diff = target_time - now
        hours, remainder = divmod(diff.seconds, 3600)
        minutes, _ = divmod(remainder, 60)

        notif_body.value = f"До выхода ({dest_dropdown.value}): {hours} ч {minutes} мин"
        notif_time.value = now.strftime("%H:%M")
        try:
            page.update()
        except Exception:
            pass

    def schedule_next_refresh():
        refresh_notification()
        # обновляем баннер каждую минуту, пока приложение открыто
        countdown_timer["handle"] = threading.Timer(60, schedule_next_refresh)
        countdown_timer["handle"].daemon = True
        countdown_timer["handle"].start()

    def calculate_departure(e):
        if countdown_timer["handle"]:
            countdown_timer["handle"].cancel()
        schedule_next_refresh()

    dest_dropdown = ft.Dropdown(
        options=[ft.dropdown.Option(k) for k in destinations],
        border_color=DARK_GREY,
        bgcolor=DARK_GREY,
        color=WHITE,
        border_radius=14,
        content_padding=14,
        text_size=14,
        on_change=calculate_departure,
        expand=True,
    )

    header = ft.Column(
        [
            ft.Text("ДОБРОЕ УТРО", size=13, color=GREY, weight=ft.FontWeight.W_600),
            ft.Text("Мое Утро", size=30, weight=ft.FontWeight.W_900, color=WHITE),
        ],
        spacing=2,
        horizontal_alignment=ft.CrossAxisAlignment.START,
    )

    streak_card = card(
        ft.Column(
            [
                ft.Row([ft.Icon(ft.icons.LOCAL_FIRE_DEPARTMENT_ROUNDED, color=WHITE, size=22),
                        ft.Text("СЕРИЯ", size=12, color=GREY, weight=ft.FontWeight.W_700)],
                       spacing=6),
                streak_number,
                streak_label,
                ft.Divider(height=20, color=DARK_GREY),
                time_text,
            ],
            spacing=2,
        )
    )

    wake_section = ft.Container(
        content=wake_up_btn,
        alignment=ft.alignment.center,
        padding=ft.padding.symmetric(vertical=10),
    )

    departure_card = card(
        ft.Column(
            [
                ft.Row([ft.Icon(ft.icons.DIRECTIONS_WALK_ROUNDED, color=WHITE, size=20),
                        ft.Text("ВЫХОД", size=12, color=GREY, weight=ft.FontWeight.W_700)],
                       spacing=6),
                dest_dropdown,
                ft.Container(height=8),
                notif_banner,
            ],
            spacing=10,
        )
    )

    page.add(
        ft.Container(
            content=ft.Column(
                [
                    header,
                    ft.Container(height=20),
                    streak_card,
                    wake_section,
                    departure_card,
                ],
                spacing=16,
            ),
            padding=ft.padding.symmetric(horizontal=24, vertical=40),
        )
    )


ft.app(target=main)
