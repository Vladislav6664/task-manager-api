from aiogram.fsm.state import State, StatesGroup


class CreateTaskStates(StatesGroup):
    waiting_for_title = State()
    waiting_for_description = State()
    waiting_for_priority = State()
    waiting_for_edit_title = State()
    waiting_for_edit_description = State()
    waiting_for_edit_priority = State()
