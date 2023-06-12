from aiogram.dispatcher.filters.state import StatesGroup, State


class AddCard(StatesGroup):
    card_number = State()
    card_nickname = State()
    confirm = State()


class ShowCard(StatesGroup):
    show_card_number = State()
