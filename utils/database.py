import sqlite3
from pathlib import Path
from typing import Optional


DB_PATH = Path(__file__).parent.parent / "cms.db"


def init_database():
    """Инициализирует базу данных и создает таблицы"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            name TEXT PRIMARY KEY,
            param TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS admins (
            user_id INTEGER PRIMARY KEY
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            path TEXT NOT NULL,
            network TEXT,
            volumes TEXT
        )
    """)

    conn.commit()
    conn.close()


def get_setting(name: str) -> Optional[str]:
    """Получает значение настройки по имени"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT param FROM settings WHERE name = ?", (name,))
    result = cursor.fetchone()

    conn.close()
    return result[0] if result else None


def set_setting(name: str, param: str):
    """Устанавливает или обновляет настройку"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO settings (name, param) VALUES (?, ?)
        ON CONFLICT(name) DO UPDATE SET param = excluded.param
    """, (name, param))

    conn.commit()
    conn.close()


def delete_setting(name: str):
    """Удаляет настройку"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("DELETE FROM settings WHERE name = ?", (name,))

    conn.commit()
    conn.close()


def get_all_settings() -> list[tuple[str, str]]:
    """Получает все настройки"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT name, param FROM settings")
    results = cursor.fetchall()

    conn.close()
    return results


def add_admin(user_id: int) -> bool:
    """Добавляет админа в БД"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        cursor.execute("INSERT INTO admins (user_id) VALUES (?)", (user_id,))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        conn.close()
        return False


def remove_admin(user_id: int) -> bool:
    """Удаляет админа из БД"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("DELETE FROM admins WHERE user_id = ?", (user_id,))
    deleted = cursor.rowcount > 0

    conn.commit()
    conn.close()
    return deleted


def is_admin(user_id: int) -> bool:
    """Проверяет является ли пользователь админом"""
    from config import ADMIN_ID

    if user_id == ADMIN_ID:
        return True

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT 1 FROM admins WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()

    conn.close()
    return result is not None


def get_all_admins() -> list[int]:
    """Получает список всех админов"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT user_id FROM admins")
    results = cursor.fetchall()

    conn.close()
    return [row[0] for row in results]


def add_project(name: str, path: str, network: str = "", volumes: str = "") -> int:
    """Добавляет проект в БД"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO projects (name, path, network, volumes)
        VALUES (?, ?, ?, ?)
    """, (name, path, network, volumes))

    project_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return project_id


def get_project(project_id: int) -> Optional[tuple]:
    """Получает проект по ID"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT id, name, path, network, volumes FROM projects WHERE id = ?", (project_id,))
    result = cursor.fetchone()

    conn.close()
    return result


def get_all_projects() -> list[tuple]:
    """Получает все проекты"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT id, name, path, network, volumes FROM projects")
    results = cursor.fetchall()

    conn.close()
    return results


def delete_project(project_id: int) -> bool:
    """Удаляет проект"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("DELETE FROM projects WHERE id = ?", (project_id,))
    deleted = cursor.rowcount > 0

    conn.commit()
    conn.close()
    return deleted


def update_project(project_id: int, network: str = None, volumes: str = None) -> bool:
    """Обновляет информацию о проекте"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    updates = []
    values = []

    if network is not None:
        updates.append("network = ?")
        values.append(network)

    if volumes is not None:
        updates.append("volumes = ?")
        values.append(volumes)

    if not updates:
        conn.close()
        return False

    values.append(project_id)
    query = f"UPDATE projects SET {', '.join(updates)} WHERE id = ?"

    cursor.execute(query, values)
    updated = cursor.rowcount > 0

    conn.commit()
    conn.close()
    return updated
