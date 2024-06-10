def hello_text(username):
    return f"""
        Здравствуйте, {username}! \nЭтот бот поможет вам запоминать информацию, напоминая повторять ее с определенной частотой.
    """

def reminder_text(question):
    return f"У вас новое напоминание!\nОтветьте на вопрос:\n    {question}"


def show_summary_text(question, answer, days):
    return f"Запись успешно сохранена. \nВопрос:\n    {question} \nОтвет:\n    <tg-spoiler>{answer}</tg-spoiler> \nЦель запоминания: \n    {days}"

do_not_change_keyboard_text = "Оставить неизменным"



