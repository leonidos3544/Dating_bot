import os
import asyncpg
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message


BOT_TOKEN = os.getenv("BOT_TOKEN")
DB_HOST = os.getenv("DB_HOST", "db")
DB_USER = os.getenv("DB_USER", "bot_user")
DB_PASSWORD = os.getenv("DB_PASSWORD", "secret")
DB_NAME = os.getenv("DB_NAME", "dating_db")
DB_DSN = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

class ProfileForm(StatesGroup):
    name = State()
    age = State()
    bio = State()

@dp.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(
        " Привет! Это бот для знакомств.\n\n"
        " /reg — создать или обновить свою анкету\n"
        " /next — получить случайную анкету"
    )

@dp.message(Command("reg"))
async def cmd_reg(message: Message, state: FSMContext):
    await message.answer("Как тебя зовут?")
    await state.set_state(ProfileForm.name)

@dp.message(ProfileForm.name)
async def process_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text.strip())
    await message.answer("Сколько тебе лет?")
    await state.set_state(ProfileForm.age)

@dp.message(ProfileForm.age, F.text.isdigit())
async def process_age(message: Message, state: FSMContext):
    age = int(message.text)
    await state.update_data(age=age)
    await message.answer("Расскажи о себе в двух словах:")
    await state.set_state(ProfileForm.bio)


@dp.message(ProfileForm.bio)
async def process_bio(message: Message, state: FSMContext):
    data = await state.get_data()
    conn = await asyncpg.connect(dsn=DB_DSN)
    try:
        await conn.execute(
            """INSERT INTO profiles (tg_user_id, name, age, bio) 
               VALUES ($1, $2, $3, $4)
               ON CONFLICT (tg_user_id) DO UPDATE SET 
               name=EXCLUDED.name, age=EXCLUDED.age, bio=EXCLUDED.bio""",
            message.from_user.id, data["name"], data["age"], message.text.strip()
        )
        await message.answer("Анкета успешно сохранена! Жми /next для поиска.")
    except Exception as e:
        await message.answer(f"Ошибка сохранения: {e}")
    finally:
        await conn.close()
    await state.clear()

@dp.message(Command("next"))
async def cmd_next(message: Message):
    conn = await asyncpg.connect(dsn=DB_DSN)
    try:
        row = await conn.fetchrow(
            "SELECT name, age, bio FROM profiles WHERE tg_user_id != $1 ORDER BY RANDOM() LIMIT 1",
            message.from_user.id
        )
        if row:
            await message.answer(f"👤 {row['name']}, {row['age']} лет\n📝 {row['bio']}")
    except Exception as e:
        await message.answer(f"Ошибка базы данных: {e}")
    finally:
        await conn.close()

@dp.message()
async def fallback(message: Message):
    await message.answer("Используй команды: /start, /reg, /next")

async def main():
    try:
        conn = await asyncpg.connect(dsn=DB_DSN)
        await conn.close()
        print("Подключение к PostgreSQL успешно")
    except Exception as e:
        print(f"Ошибка подключения к БД: {e}")
        return

    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
