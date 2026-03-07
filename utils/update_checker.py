import subprocess
import logging
from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

logger = logging.getLogger(__name__)

_last_checked_commit = None


def check_for_updates() -> tuple[bool, str, str] | None:
    """Проверяет наличие обновлений в репозитории

    Returns:
        tuple[bool, str, str] | None: (has_updates, commit_hash, commit_message) или None при ошибке
    """
    global _last_checked_commit

    try:
        # Выполняем git fetch
        subprocess.run(
            ["git", "fetch"],
            cwd="/opt/cms",
            capture_output=True,
            timeout=30,
            check=True
        )

        # Получаем текущий HEAD
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd="/opt/cms",
            capture_output=True,
            text=True,
            timeout=5
        )
        current_commit = result.stdout.strip()

        # Получаем удаленный HEAD
        result = subprocess.run(
            ["git", "rev-parse", "origin/main"],
            cwd="/opt/cms",
            capture_output=True,
            text=True,
            timeout=5
        )
        remote_commit = result.stdout.strip()

        # Если это первая проверка, просто сохраняем текущий коммит
        if _last_checked_commit is None:
            _last_checked_commit = current_commit
            return None

        # Проверяем, есть ли новые коммиты
        if current_commit != remote_commit and _last_checked_commit == current_commit:
            # Получаем информацию о новом коммите
            result = subprocess.run(
                ["git", "log", "-1", "--format=%h", "origin/main"],
                cwd="/opt/cms",
                capture_output=True,
                text=True,
                timeout=5
            )
            commit_hash = result.stdout.strip()

            result = subprocess.run(
                ["git", "log", "-1", "--format=%s", "origin/main"],
                cwd="/opt/cms",
                capture_output=True,
                text=True,
                timeout=5
            )
            commit_message = result.stdout.strip()

            return (True, commit_hash, commit_message)

        return None

    except Exception as e:
        logger.error(f"Ошибка при проверке обновлений: {e}")
        return None


def get_update_keyboard() -> InlineKeyboardMarkup:
    """Возвращает клавиатуру с кнопкой обновления"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="Обновить панель",
                icon_custom_emoji_id="5172533495162995360",
                callback_data="update_panel"
            )
        ]
    ])


async def notify_admins_about_update(bot: Bot, admin_ids: list[int], commit_hash: str, commit_message: str):
    """Отправляет уведомление всем админам о новом обновлении"""
    text = (
        f'<tg-emoji emoji-id=\\'5174912572037530196\\'>👋</tg-emoji> <b>Вышло обновление</b>\n'
        f'<blockquote><tg-emoji emoji-id=\\'5174696127160648257\\'>👋</tg-emoji><b> Хэш:</b> {commit_hash}\n'
        f'<tg-emoji emoji-id=\\'5175138775080108724\\'>👋</tg-emoji> <b>Сведения:</b> {commit_message}</blockquote>'
    )

    for admin_id in admin_ids:
        try:
            await bot.send_message(
                chat_id=admin_id,
                text=text,
                parse_mode="HTML",
                reply_markup=get_update_keyboard()
            )
        except Exception as e:
            logger.error(f"Не удалось отправить уведомление админу {admin_id}: {e}")
