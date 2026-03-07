import subprocess
import asyncio

_cached_containers_count = 0
_cached_networks_count = 0


def update_docker_stats():
    global _cached_containers_count, _cached_networks_count

    try:
        result = subprocess.run(
            ["docker", "ps", "-q"],
            capture_output=True,
            text=True,
            timeout=5
        )
        containers = result.stdout.strip().split("\n")
        _cached_containers_count = len([c for c in containers if c])

        result = subprocess.run(
            ["docker", "network", "ls", "--format", "{{.Name}}"],
            capture_output=True,
            text=True,
            timeout=5
        )
        networks = result.stdout.strip().split("\n")
        default_networks = {"bridge", "host", "none"}
        custom_networks = [n for n in networks if n and n not in default_networks]
        _cached_networks_count = len(custom_networks)

    except Exception as e:
        print(f"Error updating docker stats: {e}")


def get_docker_stats() -> tuple[int, int]:
    return _cached_containers_count, _cached_networks_count


def format_docker_stats() -> str:
    containers, networks = get_docker_stats()

    return (
        f'<tg-emoji emoji-id=\'5172928932801938153\'>👋</tg-emoji> <b>Docker</b>\n'
        f'<blockquote><tg-emoji emoji-id=\'5174696127160648257\'>👋</tg-emoji><b> Сети:</b> {networks}\n'
        f'<tg-emoji emoji-id=\'5172494668658639634\'>👋</tg-emoji> <b>Контейнеры:</b> {containers}</blockquote>'
    )


async def docker_stats_updater():
    while True:
        update_docker_stats()
        await asyncio.sleep(60)


def get_project_containers_count(project_path: str = None, network: str = None) -> int:
    try:
        if network:
            result = subprocess.run(
                ["docker", "ps", "-q", "--filter", f"network={network}"],
                capture_output=True,
                text=True,
                timeout=5
            )
        else:
            result = subprocess.run(
                ["docker", "compose", "ps", "-q"],
                cwd=project_path,
                capture_output=True,
                text=True,
                timeout=5
            )
        containers = result.stdout.strip().split("\n")
        return len([c for c in containers if c])
    except Exception:
        return 0


def is_project_running(project_path: str = None, network: str = None) -> bool:
    return get_project_containers_count(project_path, network) > 0
