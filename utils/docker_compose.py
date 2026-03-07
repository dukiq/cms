import os
import yaml
from pathlib import Path


def parse_docker_compose(project_path: str) -> tuple[str, str]:
    """
    Парсит docker-compose.yml и возвращает (networks, volumes)
    """
    compose_files = ["docker-compose.yml", "docker-compose.yaml", "compose.yml", "compose.yaml"]

    compose_path = None
    for filename in compose_files:
        path = Path(project_path) / filename
        if path.exists():
            compose_path = path
            break

    if not compose_path:
        return "", ""

    try:
        with open(compose_path, 'r') as f:
            compose_data = yaml.safe_load(f)

        # Получаем networks
        networks = []
        if 'networks' in compose_data and compose_data['networks']:
            networks = list(compose_data['networks'].keys())

        # Получаем volumes
        volumes = []
        if 'volumes' in compose_data and compose_data['volumes']:
            volumes = list(compose_data['volumes'].keys())

        networks_str = ", ".join(networks) if networks else ""
        volumes_str = ", ".join(volumes) if volumes else ""

        return networks_str, volumes_str

    except Exception as e:
        print(f"Error parsing docker-compose.yml: {e}")
        return "", ""
