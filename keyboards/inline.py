from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_main_menu() -> InlineKeyboardMarkup:
    """Главное меню"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="Терминал",
                icon_custom_emoji_id="5174912572037530196",
                callback_data="terminal"
            ),
            InlineKeyboardButton(
                text="Настройки",
                icon_custom_emoji_id="5174760671929172797",
                callback_data="settings"
            )
        ],
        [
            InlineKeyboardButton(
                text="Проекты",
                icon_custom_emoji_id="5172581207954686681",
                callback_data="projects"
            ),
            InlineKeyboardButton(
                text="Проводник",
                icon_custom_emoji_id="5172494668658639634",
                callback_data="explorer"
            )
        ],
        [
            InlineKeyboardButton(
                text="Обновить панель",
                icon_custom_emoji_id="5172533495162995360",
                callback_data="update_panel"
            )
        ]
    ])


def get_terminal_keyboard() -> InlineKeyboardMarkup:
    """Кнопка завершения терминала"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="Завершить",
                icon_custom_emoji_id="5174912572037530196",
                callback_data="terminal_stop"
            )
        ]
    ])


def get_settings_menu() -> InlineKeyboardMarkup:
    """Меню настроек"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="Админы",
                callback_data="admins"
            )
        ],
        [
            InlineKeyboardButton(
                text="Назад",
                icon_custom_emoji_id="5172739571988824888",
                callback_data="back_main"
            )
        ]
    ])


def get_admins_menu() -> InlineKeyboardMarkup:
    """Меню управления админами"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="Добавить",
                callback_data="admin_add"
            ),
            InlineKeyboardButton(
                text="Удалить",
                callback_data="admin_remove"
            )
        ],
        [
            InlineKeyboardButton(
                text="Назад",
                icon_custom_emoji_id="5172739571988824888",
                callback_data="back_settings"
            )
        ]
    ])


def get_projects_menu(projects: list[tuple], page: int = 0) -> InlineKeyboardMarkup:
    """Меню проектов с пагинацией"""
    keyboard = []

    # 4 проекта на странице
    start = page * 4
    end = start + 4
    page_projects = projects[start:end]

    # Кнопки проектов
    for project_id, name, _, _, _ in page_projects:
        keyboard.append([
            InlineKeyboardButton(
                text=name,
                callback_data=f"project_{project_id}"
            )
        ])

    # Пагинация
    if len(projects) > 4:
        nav_buttons = []
        if page > 0:
            nav_buttons.append(
                InlineKeyboardButton(text="←", callback_data=f"projects_page_{page-1}")
            )
        nav_buttons.append(
            InlineKeyboardButton(text=f"{page + 1}", callback_data="projects_current")
        )
        if end < len(projects):
            nav_buttons.append(
                InlineKeyboardButton(text="→", callback_data=f"projects_page_{page+1}")
            )
        keyboard.append(nav_buttons)

    # Кнопка Создать
    keyboard.append([
        InlineKeyboardButton(
            text="Создать",
            icon_custom_emoji_id="5175164046667678412",
            callback_data="project_create"
        )
    ])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_project_menu(project_id: int, is_running: bool) -> InlineKeyboardMarkup:
    """Меню управления проектом"""
    keyboard = [
        [
            InlineKeyboardButton(
                text="Перезапустить",
                icon_custom_emoji_id="5172868665820840610",
                callback_data=f"project_restart_{project_id}"
            ),
            InlineKeyboardButton(
                text="Пересобрать",
                icon_custom_emoji_id="5172533495162995360",
                callback_data=f"project_rebuild_{project_id}"
            )
        ],
        [
            InlineKeyboardButton(
                text="Выключить" if is_running else "Включить",
                icon_custom_emoji_id="5172915545388876587" if is_running else "5172906452943110742",
                callback_data=f"project_toggle_{project_id}"
            ),
            InlineKeyboardButton(
                text="Пулл",
                icon_custom_emoji_id="5172800865467105963",
                callback_data=f"project_pull_{project_id}"
            )
        ],
        [
            InlineKeyboardButton(
                text="Удалить",
                icon_custom_emoji_id="5172445899304993500",
                callback_data=f"project_delete_{project_id}"
            ),
            InlineKeyboardButton(
                text="Обновить",
                icon_custom_emoji_id="5172658298322682813",
                callback_data=f"project_refresh_{project_id}"
            )
        ],
        [
            InlineKeyboardButton(
                text="Назад",
                icon_custom_emoji_id="5172739571988824888",
                callback_data="back_projects"
            )
        ]
    ]

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_delete_confirmation_menu(project_id: int) -> InlineKeyboardMarkup:
    """Меню подтверждения удаления директории"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="Да",
                icon_custom_emoji_id="5172888203627070189",
                callback_data=f"project_delete_yes_{project_id}"
            ),
            InlineKeyboardButton(
                text="Нет",
                icon_custom_emoji_id="5172915545388876587",
                callback_data=f"project_delete_no_{project_id}"
            )
        ]
    ])
