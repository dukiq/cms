import os
import yaml
from pathlib import Path


def parse_docker_compose(project_path: str) -> tuple[str, str]:
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

        project_name = os.path.basename(project_path)

        networks = []
        if 'networks' in compose_data and compose_data['networks']:
            for net_key, net_data in compose_data['networks'].items():
                if isinstance(net_data, dict) and 'name' in net_data:
                    networks.append(net_data['name'])
                else:
                    networks.append(f"{project_name}_{net_key}")

        volumes = []
        if 'volumes' in compose_data and compose_data['volumes']:
            for vol_key, vol_data in compose_data['volumes'].items():
                if isinstance(vol_data, dict) and 'name' in vol_data:
                    volumes.append(vol_data['name'])
                else:
                    volumes.append(vol_key)

        networks_str = ", ".join(networks) if networks else ""
        volumes_str = ", ".join(volumes) if volumes else ""

        return networks_str, volumes_str

    except Exception as e:
        print(f"Error parsing docker-compose.yml: {e}")
        return "", ""
