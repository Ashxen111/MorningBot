from aiogram.fsm.state import StatesGroup, State


from aiogram.fsm.state import State, StatesGroup


class UserStates(StatesGroup):
    waiting_for_focus = State()
    waiting_for_tasks = State()
    waiting_for_time = State()
