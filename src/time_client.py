from time_messenger import AsyncDriver

from src.config import TIME_DRIVER_CONFIG
from src.logger import stdout_log, LogLevel


async def create_answer(message: str, channel_id: str, root_id: str, post_id: str):
    stdout_log(
        f"Вызвана функция create_answer: {message}, {channel_id},"
        f" {root_id}, {post_id}", LogLevel.INFO
    )
    time_driver = AsyncDriver(options=TIME_DRIVER_CONFIG)
    async with time_driver:
        await time_driver.login()
        await time_driver.posts.create_post(
            options={
                "channel_id": channel_id,
                "message": message,
                "root_id": root_id,
                "props": {
                    "quote_post_id": post_id,
                },
            }
        )
