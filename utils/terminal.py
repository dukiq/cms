import subprocess
import os
import time
import threading
import select
from typing import Optional


class TerminalSession:
    def __init__(self):
        self.sessions = {}
        self.live_buffers = {}
        self.live_complete = {}

    def create_session(self, user_id: int) -> subprocess.Popen:
        """Создает новую чистую bash сессию для каждого пользователя"""
        env = {
            "PATH": "/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin",
            "HOME": os.path.expanduser("~"),
            "USER": os.environ.get("USER", "user"),
            "SHELL": "/bin/bash",
            "TERM": "xterm-256color",
            "HISTFILE": f"/tmp/.bash_history_{user_id}",
            "HISTSIZE": "1000",
            "HISTFILESIZE": "2000",
        }

        process = subprocess.Popen(
            ["/bin/bash", "--norc", "--noprofile"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=0,
            env=env
        )

        # Включаем историю
        init_cmd = "set -o history\n"
        process.stdin.write(init_cmd)
        process.stdin.flush()
        time.sleep(0.05)

        self.sessions[user_id] = process
        return process

    def execute_command(self, user_id: int, command: str) -> tuple[str, str]:
        """Выполняет команду в bash сессии. Возвращает (output, venv_name)"""
        if user_id not in self.sessions:
            self.create_session(user_id)

        process = self.sessions[user_id]

        if process.poll() is not None:
            self.create_session(user_id)
            process = self.sessions[user_id]

        try:
            marker = f"___END_OF_COMMAND_{time.time()}___"
            env_marker = f"___VENV_{time.time()}___"
            full_command = f"{command}\necho '{marker}'\necho '{env_marker}:'${{VIRTUAL_ENV##*/}}\n"

            process.stdin.write(full_command)
            process.stdin.flush()

            output_lines = []
            venv_name = ""

            while True:
                line = process.stdout.readline()
                if marker in line:
                    continue
                if env_marker in line:
                    venv_name = line.split(":", 1)[1].strip() if ":" in line else ""
                    break
                output_lines.append(line)

            output = "".join(output_lines).strip()
            return (output if output else "0", venv_name)

        except Exception as e:
            return (f"Ошибка выполнения: {str(e)}", "")

    def close_session(self, user_id: int) -> None:
        """Закрывает bash сессию"""
        if user_id in self.sessions:
            process = self.sessions[user_id]
            try:
                process.stdin.close()
                process.terminate()
                process.wait(timeout=2)
            except:
                process.kill()
            del self.sessions[user_id]

    def has_session(self, user_id: int) -> bool:
        """Проверяет наличие активной сессии"""
        return user_id in self.sessions

    def _read_output_thread(self, user_id: int, process: subprocess.Popen, marker: str, env_marker: str):
        """Поток для чтения вывода команды"""
        output_lines = []
        venv_name = ""
        last_activity = time.time()
        has_output = False
        empty_reads = 0

        try:
            while True:
                ready, _, _ = select.select([process.stdout], [], [], 0.5)

                if ready:
                    line = process.stdout.readline()
                    last_activity = time.time()
                    empty_reads = 0

                    if not line:
                        break

                    if marker in line:
                        continue
                    if env_marker in line:
                        venv_name = line.split(":", 1)[1].strip() if ":" in line else ""
                        break

                    output_lines.append(line)
                    has_output = True
                    self.live_buffers[user_id] = {
                        "output": "".join(output_lines),
                        "venv": venv_name
                    }
                else:
                    empty_reads += 1
                    timeout = 30 if has_output else 10

                    if time.time() - last_activity > timeout:
                        break

            final_output = "".join(output_lines).strip()

            # Фильтруем маркеры если они попали в вывод
            if "___END_OF_COMMAND" in final_output or "___VENV" in final_output:
                lines = final_output.split("\n")
                lines = [l for l in lines if not ("___END_OF_COMMAND" in l or "___VENV" in l)]
                final_output = "\n".join(lines).strip()

            self.live_buffers[user_id] = {
                "output": final_output if final_output else "0",
                "venv": venv_name
            }
            self.live_complete[user_id] = True

        except Exception as e:
            self.live_buffers[user_id] = {
                "output": f"Ошибка выполнения: {str(e)}",
                "venv": ""
            }
            self.live_complete[user_id] = True

    def execute_command_live(self, user_id: int, command: str):
        """Запускает команду в live режиме"""
        if user_id not in self.sessions:
            self.create_session(user_id)

        process = self.sessions[user_id]

        if process.poll() is not None:
            self.create_session(user_id)
            process = self.sessions[user_id]

        self.live_buffers[user_id] = {"output": "", "venv": ""}
        self.live_complete[user_id] = False

        marker = f"___END_OF_COMMAND_{time.time()}___"
        env_marker = f"___VENV_{time.time()}___"
        full_command = f"{command}\necho '{marker}'\necho '{env_marker}:'${{VIRTUAL_ENV##*/}}\n"

        process.stdin.write(full_command)
        process.stdin.flush()

        thread = threading.Thread(
            target=self._read_output_thread,
            args=(user_id, process, marker, env_marker)
        )
        thread.daemon = True
        thread.start()

    def get_live_output(self, user_id: int) -> tuple[str, str, bool]:
        """Получает текущий вывод live команды. Возвращает (output, venv_name, is_complete)"""
        if user_id not in self.live_buffers:
            return ("", "", True)

        buffer = self.live_buffers[user_id]
        is_complete = self.live_complete.get(user_id, False)

        output = buffer["output"]
        if len(output) > 4000:
            lines = output.split("\n")
            while len("\n".join(lines)) > 4000 and len(lines) > 1:
                lines.pop(0)
            output = "\n".join(lines)

        return (output if output else "0", buffer["venv"], is_complete)

    def cleanup_live(self, user_id: int):
        """Очищает буферы live режима"""
        self.live_buffers.pop(user_id, None)
        self.live_complete.pop(user_id, None)


terminal_manager = TerminalSession()
