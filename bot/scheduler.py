from sqlalchemy.orm import relationship, Session
from db import ReminderDate
import datetime
import asyncio
from reminder import remind
import logging

class Scheduler:
    def __init__(self, engine) -> None:
        self.engine = engine
        self.session = Session(bind=engine)

    def add_job(self, reminder, date):
        with self.session as session:
            reminder_date = ReminderDate(date=date, reminder=reminder)
            session.add(reminder_date)
            session.commit()

    async def start(self):
        while True:
            now = datetime.datetime.now()
            with self.session as session:
                tasks = session.query(ReminderDate).filter(ReminderDate.date <= now).all()
                for task in tasks:
                    if task:
                        await remind(task.reminder)
                        session.delete(task)
                        logging.info("Message sent")
                session.commit()
            await asyncio.sleep(10)