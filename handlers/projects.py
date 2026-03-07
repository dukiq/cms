import os
import re
import subprocess
from aiogram import Router, F
from aiogram.types import CallbackQuery, FSInputFile, Message
from aiogram.fsm.context import FSMContext

from config import DELETE_PASSWORD
from utils.database import get_all_projects, get_project, add_project, delete_project, update_project
from utils.docker_info import format_docker_stats, get_project_containers_count, is_project_running
from utils.docker_compose import parse_docker_compose
from utils.projects import restart_project, rebuild_project, stop_project, start_project, git_pull
from keyboards.inline import get_projects_menu, get_project_menu, get_delete_confirmation_menu
from states import ProjectStates

router = Router()


def get_project_network(project_id: int) -> str:
    """Получает основную сеть проекта"""
    project = get_project(project_id)
    if not project:
        return None
    _, _, _, network, _ = project
    return network.split(",")[0].strip() if network else None


@router.callback_query(F.data == "projects")
async def callback_projects(callback: CallbackQuery):
    """Показывает список проектов"""
    projects = get_all_projects()
    text = format_docker_stats()

    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=get_projects_menu(projects, page=0)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("projects_page_"))
async def callback_projects_page(callback: CallbackQuery):
    """Переключение страниц проектов"""
    page = int(callback.data.split("_")[-1])
    projects = get_all_projects()
    text = format_docker_stats()

    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=get_projects_menu(projects, page=page)
    )
    await callback.answer()


@router.callback_query(F.data == "projects_current")
async def callback_projects_current(callback: CallbackQuery):
    """Текущая страница - ничего не делаем"""
    await callback.answer()


@router.callback_query(F.data.regexp(r"^project_\d+$"))
async def callback_project_view(callback: CallbackQuery):
    """Просмотр проекта"""
    project_id = int(callback.data.split("_")[1])
    project = get_project(project_id)

    if not project:
        await callback.answer("Проект не найден", show_alert=True)
        return

    _, name, path, network, volumes = project
    main_network = network.split(",")[0].strip() if network else None
    containers_count = get_project_containers_count(network=main_network) if main_network else 0
    is_running = is_project_running(network=main_network) if main_network else False

    text = (
        f'<tg-emoji emoji-id=\'5172928932801938153\'>👋</tg-emoji> <b>{name}</b>\n'
        f'<blockquote><tg-emoji emoji-id=\'5174696127160648257\'>👋</tg-emoji><b> Сеть:</b> {network or "не указана"}\n'
        f'<tg-emoji emoji-id=\'5172494668658639634\'>👋</tg-emoji> <b>Контейнеры:</b> {containers_count}\n'
        f'<tg-emoji emoji-id=\'5175135107178038706\'>👋</tg-emoji> <b>Разделы:</b> {volumes or "не указаны"}</blockquote>'
    )

    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=get_project_menu(project_id, is_running)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("project_restart_"))
async def callback_project_restart(callback: CallbackQuery):
    """Перезапуск проекта"""
    project_id = int(callback.data.split("_")[2])
    project = get_project(project_id)

    if not project:
        await callback.answer("Проект не найден", show_alert=True)
        return

    _, name, path, _, _ = project

    await callback.answer("Перезапуск...")
    output, error = await restart_project(path)

    if error:
        await callback.answer(f"Ошибка: {error}", show_alert=True)
    else:
        await callback.answer("Проект перезапущен")

    # Обновляем меню
    is_running = is_project_running(network=get_project_network(project_id))
    await callback.message.edit_reply_markup(
        reply_markup=get_project_menu(project_id, is_running)
    )


@router.callback_query(F.data.startswith("project_rebuild_"))
async def callback_project_rebuild(callback: CallbackQuery):
    """Пересборка проекта"""
    project_id = int(callback.data.split("_")[2])
    project = get_project(project_id)

    if not project:
        await callback.answer("Проект не найден", show_alert=True)
        return

    _, name, path, _, _ = project

    # Показываем сообщение о пересборке
    await callback.message.edit_text(
        "<tg-emoji emoji-id='5172533495162995360'>👋</tg-emoji> <b>Пересобираю...</b>",
        parse_mode="HTML"
    )
    await callback.answer()

    output, error_file = await rebuild_project(path)

    if error_file:
        # Отправляем файл с ошибками
        await callback.message.answer_document(FSInputFile(error_file))
        await callback.message.edit_text(
            "<tg-emoji emoji-id='5172888203627070189'>👋</tg-emoji> <b>Ошибка при пересборке</b>",
            parse_mode="HTML",
            reply_markup=get_project_menu(project_id, is_project_running(network=get_project_network(project_id)))
        )
    else:
        await callback.message.edit_text(
            "<tg-emoji emoji-id='5172888203627070189'>👋</tg-emoji> <b>Контейнер пересобран</b>",
            parse_mode="HTML",
            reply_markup=get_project_menu(project_id, is_project_running(network=get_project_network(project_id)))
        )


@router.callback_query(F.data.startswith("project_toggle_"))
async def callback_project_toggle(callback: CallbackQuery):
    """Включить/выключить проект"""
    project_id = int(callback.data.split("_")[2])
    project = get_project(project_id)

    if not project:
        await callback.answer("Проект не найден", show_alert=True)
        return

    _, name, path, _, _ = project
    is_running = is_project_running(network=get_project_network(project_id))

    if is_running:
        success, output = await stop_project(path)
        message = "Контейнер выключен"
    else:
        success, output = await start_project(path)
        message = "Контейнер включен"

    await callback.answer(message, show_alert=True)

    # Обновляем меню
    is_running = is_project_running(network=get_project_network(project_id))
    await callback.message.edit_reply_markup(
        reply_markup=get_project_menu(project_id, is_running)
    )


@router.callback_query(F.data.startswith("project_pull_"))
async def callback_project_pull(callback: CallbackQuery):
    """Git pull проекта"""
    project_id = int(callback.data.split("_")[2])
    project = get_project(project_id)

    if not project:
        await callback.answer("Проект не найден", show_alert=True)
        return

    _, name, path, _, _ = project

    output, error_file = await git_pull(path)

    if error_file:
        await callback.message.answer_document(FSInputFile(error_file))
        await callback.answer("Ошибка при pull", show_alert=True)
    else:
        await callback.answer("Пулл успешен", show_alert=True)


@router.callback_query(F.data == "back_projects")
async def callback_back_projects(callback: CallbackQuery):
    """Возврат к списку проектов"""
    projects = get_all_projects()
    text = format_docker_stats()

    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=get_projects_menu(projects, page=0)
    )
    await callback.answer()


@router.callback_query(F.data == "project_create")
async def callback_project_create(callback: CallbackQuery, state: FSMContext):
    """Создание проекта"""
    await callback.message.edit_text(
        "Введите название проекта на английском (до 32 символов):",
        parse_mode="HTML"
    )
    await state.set_state(ProjectStates.waiting_name)
    await callback.answer()


@router.message(ProjectStates.waiting_name)
async def process_project_name(message: Message, state: FSMContext):
    """Обработка названия проекта"""
    name = message.text.strip()

    # Проверка на английские символы и длину
    if not re.match(r'^[a-zA-Z0-9_-]+$', name):
        await message.answer("Название должно содержать только английские буквы, цифры, _ и -")
        return

    if len(name) > 32:
        await message.answer("Название не должно превышать 32 символа")
        return

    # Сохраняем название
    await state.update_data(name=name)
    await state.set_state(ProjectStates.waiting_path)

    await message.answer("Введите директорию проекта (например: /opt/prj):")


@router.message(ProjectStates.waiting_path)
async def process_project_path(message: Message, state: FSMContext):
    """Обработка пути проекта"""
    path = message.text.strip()

    # Проверка существования директории
    if not os.path.isdir(path):
        await message.answer("Директория не существует. Введите существующую директорию:")
        return

    # Получаем сохраненные данные
    data = await state.get_data()
    name = data.get("name")

    # Парсим docker-compose.yml
    network, volumes = parse_docker_compose(path)

    # Сохраняем проект в БД
    try:
        project_id = add_project(name, path, network, volumes)
        await state.clear()

        # Показываем список проектов
        projects = get_all_projects()
        text = format_docker_stats()

        await message.answer(
            f"Проект <b>{name}</b> создан!",
            parse_mode="HTML"
        )
        await message.answer(
            text,
            parse_mode="HTML",
            reply_markup=get_projects_menu(projects, page=0)
        )
    except Exception as e:
        await message.answer(f"Ошибка при создании проекта: {str(e)}")
        await state.clear()


@router.callback_query(F.data.regexp(r"^project_delete_\d+$"))
async def callback_project_delete(callback: CallbackQuery, state: FSMContext):
    """Запрос пароля для удаления проекта"""
    project_id = int(callback.data.split("_")[2])
    project = get_project(project_id)

    if not project:
        await callback.answer("Проект не найден", show_alert=True)
        return

    # Сохраняем ID проекта в состояние
    await state.update_data(delete_project_id=project_id)
    await state.set_state(ProjectStates.waiting_delete_password)

    await callback.message.edit_text(
        "Введите пароль для удаления проекта:",
        parse_mode="HTML"
    )
    await callback.answer()


@router.message(ProjectStates.waiting_delete_password)
async def process_delete_password(message: Message, state: FSMContext):
    """Проверка пароля для удаления"""
    password = message.text.strip()

    if password != DELETE_PASSWORD:
        await message.answer("Неверный пароль")
        return

    # Получаем ID проекта
    data = await state.get_data()
    project_id = data.get("delete_project_id")

    await state.clear()

    # Спрашиваем об удалении директории
    await message.answer(
        "<tg-emoji emoji-id='5172445899304993500'>👋</tg-emoji> <b>Удалить также директорию проекта?</b>",
        parse_mode="HTML",
        reply_markup=get_delete_confirmation_menu(project_id)
    )


@router.callback_query(F.data.startswith("project_delete_yes_"))
async def callback_project_delete_yes(callback: CallbackQuery):
    """Удаление проекта с директорией"""
    project_id = int(callback.data.split("_")[3])
    project = get_project(project_id)

    if not project:
        await callback.answer("Проект не найден", show_alert=True)
        return

    _, name, path, _, _ = project

    # Удаляем директорию
    try:
        subprocess.run(["rm", "-rf", path], check=True, timeout=30)
    except Exception as e:
        await callback.answer(f"Ошибка при удалении директории: {str(e)}", show_alert=True)
        return

    # Удаляем из БД
    delete_project(project_id)

    await callback.answer("Проект и директория удалены")

    # Показываем список проектов
    projects = get_all_projects()
    text = format_docker_stats()

    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=get_projects_menu(projects, page=0)
    )


@router.callback_query(F.data.startswith("project_delete_no_"))
async def callback_project_delete_no(callback: CallbackQuery):
    """Удаление проекта только из БД"""
    project_id = int(callback.data.split("_")[3])
    project = get_project(project_id)

    if not project:
        await callback.answer("Проект не найден", show_alert=True)
        return

    _, name, _, _, _ = project

    # Удаляем из БД
    delete_project(project_id)

    await callback.answer("Проект удален из БД")

    # Показываем список проектов
    projects = get_all_projects()
    text = format_docker_stats()

    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=get_projects_menu(projects, page=0)
    )


@router.callback_query(F.data.startswith("project_refresh_"))
async def callback_project_refresh(callback: CallbackQuery):
    """Обновление информации о проекте"""
    project_id = int(callback.data.split("_")[2])
    project = get_project(project_id)

    if not project:
        await callback.answer("Проект не найден", show_alert=True)
        return

    _, name, path, _, _ = project

    # Обновляем network и volumes из docker-compose.yml
    network, volumes = parse_docker_compose(path)
    update_project(project_id, network, volumes)

    # Получаем обновленную информацию
    main_network = get_project_network(project_id)
    containers_count = get_project_containers_count(network=main_network) if main_network else 0
    is_running = is_project_running(network=main_network)

    text = (
        f'<tg-emoji emoji-id=\'5172928932801938153\'>👋</tg-emoji> <b>{name}</b>\n'
        f'<blockquote><tg-emoji emoji-id=\'5174696127160648257\'>👋</tg-emoji><b> Сеть:</b> {network or "не указана"}\n'
        f'<tg-emoji emoji-id=\'5172494668658639634\'>👋</tg-emoji> <b>Контейнеры:</b> {containers_count}\n'
        f'<tg-emoji emoji-id=\'5175135107178038706\'>👋</tg-emoji> <b>Разделы:</b> {volumes or "не указаны"}</blockquote>'
    )

    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=get_project_menu(project_id, is_running)
    )
    await callback.answer()
