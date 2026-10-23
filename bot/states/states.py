from aiogram.dispatcher.filters.state import StatesGroup, State


class AddCard(StatesGroup):
    card_number = State()
    card_nickname = State()


class ShowCard(StatesGroup):
    edit_card_number = State()
    edit_card_nickname = State()
