import asyncio
import logging
import sys
from os import getenv
import db
import config
from middlewares import CancelMiddleware, AntiSpamMessageMiddlware, AntiSpamCallbackQueryMiddleware
from aiogram import Bot, Dispatcher, Router, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, Command
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import KeyboardButton, Message, ReplyKeyboardMarkup, ReplyKeyboardRemove, CallbackQuery
from scheduler import Scheduler
import re
import texts


TOKEN = config.TOKEN

bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()
form_router = Router()
scheduler = Scheduler(engine=db.engine)
router = Router()


class UpdateReminder(StatesGroup):
    select_reminder = State()
    question = State()
    answer = State()

class DeleteReminder(StatesGroup):
    select_reminder = State()

class NewReminder(StatesGroup):
    question = State()
    answer = State()
    days = State()


@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    await message.answer(texts.hello_text(message.from_user.full_name))


@dp.message(Command("new_reminder"))
async def new_reminder(message: Message, state: FSMContext) -> None:
    await state.set_state(NewReminder.question)
    await message.answer(
        "Введите вопрос",
        reply_markup=ReplyKeyboardRemove(),
    )


@dp.message(NewReminder.question)
async def process_question(message: Message, state: FSMContext) -> None:
    await state.update_data(question=message.text)
    await state.set_state(NewReminder.answer)
    await message.answer(
        f"Введите ответ",
        reply_markup=ReplyKeyboardRemove()
    )


@dp.message(NewReminder.answer)
async def process_answer(message: Message, state: FSMContext) -> None:
    await state.update_data(answer=message.text)
    await state.set_state(NewReminder.days)
    kb = [
        [
            KeyboardButton(text="Запомнить за 2 дня"),
            KeyboardButton(text="Запомнить надолго")
        ],
    ]
    keyboard = ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True,
        input_field_placeholder=""
    )
    await message.answer(
        f"Введите цель запоминания",
        reply_markup=keyboard
    )
    await message.delete()


@dp.message(NewReminder.days)
async def process_days(message: Message, state: FSMContext) -> None:
    data = await state.update_data(days=message.text)
    question = data["question"]
    answer = data["answer"]
    days = data["days"]
    chat_id = message.chat.id
    await state.clear()
    db.create_new_reminder(chat_id, question, answer, days, scheduler)
    await show_summary(message=message, question=question, answer=answer, days=days)


@dp.message(Command("delete_reminder"))
async def delete_reminder(message: Message, state: FSMContext) -> None:
    await state.set_state(DeleteReminder.select_reminder)
    all_reminders = await db.get_all_reminders(message.chat.id)
    
    if not all_reminders:
        await message.answer("У вас пока нет записей")
        return

    reminder_list = "\n".join(
        f"{reminder['id']}. {reminder['question']}" for reminder in all_reminders
    )

    await message.answer(f"Вот ваши записи\n{reminder_list}")
    await message.answer(
        "Введите id записи",
        reply_markup=ReplyKeyboardRemove(),
    )


@dp.message(DeleteReminder.select_reminder)
async def process_choose_remind(message: Message, state: FSMContext) -> None:
    id = message.text
    await state.clear()
    await db.delete_reminder(id)
    await message.answer(
        f"Запись успешно удалена",
        reply_markup=ReplyKeyboardRemove()
    )


@dp.message(Command("update_reminder"))
async def update_reminder(message: Message, state: FSMContext) -> None:
    await state.set_state(UpdateReminder.select_reminder)
    all_reminders = await db.get_all_reminders(message.chat.id)
    
    if not all_reminders:
        await state.clear()
        await message.answer("У вас пока нет записей")
        return

    reminder_list = "\n".join(
        f"{reminder['id']}. {reminder['question']}" for reminder in all_reminders
    )

    await message.answer(f"Вот ваши активные записи\n{reminder_list}")
    await message.answer(
        "Введите id записи",
        reply_markup=ReplyKeyboardRemove(),
    )


do_not_change_keyboard = [
        [
            KeyboardButton(text=texts.do_not_change_keyboard_text),
        ],
    ]


@dp.message(UpdateReminder.select_reminder)
async def process_choose_reminder(message: Message, state: FSMContext) -> None:
    if re.match(r'^\d+$', message.text):
        if await db.get_reminder(int(message.text)):
            await state.update_data(id=message.text)
            await state.set_state(UpdateReminder.question)
            keyboard = ReplyKeyboardMarkup(
                keyboard=do_not_change_keyboard,
                resize_keyboard=True,
                input_field_placeholder=""
            )
            await message.answer(
                f"Введите вопрос или нажмите на кнопку \"{texts.do_not_change_keyboard_text}\"",
                reply_markup=keyboard
            )
        else:
            await state.clear()
            await message.answer(f"Запись с id {message.text} не существует", reply_markup=ReplyKeyboardRemove())
    else:
        await state.clear()
        await message.answer(f"Введен некорректный id записи", reply_markup=ReplyKeyboardRemove())


@dp.message(UpdateReminder.question)
async def process_update_question(message: Message, state: FSMContext) -> None:
    await state.update_data(question=message.text)
    await state.set_state(UpdateReminder.answer)
    keyboard = ReplyKeyboardMarkup(
        keyboard=do_not_change_keyboard,
        resize_keyboard=True,
        input_field_placeholder=""
    )
    await message.answer(
        f"Введите ответ или нажмите на кнопку \"{texts.do_not_change_keyboard_text}\"",
        reply_markup=keyboard
    )


@dp.message(UpdateReminder.answer)
async def process_update_answer(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    reminder_id = data["id"]
    question = data["question"]
    answer = message.text
    await db.update_reminder(reminder_id, question, answer)
    await message.delete()
    await state.clear()
    await message.answer(
        f"Именения приняты успешно",
        reply_markup=ReplyKeyboardRemove()
    )


async def show_summary(message: Message, question, answer, days) -> None:
    text = texts.show_summary_text(question, answer, days)
    await message.answer(text=text, reply_markup=ReplyKeyboardRemove(), parse_mode="HTML")


    

@dp.callback_query(F.data.startswith("reminder_"))
async def get_reminder_answer(callback: CallbackQuery):
    reminder_id = callback.data.split("_")[1]
    reminder = await db.get_reminder(reminder_id)
    
    try: 
        await callback.message.answer(f"<tg-spoiler>{reminder.answer}</tg-spoiler>", parse_mode="HTML")
    except AttributeError:
        await callback.message.answer(f"Запись отсутствует")

    await callback.answer()

commands = {
    '/start': 'Нажмите для запуска бота', 
    '/help': 'Нажмите для просмотра доступных команд', 
    '/new_reminder': 'Создать новую запись',
    '/delete_reminder': 'Удаляет запись',
    '/update_reminder': 'Изменяет запись', 
}

@dp.message(Command("help"))
async def help(message: Message):
    command_list = "\n".join(
        f"{command} - {discription}" for command, discription in commands.items()
    )
    await message.answer(f'{command_list}')

async def main() -> None:
    dp.message.outer_middleware(CancelMiddleware())
    dp.message.outer_middleware(AntiSpamMessageMiddlware())
    dp.callback_query.outer_middleware(AntiSpamCallbackQueryMiddleware())
    await asyncio.gather(
        dp.start_polling(bot),
        scheduler.start(),
        db.reminders_garbage_collector()
    )
    await bot.close()


if __name__ == "__main__":
    try:
        logging.basicConfig(level=logging.INFO, stream=sys.stdout, format="%(asctime)s %(levelname)s %(message)s")
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Bot stopped")