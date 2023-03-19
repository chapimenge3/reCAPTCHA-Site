import os
import logging
from uuid import uuid4 as uuid
from datetime import datetime

from deta import Deta
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import httpx
from dotenv import load_dotenv

from models import TelegramWebhook, VerifyCapthca

load_dotenv()

# BOT CONFIG
BOT_TOKEN = os.getenv("BOT_TOKEN")
BOT_WEBHOOK_SECRET = os.getenv("BOT_WEBHOOK_SECRET")
TG_API = "https://api.telegram.org/bot{}".format(BOT_TOKEN)
CAPTCHA_URL = os.getenv('CAPTCHA_URL')

BOT_INFO = httpx.get(f'{TG_API}/getMe').json().get('result')

logger = logging.getLogger(__name__)

# fast api
app = FastAPI()
origins = [
    # "http://chapimenge.me",
    "*"
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# DETA CONFIG
DETA_PROJECT_KEY = os.getenv('DETA_PROJECT_KEY')
db = Deta(DETA_PROJECT_KEY).Base('captcha')


# GOOGLE RECAPTCHA CONFIG
RECAPTCHA_SECRET = os.getenv('RECAPTCHA_SECRET')
RECAPTCHA_URL = 'https://www.google.com/recaptcha/api/siteverify'

BOT_INSTRUCTIONS = '''
Hello, I am a bot that helps you to verify that you are a human.

To use me, you need to add me to a group and make me an admin.

After that, I will make sure that members are a human before they can send messages in the group.

Follow me on twitter <a href="https://twitter.com/chapimenge3">@chapimenge3</a>
Follow me on github <a href="https://github.com/chapimenge3">@chapimenge3</a>
Follow me on instagram <a href="https://instagram.com/chapimenge3">@chapimenge3</a>
Follow me on LinkedIn <a href="https://linkedin.com/in/chapimenge">@chapimenge</a>

Read my blog https://blog.chapimenge.com/
My website https://chapimenge.com/
Join My Telegram Channel https://t.me/codewizme
'''

client = httpx.Client(base_url=TG_API)


def webhook_url():
    endpoint = ""
    for i in BOT_TOKEN:
        if i.isalpha():
            endpoint += i

    return endpoint


def generate_code():
    return str(uuid())


def save_code(data):
    # 5 min expiry
    expired_at = datetime.now().timestamp() + 300
    data['expired_at'] = expired_at
    id = db.put(data)
    return id['key']

def delete_code(code):
    db.delete(code)

def check_code(code):
    data = db.get(code)
    return data


def verify_captcha(response):
    params = {
        'secret': RECAPTCHA_SECRET,
        'response': response
    }
    response = httpx.post(RECAPTCHA_URL, params=params)

    if response.status_code == 200:
        data = response.json()
        return data.get('success')
    return False


def call_tg(method, params=None):
    try:
        response = client.post(f'/{method}', json=params)
        print('response', response.json())
        return response
    except Exception as e:
        logger.error(e)
        print('error', e)
    return None


def isAdmin(chat_id, user_id=None):
    user_id = user_id or BOT_INFO.get('id')
    params = {
        'chat_id': chat_id
    }
    bot_admins = call_tg('getChatAdministrators', params)
    if bot_admins:
        bot_admins = bot_admins.json()['result']
        return any(
            map(lambda i: i['user']['id'] == user_id, bot_admins))

    return False


def send_verification_link(chat_id, user_full_name, code):
    inline_keyboard = [[
        {
            'text': 'Verify',
            'web_app': {
                'url': f'{CAPTCHA_URL}?code={code}'
            }
        },
    ]]
    markup = {
        'inline_keyboard': inline_keyboard
    }
    params = {
        'chat_id': chat_id,
        'text': f'<a href="tg://user?id={chat_id}">{user_full_name}</a>'
        'Please verify you are human\n'
        'Join <a href="https://t.me/codewizme">My Telegram Channel</a>',
        'reply_markup': markup,
        'parse_mode': 'HTML',
        'disable_web_page_preview': True
    }
    return call_tg('sendMessage', params)


# startup method
@app.on_event("startup")
def setWehook():
    DEBUG = os.getenv('DEBUG', '')
    if DEBUG.lower() != 'true':
        return

    WEBHOOK_URL = os.getenv('WEBHOOK_URL', None)
    if WEBHOOK_URL:
        url = f'{WEBHOOK_URL}/webhook/{webhook_url()}'
        call_tg('deleteWebhook')
        params = {
            'url': url
        }
        call_tg('setWebhook', params)
        print('Webhook is set!')


@app.get("/")
def index():
    return {
        "data": "sucess",
        'endpoint': 'index'
    }


@app.post("/verify-captha")
def verify_captha(data: VerifyCapthca):
    # check request method
    code = data.code
    code_data = check_code(code)
    if not code_data:
        return {
            'status': 'error',
            'message': 'Invalid code, please try leaving and rejoining the group'
        }
    verify_captcha(data.response)
    delete_code(code)
    return {
        'status': 'ok',
        'message': 'success'
    }


@app.post(f'/webhook/{webhook_url()}')
def tg_webhook(request: TelegramWebhook):
    message = request.message
    my_chat_member = request.my_chat_member

    if message and message.get('text') and str(message.get('text')).startswith('/start'):
        cmd = message.get('text').split(' ')
        if len(cmd) == 1:
            params = {
                'chat_id': message.get('from').get('id'),
                'text': BOT_INSTRUCTIONS,
                'reply_markup': {
                    'inline_keyboard': [[
                        # buy me a coffee
                        {
                            'text': 'Buy me a coffee',
                            'url': 'https://www.buymeacoffee.com/chapimenge'
                        },
                    ]]
                }
            }
            call_tg('sendMessage', params)
            return {
                'status': 'success',
                'message': 'Bot instructions sent'
            }
        else:
            code = cmd[1]
            if not check_code(code):
                params = {
                    'chat_id': message.get('from').get('id'),
                    'text': 'Invalid code'
                }
                call_tg('sendMessage', params)
                return {
                    'status': 'success',
                    'message': 'Invalid code'
                }
            user_id = message.get('from').get('id')
            user_full_name = message.get('from').get(
                'first_name') + ' ' + message.get('from').get('last_name', '')
            send_verification_link(user_id, user_full_name, code)
            return {
                'status': 'success',
                'message': 'Code sent'
            }

    elif message and message.get('new_chat_member', None):
        chat = message.get('chat')
        if chat.get('type') == 'channel':
            # if the bot added to the channel leave it
            params = {'chat_id': chat.get('id')}
            try:
                call_tg('leaveChat', params)
            except print(0):
                pass
            return {'status': 'error', 'message': 'bot can\'t added to the channel'}

        new_chat_member = message.get('new_chat_member')

        if chat.get('type') in ['group', 'supergroup']:
            if new_chat_member and new_chat_member.get('id') == BOT_INFO['id']:
                # Bot is added to a group
                params = {
                    'chat_id': chat.get('id')
                }
                is_bot_admin = isAdmin(chat.get('id'))
                if not is_bot_admin:
                    # send message to the chat
                    text = "To make bot active, please make it group administrator!"
                    params.update({
                        'text': text
                    })
                    call_tg('sendMessage', params)

                return {'status': 'ok', 'message': 'bot added to the group'}

            elif new_chat_member and new_chat_member.get('status') == 'administrator':
                if new_chat_member.get('user', None) and new_chat_member.get('user')['id'] == BOT_INFO['id']:
                    # Bot is added to a group
                    params = {
                        'chat_id': chat.get('id')
                    }
                    is_bot_admin = isAdmin(chat.get('id'))
                    if is_bot_admin:
                        # send message to the chat
                        text = "Bot is active!"
                        params.update({
                            'text': text
                        })
                        call_tg('sendMessage', params)
                    return {'status': 'ok', 'message': 'bot added to the group as an admin'}
            else:
                new_chat_member = message.get('new_chat_member', None)
                if not new_chat_member:
                    return {
                        'status': 'error',
                        'message': 'new_chat_member not found'
                    }
                # user added to a group
                params = {
                    'chat_id': chat.get('id')
                }
                is_bot_admin = isAdmin(chat.get('id'))
                if not is_bot_admin:
                    return {'status': 'error', 'message': 'bot is not admin'}
                else:
                    if message.get('from', None):
                        _from = message.get('from')
                        params = {
                            'chat_id': chat.get('id'),
                        }
                        is_from_admin = isAdmin(
                            chat.get('id'), _from.get('id'))
                        if is_from_admin:
                            return {
                                'status': 'ok',
                                'message': 'user added to the group by admin'
                            }

                    chat_id = chat.get('id')
                    data = {
                        'chat_id': chat_id,
                        'user_id': new_chat_member.get('id'),
                    }
                    code = save_code(data)
                    user_full_name = f'{new_chat_member.get("first_name", "")} {new_chat_member.get("last_name", "")}'
                    inline_keyboard = [[
                        {
                            'text': 'Verify',
                            'url': f'https://t.me/{BOT_INFO["username"]}?start={code}'
                        },
                    ], ]

                    markup = {
                        'inline_keyboard': inline_keyboard
                    }

                    params = {
                        'chat_id': chat_id,
                        'text': f'Welcome <a href="tg://user?id={chat_id}">{user_full_name}</a>.'
                        'Please verify you are human',
                        'reply_markup': markup,
                        'parse_mode': 'HTML'
                    }

                    call_tg('sendMessage', params)

                return {'status': 'ok', 'message': 'user added to the group and sent verification message'}

    elif my_chat_member and my_chat_member.get('new_chat_member'):
        new_chat_member = my_chat_member.get('new_chat_member')
        if new_chat_member.get('status') == 'administrator':
            # Bot is added to a group
            params = {
                'chat_id': my_chat_member.get('chat').get('id')
            }
            is_bot_admin = isAdmin(my_chat_member.get('chat').get('id'))
            if is_bot_admin:
                # send message to the chat
                text = "Bot is now active!"
                params.update({
                    'text': text
                })
                call_tg('sendMessage', params)
            return {'status': 'ok', 'message': 'bot added to the group as an admin'}

    return {"Hello": "World"}
