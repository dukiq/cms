import asyncio
import html
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from utils.system_info import format_system_stats
from utils.terminal import terminal_manager
from utils.admins import add_admin, remove_admin
from keyboards.inline import (
    get_main_menu,
    get_terminal_keyboard,
    get_settings_menu,
    get_admins_menu
)
from states import TerminalStates, AdminStates

router = Router()


@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    stats = format_system_stats()
    await message.answer(stats, parse_mode="HTML", reply_markup=get_main_menu())


@router.callback_query(F.data == "terminal")
async def callback_terminal(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "<blockquote><tg-emoji emoji-id='5174912572037530196'>👋</tg-emoji><b>Введите команду:</b></blockquote>",
        parse_mode="HTML"
    )
    await state.set_state(TerminalStates.waiting_command)
    await callback.answer()


@router.message(TerminalStates.waiting_command)
async def process_terminal_command(message: Message, state: FSMContext):
    command = message.text

    terminal_manager.execute_command_live(message.from_user.id, command)

    sent_message = await message.answer(
        "<blockquote>Выполнение...</blockquote>",
        parse_mode="HTML"
    )

    last_output = ""
    max_iterations = 360

    for _ in range(max_iterations):
        await asyncio.sleep(5)

        output, venv_name, is_complete = terminal_manager.get_live_output(message.from_user.id)

        escaped_output = html.escape(output)

        if venv_name:
            formatted_output = f"({venv_name}) {escaped_output}"
        else:
            formatted_output = escaped_output

        if formatted_output != last_output:
            try:
                await sent_message.edit_text(
                    f"<blockquote>{formatted_output}</blockquote>",
                    parse_mode="HTML"
                )
                last_output = formatted_output
            except Exception as e:
                print(f"Error editing message: {e}")

        if is_complete:
            terminal_manager.cleanup_live(message.from_user.id)
            try:
                # Обновляем текст финальным выводом и добавляем клавиатуру
                await sent_message.edit_text(
                    f"<blockquote>{formatted_output}</blockquote>",
                    parse_mode="HTML",
                    reply_markup=get_terminal_keyboard()
                )
            except Exception as e:
                print(f"Error updating final message: {e}")
                try:
                    await sent_message.edit_reply_markup(reply_markup=get_terminal_keyboard())
                except:
                    pass
            break


@router.callback_query(F.data == "terminal_stop")
async def callback_terminal_stop(callback: CallbackQuery, state: FSMContext):
    terminal_manager.close_session(callback.from_user.id)
    await state.clear()

    stats = format_system_stats()
    await callback.message.edit_text(stats, parse_mode="HTML", reply_markup=get_main_menu())
    await callback.answer()


@router.callback_query(F.data == "settings")
async def callback_settings(callback: CallbackQuery):
    await callback.message.edit_text(
        "<tg-emoji emoji-id='5174760671929172797'>👋</tg-emoji><b>Настройки</b>",
        parse_mode="HTML",
        reply_markup=get_settings_menu()
    )
    await callback.answer()


@router.callback_query(F.data == "admins")
async def callback_admins(callback: CallbackQuery):
    await callback.message.edit_text(
        "<tg-emoji emoji-id='5174760671929172797'>👋</tg-emoji><b>Админы</b>",
        parse_mode="HTML",
        reply_markup=get_admins_menu()
    )
    await callback.answer()


@router.callback_query(F.data == "admin_add")
async def callback_admin_add(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "<tg-emoji emoji-id='5172623642231571081'>👋</tg-emoji>Введите айди:",
        parse_mode="HTML"
    )
    await state.set_state(AdminStates.waiting_add_id)
    await callback.answer()


@router.message(AdminStates.waiting_add_id)
async def process_admin_add(message: Message, state: FSMContext):
    try:
        user_id = int(message.text)
        add_admin(user_id)
        msg = await message.answer("Админ добавлен")

        await asyncio.sleep(2)
        await msg.delete()

        await state.clear()
        stats = format_system_stats()
        await message.answer(stats, parse_mode="HTML", reply_markup=get_main_menu())
    except ValueError:
        await message.answer("Неверный формат ID")


@router.callback_query(F.data == "admin_remove")
async def callback_admin_remove(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "<tg-emoji emoji-id='5172623642231571081'>👋</tg-emoji>Введите айди:",
        parse_mode="HTML"
    )
    await state.set_state(AdminStates.waiting_remove_id)
    await callback.answer()


@router.message(AdminStates.waiting_remove_id)
async def process_admin_remove(message: Message, state: FSMContext):
    try:
        user_id = int(message.text)
        remove_admin(user_id)
        msg = await message.answer("Админ удален")

        await asyncio.sleep(2)
        await msg.delete()

        await state.clear()
        stats = format_system_stats()
        await message.answer(stats, parse_mode="HTML", reply_markup=get_main_menu())
    except ValueError:
        await message.answer("Неверный формат ID")


@router.callback_query(F.data == "back_settings")
async def callback_back_settings(callback: CallbackQuery):
    await callback.message.edit_text(
        "<tg-emoji emoji-id='5174760671929172797'>👋</tg-emoji><b>Настройки</b>",
        parse_mode="HTML",
        reply_markup=get_settings_menu()
    )
    await callback.answer()


@router.callback_query(F.data == "back_main")
async def callback_back_main(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    stats = format_system_stats()
    await callback.message.edit_text(stats, parse_mode="HTML", reply_markup=get_main_menu())
    await callback.answer()


@router.callback_query(F.data == "update_panel")
async def callback_update_panel(callback: CallbackQuery):
    """Обновление панели"""
    import subprocess
    import os
    import logging
    from config import BOT_TOKEN, ADMIN_ID

    logger = logging.getLogger(__name__)

    await callback.message.edit_text(
        "<tg-emoji emoji-id='5172533495162995360'>👋</tg-emoji> <b>Запуск обновления...</b>",
        parse_mode="HTML"
    )
    await callback.answer()

    update_script = '''#!/bin/bash
export PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"

LOGFILE="/tmp/cms_update.log"
exec > "$LOGFILE" 2>&1

set -e

INSTALL_DIR="/opt/cms"

echo "Начало обновления..."
sleep 2

cd "$INSTALL_DIR"

echo "Обновление кода..."
git pull

echo "Установка зависимостей..."
. venv/bin/activate
pip install -r requirements.txt

echo "Перезапуск сервиса..."
systemctl restart cmsdash || true

set +e

sleep 5

echo "Извлечение токена и ID..."
BOT_TOKEN=$(grep BOT_TOKEN .env | cut -d'=' -f2)
ADMIN_ID=$(grep ADMIN_ID .env | cut -d'=' -f2)

echo "Отправка уведомления..."
curl -s -X POST "https://api.telegram.org/bot$BOT_TOKEN/sendMessage" \
  -d "chat_id=$ADMIN_ID" \
  -d "parse_mode=HTML" \
  -d "text=<tg-emoji emoji-id='5172533495162995360'>👋</tg-emoji> <b>Обновление панели завершено</b>"

echo "Обновление завершено успешно"
rm -f "$0"
'''

    script_path = "/tmp/cms_update.sh"

    try:
        logger.info("Создание скрипта обновления...")
        with open(script_path, "w") as f:
            f.write(update_script)

        os.chmod(script_path, 0o755)
        logger.info(f"Скрипт создан: {script_path}")

        logger.info("Запуск скрипта обновления...")
        subprocess.Popen(["/usr/bin/systemd-run", "--unit=cms-update", "/bin/bash", script_path],
                         stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL)
        logger.info("Скрипт обновления запущен")
    except Exception as e:
        logger.error(f"Ошибка при обновлении панели: {e}")
