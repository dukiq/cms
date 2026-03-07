import psutil
import asyncio

_cached_cpu_percent = 0.0
_cached_cpu_count = psutil.cpu_count()
_cached_ram_percent = 0.0


def update_system_stats():
    global _cached_cpu_percent, _cached_cpu_count, _cached_ram_percent

    _cached_cpu_percent = psutil.cpu_percent(interval=1)
    _cached_cpu_count = psutil.cpu_count()

    ram = psutil.virtual_memory()
    _cached_ram_percent = ram.percent


def format_system_stats() -> str:
    cpu_total_percent = _cached_cpu_count * 100

    return (
        f'<tg-emoji emoji-id=\'4904565554943099861\'>👋</tg-emoji><b>CMS Приветствует</b>\n\n'
        f'<blockquote><tg-emoji emoji-id=\'5172869086727635492\'>👋</tg-emoji><b>CPU:</b> {_cached_cpu_percent:.0f}/{cpu_total_percent}%\n'
        f'<tg-emoji emoji-id=\'5174693704799093859\'>👋</tg-emoji><b>RAM:</b> {_cached_ram_percent:.0f}/100%</blockquote>'
    )


async def stats_updater():
    while True:
        update_system_stats()
        await asyncio.sleep(60)
