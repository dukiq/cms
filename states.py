from aiogram.fsm.state import State, StatesGroup


class TerminalStates(StatesGroup):
    waiting_command = State()


class AdminStates(StatesGroup):
    waiting_add_id = State()
    waiting_remove_id = State()


class ProjectStates(StatesGroup):
    waiting_name = State()
    waiting_path = State()
    waiting_delete_password = State()
