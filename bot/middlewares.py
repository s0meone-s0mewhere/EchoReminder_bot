from typing import Any, Awaitable, Callable, Coroutine, Dict
from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject, BotCommand, CallbackQuery
from datetime import datetime, timedelta


class CancelMiddleware(BaseMiddleware):
    async def __call__(self, handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]], event: Message, data: Dict[str, Any]) -> Coroutine[Any, Any, Any]: 
        if data["raw_state"] and event.text == "/cancel":
            await data["state"].clear()
            await event.answer("Отменено")
            return
        else:
            return await handler(event, data)
        

class AntiSpamMessageMiddlware(BaseMiddleware):
    last_time = {}
    #{"chat_id": (date, text)}
    async def __call__(self, handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]], event: BotCommand, data: Dict[str, Any]) -> Any:
        if event.chat.id not in self.last_time:
            self.last_time[event.chat.id] = (datetime.now(), event.text)
            return await handler(event, data)
        if self.last_time[event.chat.id][1] == event.text:
            if not data["raw_state"]:
                if datetime.now() - self.last_time[event.chat.id][0] > timedelta(seconds=10):
                    self.last_time[event.chat.id] = (datetime.now(), event.text)

                    return await handler(event, data)
            else:
                return await handler(event, data)  
        else: 
            self.last_time[event.chat.id] = (datetime.now(), event.text)
            return await handler(event, data)


class AntiSpamCallbackQueryMiddleware(BaseMiddleware):
    last_time = {}

    async def __call__(self, handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]], event: CallbackQuery, data: Dict[str, Any]) -> Any:
        if event.data not in self.last_time:
            self.last_time[event.data] = datetime.now()
            return await handler(event, data)
        
        if datetime.now() - self.last_time[event.data] > timedelta(seconds=10):
            self.last_time[event.data] = datetime.now()
            return await handler(event, data)

