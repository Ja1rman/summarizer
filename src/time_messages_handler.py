import asyncio
import json
import re
import sys
from urllib.parse import urlparse

from time_messenger import AsyncDriver

from src.config import TIME_DRIVER_CONFIG
from src.time_client import create_answer
from src.general import create_summary_for_thread_and_post
from src.stats_pusher import stats_pusher
from src.logger import stdout_log, LogLevel


async def init_background_websocket():
    async def websocket_wrapper():
        try:
            time_driver = AsyncDriver(options=TIME_DRIVER_CONFIG)
            async with time_driver:
                await time_driver.login()
                await time_driver.init_websocket(event_handler)
        except Exception as e:
            stdout_log(f"Websocket crashed: {e}", LogLevel.FATAL)
            sys.exit(1)

    asyncio.create_task(websocket_wrapper())


async def event_handler(event_message):
    try:
        event_data = json.loads(event_message)
        if event_data.get("event") != "posted":
            return
        post = json.loads(event_data.get("data", {}).get("post", ""))
    except:
        return
    message = post.get("message", "")
    channel_id = post.get("channel_id", "")
    root_id = post.get("root_id", "")
    post_id = post.get("id", root_id)
    thread_root_id = root_id or post_id
    if not re.search(r'@summarize\b', message):
        return
    await stats_pusher('bot_summarize', post.get('user_id', 'unknown'))
    message = message[message.find('@summarize'):]
    splited = message.split()
    if len(splited) > 1 and '/' in splited[1]:
        thread_id = splited.pop(1).split('/')[-1]
    else:
        thread_id = ''
    prompt = ' '.join(splited[1:]) if len(splited) > 1 else ''
    if not thread_id:
        thread_id = thread_root_id
    if len(thread_id) < 10:
        message = (
            "Невозможно определить thread_id. Тегните меня в треде. Либо после тега "
            "укажите ссылку на тред."
        )
        await create_answer(message, channel_id, thread_root_id, post_id)
        return
    await create_summary_for_thread_and_post(
        thread_id, channel_id, thread_root_id, post_id, prompt
    )


def extract_id(url: str) -> str:
    path_parts = urlparse(url).path.strip('/').split('/')
    return path_parts[-1] if path_parts else ''
