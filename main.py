import flet as ft
from datetime import datetime, timedelta
import json
import os
import random
import traceback

# Храним файл данных рядом со скриптом, а не в "текущей папке запуска" —
# иначе при запуске из разных мест (IDE, ярлык, uv) стрик мог "теряться".
APP_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(APP_DIR, "streak_data.json")

BLACK = "#0A0A0A"
WHITE = "#FFFFFF"
GREY = "#8A8A8A"
DARK_GREY = "#1C1C1C"
CARD_BG = "#141414"
ACCENT = "#EDEDED"
FIRE_COLORS = ["#8A8A8A", "#F2C94C", "#F2994A", "#EB5757", "#FF3D3D"]

FONT_NAME = "Manrope"

DESTINATIONS = {
    "Школа": (8, 0),
    "Шарага": (9, 30),
    "Работа": (10, 0),
    "Репетитор": (18, 0),
}

WISHES = [
    "Пусть сегодня всё получится с первого раза ✨",
    "Маленькие шаги каждый день — большой путь за год 🚀",
    "Ты уже встал(а) — считай, полдела сделано 💪",
    "Сегодня отличный день, чтобы стать чуточку лучше 🌱",
    "Не забудь улыбнуться хотя бы раз сегодня 🙂",
    "Помни: высыпаться — это тоже продуктивность 😴",
]


def load_data():
    default = {
        "streak": 0,
        "best_streak": 0,
        "last_wake_date": None,
        "last_wake_time": None,
        "goal_hour": 7,
        "goal_minute": 0,
    }
    try:
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                saved = json.load(f)
                default.update(saved)
    except (json.JSONDecodeError, OSError):
        # повреждённый файл не должен ронять приложение — просто начинаем заново
        pass
    return default


def save_data(data):
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)
    except OSError:
        pass


def build_ui(page: ft.Page):
    page.title = "Мое Утро"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = BLACK
    page.padding = 0
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.scroll = ft.ScrollMode.AUTO

    # Красивый современный шрифт (грузится с Google Fonts при наличии интернета;
    # если сети нет — Flet тихо откатится на системный шрифт, без ошибок).
    page.fonts = {
        "Manrope": "https://raw.githubusercontent.com/google/fonts/main/ofl/manrope/Manrope%5Bwght%5D.ttf",
    }
    page.theme = ft.Theme(font_family=FONT_NAME)

    app_data = load_data()
    state = {"dest": "Школа"}

    def card(content, padding=22):
        return ft.Container(
            content=content,
            bgcolor=CARD_BG,
            border_radius=24,
            padding=padding,
            border=ft.border.all(1, DARK_GREY),
            animate=ft.Animation(400, ft.AnimationCurve.EASE_OUT),
        )

    # ---------- HERO: время до выхода ----------
    hero_time = ft.Text("--", size=46, weight=ft.FontWeight.W_900, color=WHITE, font_family=FONT_NAME)
    hero_sub = ft.Text("до выхода", size=13, color=GREY, font_family=FONT_NAME)
    hero_dest = ft.Text("Школа · к 08:00", size=13, weight=ft.FontWeight.W_600, color="#CFCFCF", font_family=FONT_NAME)

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
                    [ft.Icon(ft.Icons.SCHEDULE_ROUNDED, color=BLACK, size=18),
                     ft.Text("ВРЕМЯ ВЫХОДА", size=11, weight=ft.FontWeight.W_800, color="#4A4A4A", font_family=FONT_NAME)],
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
        animate=ft.Animation(400, ft.AnimationCurve.EASE_OUT),
        animate_scale=ft.Animation(400, ft.AnimationCurve.EASE_OUT),
    )
    # исправляем цвета текста внутри hero (на белом фоне нужен темный текст)
    hero_time.color = BLACK
    hero_sub.color = "#555555"

    # ---------- Выбор направления (таблетки) ----------
    dest_chips_row = ft.Row(spacing=8, wrap=True)

    def select_dest(name):
        def handler(e):
            if state["dest"] == name:
                return
            state["dest"] = name
            rebuild_chips()
            refresh_hero()
        return handler

    def chip_hover(container):
        def handler(e):
            container.scale = 1.05 if e.data == "true" else 1.0
            page.update()
        return handler

    def rebuild_chips():
        dest_chips_row.controls.clear()
        for name in DESTINATIONS:
            is_selected = state["dest"] == name
            chip = ft.Container(
                content=ft.Text(
                    name,
                    size=13,
                    weight=ft.FontWeight.W_600,
                    color=BLACK if is_selected else WHITE,
                    font_family=FONT_NAME,
                ),
                bgcolor=WHITE if is_selected else DARK_GREY,
                border_radius=100,
                padding=ft.padding.symmetric(vertical=10, horizontal=16),
                on_click=select_dest(name),
                ink=True,
                scale=1.0,
                animate=ft.Animation(300, ft.AnimationCurve.EASE_OUT),
                animate_scale=ft.Animation(200, ft.AnimationCurve.EASE_OUT),
            )
            chip.on_hover = chip_hover(chip)
            dest_chips_row.controls.append(chip)
        try:
            page.update()
        except Exception:
            pass

    # ---------- Серия и цель подъема ----------
    streak_number = ft.Text(
        str(app_data["streak"]), size=48, weight=ft.FontWeight.W_900, color=WHITE,
        font_family=FONT_NAME,
    )
    best_streak_text = ft.Text(f"рекорд: {app_data['best_streak']}", size=12, color=GREY, font_family=FONT_NAME)
    wake_status_text = ft.Text("Ты еще не проснулся", size=13, color=GREY, font_family=FONT_NAME)

    # Фишка: "пламя серии" — иконка растёт и меняет цвет по мере роста стрика
    def fire_color(streak):
        if streak <= 0:
            return FIRE_COLORS[0]
        if streak < 3:
            return FIRE_COLORS[1]
        if streak < 7:
            return FIRE_COLORS[2]
        if streak < 30:
            return FIRE_COLORS[3]
        return FIRE_COLORS[4]

    def fire_scale(streak):
        return 1.0 + min(streak, 25) * 0.035

    fire_icon = ft.Icon(
        ft.Icons.LOCAL_FIRE_DEPARTMENT_ROUNDED,
        color=fire_color(app_data["streak"]),
        size=22,
    )
    fire_wrap = ft.Container(
        content=fire_icon,
        scale=1.0,
        animate_scale=ft.Animation(400, ft.AnimationCurve.EASE_OUT),
    )

    milestone_text = ft.Text(
        "", size=12, color=WHITE, weight=ft.FontWeight.W_600, font_family=FONT_NAME,
        opacity=0, animate_opacity=ft.Animation(500, ft.AnimationCurve.EASE_OUT),
    )

    MILESTONES = {3: "🎉 3 дня подряд — старт положен!",
                  7: "🔥 неделя без пропусков — это уже привычка!",
                  14: "💎 две недели — серьёзная дисциплина!",
                  30: "👑 месяц подряд — ты легенда!"}

    def update_fire(streak):
        fire_icon.color = fire_color(streak)
        fire_wrap.scale = fire_scale(streak)
        if streak in MILESTONES:
            milestone_text.value = MILESTONES[streak]
            milestone_text.opacity = 1
        else:
            milestone_text.opacity = 0

    goal_text = ft.Text(
        f"{app_data['goal_hour']:02d}:{app_data['goal_minute']:02d}",
        size=20, weight=ft.FontWeight.W_800, color=WHITE, font_family=FONT_NAME,
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
        btn = ft.Container(
            content=ft.Icon(icon, color=WHITE, size=16),
            width=32, height=32,
            bgcolor=DARK_GREY,
            border_radius=10,
            alignment=ft.alignment.center,
            on_click=adjust_goal(delta),
            ink=True,
            scale=1.0,
            animate_scale=ft.Animation(150, ft.AnimationCurve.EASE_OUT),
        )

        def hover(e):
            btn.scale = 1.1 if e.data == "true" else 1.0
            page.update()

        btn.on_hover = hover
        return btn

    goal_row = ft.Row(
        [
            goal_btn(ft.Icons.REMOVE_ROUNDED, -15),
            ft.Container(
                content=ft.Column(
                    [ft.Text("ЦЕЛЬ ПОДЪЁМА", size=10, color=GREY, weight=ft.FontWeight.W_700, font_family=FONT_NAME),
                     goal_text],
                    spacing=0, horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                width=110,
                alignment=ft.alignment.center,
            ),
            goal_btn(ft.Icons.ADD_ROUNDED, 15),
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
        update_fire(app_data["streak"])

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
        wake_up_btn.scale = 0.97
        page.update()

    wake_up_btn = ft.Container(
        content=ft.Text("Я проснулся", size=17, weight=ft.FontWeight.W_700, color=BLACK, font_family=FONT_NAME),
        bgcolor=WHITE,
        border_radius=100,
        padding=ft.padding.symmetric(vertical=18, horizontal=20),
        alignment=ft.alignment.center,
        width=280,
        on_click=wake_up_click,
        ink=True,
        scale=1.0,
        animate=ft.Animation(300, ft.AnimationCurve.EASE_OUT),
        animate_scale=ft.Animation(250, ft.AnimationCurve.EASE_OUT),
    )

    def btn_hover(e):
        if not wake_up_btn.disabled:
            wake_up_btn.scale = 1.03 if e.data == "true" else 1.0
            page.update()

    wake_up_btn.on_hover = btn_hover

    streak_card = card(
        ft.Column(
            [
                ft.Row(
                    [fire_wrap,
                     ft.Text("СЕРИЯ", size=12, color=GREY, weight=ft.FontWeight.W_700, font_family=FONT_NAME)],
                    spacing=6,
                ),
                streak_number,
                best_streak_text,
                milestone_text,
                ft.Divider(height=20, color=DARK_GREY),
                wake_status_text,
                ft.Container(height=14),
                goal_row,
            ],
            spacing=4,
        )
    )

    wish_text = ft.Text(
        random.choice(WISHES), size=12, color="#B5B5B5", italic=True, font_family=FONT_NAME,
    )

    header = ft.Column(
        [
            ft.Text("ДОБРОЕ УТРО", size=13, color=GREY, weight=ft.FontWeight.W_600, font_family=FONT_NAME),
            ft.Text("Мое Утро", size=30, weight=ft.FontWeight.W_900, color=WHITE, font_family=FONT_NAME),
            ft.Container(height=4),
            wish_text,
        ],
        spacing=2,
        horizontal_alignment=ft.CrossAxisAlignment.START,
    )

    dest_section = ft.Column(
        [
            ft.Text("КУДА СОБИРАЕШЬСЯ", size=11, color=GREY, weight=ft.FontWeight.W_700, font_family=FONT_NAME),
            dest_chips_row,
        ],
        spacing=8,
    )

    wake_section = ft.Container(
        content=wake_up_btn,
        alignment=ft.alignment.center,
        padding=ft.padding.symmetric(vertical=6),
    )

    # Обёртка для плавного появления всего интерфейса при запуске
    root = ft.Container(
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
        opacity=0,
        animate_opacity=ft.Animation(600, ft.AnimationCurve.EASE_OUT),
    )

    page.add(root)

    update_fire(app_data["streak"])
    rebuild_chips()
    refresh_hero()

    # запускаем плавное появление интерфейса
    root.opacity = 1
    page.update()


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
