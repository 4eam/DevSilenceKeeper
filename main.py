import telebot
import keys
import settings


def init_banlist():
    with open(settings.BANLIST_FILE) as file:
        content = file.readlines()
    words = [x.strip() for x in content]
    settings.BLOCKED_WORD_LIST = words


init_banlist()
print('Banlist loaded...')
bot = telebot.TeleBot(keys.TOKEN)
print('Signal with Telegram Bot API is established...')
print('Telegram bot is working...')


def get_command_params(message_content):
    return ' '.join(str(message_content).split()[1:])


def is_url(text):
    return text.find('/') != -1


def is_admin(message):
    admins = bot.get_chat_administrators(message.chat.id)
    admins_id = [admin.user.id for admin in admins]
    if message.from_user.id in admins_id:
        return True
    return False


def reply_and_kick(message):
    first_name = message.from_user.first_name
    last_name = message.from_user.last_name
    username = message.from_user.username
    text = 'Пользователь '
    if first_name is not None:
        text += message.from_user.first_name + ' '
    if last_name is not None:
        text += message.from_user.last_name + ' '
    if username is not None:
        text += '(@' + message.from_user.username + ') '
    text += 'нарушил второе правило чата!'
    bot.reply_to(message, text)
    bot.delete_message(message.chat.id, message.message_id)
    if not (is_admin(message)):
        bot.kick_chat_member(message.chat.id, message.from_user.id)
        bot.unban_chat_member(message.chat.id, message.from_user.id)


def add_blocked_template(template):
    banlist_file = open(settings.BANLIST_FILE, 'a')
    banlist_file.write(template + '\n')
    settings.BLOCKED_WORD_LIST.append(template)
    banlist_file.close()


def remove_blocked_template(template):
    banlist_file = open(settings.BANLIST_FILE, 'w+')
    file_content = banlist_file.readlines()
    for line in file_content:
        str(line).replace(template, '')
    banlist_file.writelines(file_content)
    settings.BLOCKED_WORD_LIST.remove(template)
    banlist_file.close()


def is_message_dangerous(message_content):
    if message_content is None:
        return False
    text = str(message_content)
    banlist_to_lower = False
    if not is_url(text):
        text = text.lower()
        banlist_to_lower = True
    for blocked_word in settings.BLOCKED_WORD_LIST:
        if banlist_to_lower:
            blocked_word = blocked_word.lower()
        if text.find(blocked_word) != -1:
            return True
    return False


@bot.message_handler(commands=['help'])
def show_help(message):
    if is_admin(message):
        answer_text = ('Я знаю следующие команды:'
                       + '\n/help — получить справку команд'
                       + '\n/showbanlist — показать список строк-шаблонов в банлисте'
                       + '\n/add {строка-шаблон} — добавить строку-шаблон в банлист'
                       + '\n/remove {строка-шаблон} — удалить строку-шаблон из банлиста'
                       + '\n/bugreport {текст проблемы} — послать разработчиков на... Кхм.. Сообщить об ошибке разработчикам'
                       + '\n\nВсе команды могут использовать только админы чата!')
        bot.send_message(message.chat.id, answer_text)


@bot.message_handler(commands=['add'])
def add_word(message):
    if is_admin(message):
        params = get_command_params(message.text)
        if (params not in settings.BLOCKED_WORD_LIST) and params:
            add_blocked_template(params)
            bot.send_message(message.chat.id, 'Строка-шаблон:\n"' + params + '"\nдобавлена в банлист.')
        else:
            bot.send_message(message.chat.id, 'Данная строка-шаблон уже есть в банлисте.')


@bot.message_handler(commands=['remove'])
def remove_word(message):
    if is_admin(message):
        params = get_command_params(message.text)
        if params in settings.BLOCKED_WORD_LIST:
            remove_blocked_template(params)
            bot.send_message(message.chat.id, 'Cтрока-шаблон:\n"' + params + '"\nудалена из банлиста.')
        else:
            bot.send_message(message.chat.id, 'Данная строка-шаблон отсутствует в банлисте.')


@bot.message_handler(commands=['showbanlist'])
def show_list(message):
    banlist_words = '\n'.join(settings.BLOCKED_WORD_LIST)
    bot.send_message(message.chat.id, 'Cтроки-шаблоны в банлисте:\n' + banlist_words)


@bot.message_handler(commands=['bugreport'])
def show_bugreport(message):
    if is_admin(message):
        params = get_command_params(message.text)
        bot.send_message(keys.DEVELOPERS_CHAT_ID, 'Хьюстон, нам пришла жалоба:\n"' + params + '"')


@bot.message_handler(func=lambda message: True)
def check_messages(message):
    if is_message_dangerous(message.text):
        reply_and_kick(message)
    if message.entities is not None:
        for entity in message.entities:
            if is_message_dangerous(entity.url):
                reply_and_kick(message)
                break


bot.polling(none_stop=False, interval=0, timeout=20)

