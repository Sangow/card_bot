from aiogram.dispatcher.filters.state import StatesGroup, State


class AddCard(StatesGroup):
    # The nickname goes first, so the card number is saved as soon as it is
    # entered and never kept in the conversation state
    card_nickname = State()
    card_number = State()


class ShowCard(StatesGroup):
    edit_card_number = State()
    edit_card_nickname = State()
