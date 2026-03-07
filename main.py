import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from config import BOT_TOKEN
from middlewares.admin_check import AdminCheckMiddleware
from handlers import admin, projects
from utils.database import init_database
from utils.system_info import update_system_stats, stats_updater
from utils.docker_info import update_docker_stats, docker_stats_updater

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    init_database()
    logger.info("База данных инициализирована")

    # Обновляем статистику при старте
    update_system_stats()
    update_docker_stats()
    logger.info("Статистика системы и Docker обновлена")

    # Запускаем фоновые задачи для обновления статистики
    asyncio.create_task(stats_updater())
    asyncio.create_task(docker_stats_updater())

    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )

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
