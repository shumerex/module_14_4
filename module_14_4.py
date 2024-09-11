from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.types import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton, KeyboardButton
import crud_functions as db
import sqlite3
from http.client import responses
from itertools import product

API_TOKEN = ""
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())

class UserState(StatesGroup):
    age = State()
    growth = State()
    weight = State()

db.initiate_db()

# def populate_data():
#     conn = sqlite3.connect('products.db')
#     cursor = conn.cursor()
#     products = [
#         ("Продукт 1", "Описание 1", 100),
#         ("Продукт 2", "Описание 2", 200),
#         ("Продукт 3", "Описание 3", 300),
#         ("Продукт 4", "Описание 4", 400)
#     ]
#     cursor.executemany('INSERT INTO Products (title, description, price) VALUES (?, ?, ?)', products)
#     conn.commit()
#     conn.close()
#
# populate_data()

keyboard = ReplyKeyboardMarkup(resize_keyboard=True).add("Рассчитать", "Информация", "Купить")
kb = InlineKeyboardMarkup().add(
    InlineKeyboardButton(text="Рассчитать норму калорий", callback_data="calories"),
    InlineKeyboardButton(text='Формула расчёта', callback_data='formulas'),
)
buying_kb = InlineKeyboardMarkup().add(
    InlineKeyboardButton(text="Product1", callback_data="product_buying"),
    InlineKeyboardButton(text="Product2", callback_data="product_buying"),
    InlineKeyboardButton(text="Product3", callback_data="product_buying"),
    InlineKeyboardButton(text="Product4", callback_data="product_buying"),
)
@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    await message.reply("Привет! Я бот, помогающий твоему здоровью.", reply_markup=keyboard)


@dp.message_handler(Text(equals="Рассчитать"))
async def main_menu(message: types.Message):
    await message.answer("Выберите опцию:", reply_markup=kb)

@dp.callback_query_handler(Text(equals='formulas'))
async def get_formulas(call: types.CallbackQuery):
    await call.message.answer("Формула Миффлина-Сан Жеора:\n"
                               "BMR = 10 * вес (кг) + 6.25 * рост (см) - 5 * возраст (годы) + 5")
    await call.answer()

@dp.callback_query_handler(Text(equals="calories"))
async def set_age(call: types.CallbackQuery):
    await call.message.answer("Введите свой возраст:")
    await UserState.age.set()
    await call.answer()

@dp.message_handler(state=UserState.age)
async def set_growth(message: types.Message, state: FSMContext):
    await state.update_data(age=message.text)
    await message.answer("Введите свой рост:")
    await UserState.growth.set()

@dp.message_handler(state=UserState.growth)
async def set_weight(message: types.Message, state: FSMContext):
    await state.update_data(growth=message.text)
    await message.answer("Введите свой вес:")
    await UserState.weight.set()

@dp.message_handler(state=UserState.weight)
async def send_calories(message: types.Message, state: FSMContext):
    await state.update_data(weight=message.text)
    data = await state.get_data()

    age = int(data['age'])
    growth = int(data['growth'])
    weight = int(data['weight'])

    calories = 10 * weight + 6.25 * growth - 5 * age + 5  # Формула для мужчин

    await message.answer(f"Ваша норма калорий: {calories:.2f} ккал")
    await state.finish()

@dp.message_handler(text="Купить")
async def get_buying_list(message: types.Message):
    products = db.get_all_products()
    response = "Доступные продукты:\n\n"

    for product in products:
        title, description, price = product
        response += f"Название: {title} | Описание: {description} | Цена: {price}\n"

        with open('1.jpg', 'rb') as img:
            await message.answer_photo(img, reply_markup=buying_kb)

    await message.answer(response)

@dp.callback_query_handler(lambda call: call.data == "product_buying")
async def send_confirm_message(call: types.CallbackQuery):
    await call.message.answer('Вы успешно приобрели продукт!')
    await call.answer()

@dp.message_handler()
async def all_messages(message: types.Message):
    await message.reply("Введи команду /start для начала работы с ботом.")

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
