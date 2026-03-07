import subprocess
import os
from datetime import datetime
from pathlib import Path


async def restart_project(project_path: str) -> tuple[str, str]:
    """Перезапускает проект"""
    try:
        result = subprocess.run(
            "docker compose down && docker compose up -d",
            shell=True,
            cwd=project_path,
            capture_output=True,
            text=True,
            timeout=60
        )
        output = result.stdout + result.stderr
        return output, ""
    except Exception as e:
        return "", str(e)


async def rebuild_project(project_path: str) -> tuple[str, str]:
    """Пересобирает проект"""
    try:
        result = subprocess.run(
            "docker compose down && docker builder prune -f && docker compose build --no-cache && docker compose up -d",
            shell=True,
            cwd=project_path,
            capture_output=True,
            text=True,
            timeout=300
        )
        output = result.stdout + result.stderr
        error_file = ""

        if result.returncode != 0:
            filename = f"rebuild_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            filepath = Path("/tmp") / filename
            with open(filepath, "w") as f:
                f.write(output)
            error_file = str(filepath)

        return output, error_file
    except Exception as e:
        return "", str(e)


async def stop_project(project_path: str) -> tuple[bool, str]:
    """Останавливает проект"""
    try:
        result = subprocess.run(
            ["docker", "compose", "down"],
            cwd=project_path,
            capture_output=True,
            text=True,
            timeout=60
        )
        return result.returncode == 0, result.stdout + result.stderr
    except Exception as e:
        return False, str(e)


async def start_project(project_path: str) -> tuple[bool, str]:
    """Запускает проект"""
    try:
        result = subprocess.run(
            ["docker", "compose", "up", "-d"],
            cwd=project_path,
            capture_output=True,
            text=True,
            timeout=60
        )
        return result.returncode == 0, result.stdout + result.stderr
    except Exception as e:
        return False, str(e)


async def git_pull(project_path: str) -> tuple[str, str]:
    """Выполняет git pull"""
    try:
        result = subprocess.run(
            ["git", "pull"],
            cwd=project_path,
            capture_output=True,
            text=True,
            timeout=60
        )
        output = result.stdout + result.stderr
        error_file = ""

        if result.returncode != 0:
            filename = f"pull_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            filepath = Path("/tmp") / filename
            with open(filepath, "w") as f:
                f.write(output)
            error_file = str(filepath)

        return output, error_file
    except Exception as e:
        return "", str(e)
