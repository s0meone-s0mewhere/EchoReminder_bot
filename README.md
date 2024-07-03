# RU
---
# EchoReminder - бот для запоминания информации
## Концепция
Этот бот помогает запоминать информацию, присылая карточки с вопросами через определенные промежутки времени. В основе этой концепции лежит кривая забывания.

## Функционал
У бота есть следующие основные команды:
- `/start` - запускает бота и выводит приветственное сообщение с кратким описанием возможностей
- `/help` - просмотр доступных команд с кратким описанием
- `/new_reminder` - создает новую запись. Запускает диалог, в котором запрашивается вопрос, затем ответ, а также цель запоминания (запомнить надолго или запомнить за 2 дня, от этого зависит с какой периодичностью будут присылаться карточки с вопросами). После ввода ответа сообщение автоматически удаляется.
- `/update_reminder` - изменяет запись. Запускается диалог, в котором показываются все действующие записи и их id. Нужно прислать этот id, а затем будет предложено изменить поля или оставить неизменными.
- `/delete_reminder` - удаляет запись. Сначала будут выведены активные записи, а затем нужно будет ввести id записи, которую нужно удалить.
- `/cancel` - отменяет диалоги.
  

## Сборщик мусора
Бот имеет систему сборки неактивных записей. Когда присылается последнее уведомление, запись становится неактивной, она будет удалена через 2 дня.

## Анти-спам система
Также реализована анти-спам система, которая позволяет защитить бота от DOS атак. Этот функционал реализован с помощью мидлвари, которая при первом вводе команды записывает в словарь id пользователя в качестве ключа, а также кортеж в виде названия команды и времени ее ввода. Если команда будет введена повторно, то будет выполнена проверка, прошло ли 10 секунд с прошлого ввода, если да то запрос передается хэндлеру, а если не прошло 10 секунд, то команда обрабатываться не будет.