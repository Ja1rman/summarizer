import os


TIME_BOT_TOKEN = os.environ.get('TIME_BOT_TOKEN')
GPT_TOKEN = os.environ.get('GPT_TOKEN')

TIME_DRIVER_CONFIG = {
    "url": "api-time.tinkoff.ru",
    "scheme": "https",
    "port": 443,
    "token": TIME_BOT_TOKEN,
}

SAGE_ENV = os.getenv("SAGE_ENV", default="test")
SAGE_SYSTEM = os.getenv("SAGE_SYSTEM", default="summarizer")
SAGE_SERVER = os.getenv("SAGE_SERVER", default="m1")
SAGE_GROUP = os.getenv("SAGE_GROUP", default="bot_workflow")
POD_NAME = os.getenv("POD_NAME", default="unknown")
