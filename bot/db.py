from sqlalchemy import create_engine, Integer, String, Column, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
import datetime
from sqlalchemy.orm import relationship, Session
import texts
import logging
import asyncio
import config
import os

Base = declarative_base()

current_dir = os.getcwd()
parent_dir = os.path.abspath(os.path.join(current_dir, os.pardir))
file_path = os.path.join(parent_dir, 'db_password.txt')

with open(file_path, "r") as file:
    engine = create_engine(f'postgresql+psycopg2://postgres:{file.read()}@{os.getenv("DB_HOST") if os.getenv("DB_HOST") else "localhost" }:5432/reminderdb')

class Reminder(Base):
    __tablename__ = 'reminders'
    id = Column(Integer, primary_key=True)
    chat_id = Column(Integer, nullable=False)
    question = Column(String(4096), nullable=False)
    answer = Column(String(4096), nullable=False)
    created_on = Column(DateTime(), default=datetime.datetime.now)
    delete_on = Column(DateTime(), nullable=False)
    remind_dates = relationship("ReminderDate", back_populates="reminder", overlaps="remind_dates", cascade="all, delete-orphan")

class ReminderDate(Base):
    __tablename__ = 'reminder_dates'
    id = Column(Integer, primary_key=True)
    date = Column(DateTime, nullable=False)
    reminder_id = Column(Integer, ForeignKey('reminders.id'))
    reminder = relationship("Reminder", back_populates="remind_dates")

Base.metadata.create_all(engine)
session = Session(bind=engine)

def create_new_reminder(chat_id, question, answer, days, scheduler):
    with session:
        reminder = Reminder(chat_id=chat_id, question=question, answer=answer)

        if days == "Запомнить за 2 дня":
            first_remind = datetime.datetime.now() + datetime.timedelta(minutes=10)
            second_remind = first_remind + datetime.timedelta(hours=8)
            third_remind = second_remind + datetime.timedelta(hours=24)
            reminder.delete_on = third_remind + datetime.timedelta(days=2)

            for date in first_remind, second_remind, third_remind:
               scheduler.add_job(reminder=reminder, date=date)

        elif days == "Запомнить надолго":
            first_remind = datetime.datetime.now() + datetime.timedelta(minutes=20)
            second_remind = first_remind + datetime.timedelta(days=1)
            third_remind = second_remind + datetime.timedelta(weeks=2)
            fourth_remind = third_remind + datetime.timedelta(weeks=9)
            reminder.delete_on = fourth_remind + datetime.timedelta(days=2)

            for date in first_remind, second_remind, third_remind, fourth_remind:
                scheduler.add_job(reminder=reminder, date=date)
        
        session.add(reminder)
        session.commit()


async def get_reminder(reminder_id):
    return session.query(Reminder).get(reminder_id)


async def delete_reminder(reminder_id):
    with session:
        reminder = await get_reminder(reminder_id)
        session.delete(reminder)
        session.commit()


async def update_reminder(reminder_id, question, answer):
        with session:
            reminder = await get_reminder(reminder_id)
            if reminder:
                if question != texts.do_not_change_keyboard_text:
                    reminder.question = question

                if answer != texts.do_not_change_keyboard_text:
                    reminder.answer = answer

                session.add(reminder)
                session.commit()


async def get_all_reminders(chat_id):
    with session:
        reminders = session.query(Reminder).filter(Reminder.chat_id == chat_id).order_by(Reminder.created_on).all()
        return [
            {
                "id": reminder.id,
                "question": reminder.question,
                "answer": reminder.answer,
            }
            for reminder in reminders
        ]
    

async def reminders_garbage_collector():
    logging.info("reminders garbage collector is working")
    while True:
        reminders = session.query(Reminder).all()
        active_reminders = session.query(Reminder).filter(Reminder.delete_on > datetime.datetime.now()).all()
        for reminder in reminders:
            if not reminder in active_reminders:
                with session:
                    session.delete(reminder)
                    session.commit()
        await asyncio.sleep(100)