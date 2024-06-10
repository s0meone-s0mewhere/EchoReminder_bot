from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode 
from aiogram import Bot, F, Dispatcher
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton, ReplyKeyboardRemove
import config
import texts

bot = Bot(token=config.TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

async def remind(reminder):
    if reminder.id:
        builder = InlineKeyboardBuilder()
        builder.add(InlineKeyboardButton(
            text="Посмотреть ответ",
            callback_data=f"reminder_{reminder.id}")
        )
        await bot.send_message(chat_id=reminder.chat_id, text=texts.reminder_text(reminder.question), reply_markup=builder.as_markup())
    else:
        await bot.send_message(chat_id=reminder.chat_id, text=texts.reminder_text(reminder.question), reply_markup=ReplyKeyboardRemove())
