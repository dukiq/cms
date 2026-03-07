import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from config import BOT_TOKEN, ADMIN_ID
from middlewares.admin_check import AdminCheckMiddleware
from handlers import admin, projects
from utils.database import init_database, get_all_admins
from utils.system_info import update_system_stats, stats_updater
from utils.docker_info import update_docker_stats, docker_stats_updater
from utils.update_checker import check_for_updates, notify_admins_about_update

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def update_checker(bot: Bot):
    """Фоновая задача для проверки обновлений каждые 3 часа"""
    while True:
        try:
            await asyncio.sleep(10800)  # 3 часа

            logger.info("Проверка обновлений...")
            result = check_for_updates()

            if result and result[0]:
                _, commit_hash, commit_message = result
                logger.info(f"Найдено обновление: {commit_hash} - {commit_message}")

                # Получаем список всех админов
                admin_ids = [ADMIN_ID]
                db_admins = get_all_admins()
                admin_ids.extend([admin_id for admin_id, in db_admins])

                # Отправляем уведомления
                await notify_admins_about_update(bot, admin_ids, commit_hash, commit_message)
        except Exception as e:
            logger.error(f"Ошибка при проверке обновлений: {e}")


async def main():
    init_database()
    logger.info("База данных инициализирована")

    # Обновляем статистику при старте
    update_system_stats()
    update_docker_stats()
    logger.info("Статистика системы и Docker обновлена")

    # Инициализируем проверку обновлений
    check_for_updates()
    logger.info("Проверка обновлений инициализирована")

    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )

    # Запускаем фоновые задачи для обновления статистики
    asyncio.create_task(stats_updater())
    asyncio.create_task(docker_stats_updater())
    asyncio.create_task(update_checker(bot))

    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    dp.message.middleware(AdminCheckMiddleware())
    dp.callback_query.middleware(AdminCheckMiddleware())

    dp.include_router(admin.router)
    dp.include_router(projects.router)

    logger.info("Бот запущен")

    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен")
