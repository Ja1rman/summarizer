from src.time_client import create_answer
from src.time_requests import get_messages_from_thread
from src.gpt import summarize_dialog, create_answer_with_gpt
from src.logger import stdout_log, LogLevel


async def create_summary_for_thread_and_post(thread_id, channel_id, root_id, post_id, prompt):
    stdout_log(
        f"Вызвана функция create_summary_for_thread_and_post: {thread_id}, {channel_id},"
        f" {root_id}, {post_id}, {prompt}", LogLevel.INFO
    )
    message = await create_summary_for_thread(thread_id, prompt)
    try:
        await create_answer(message, channel_id, root_id, post_id)
    except Exception as e:
        stdout_log(f"Ошибка создания сообщения: {e}", LogLevel.ERROR)


async def create_summary_for_thread(thread_id: str, prompt: str) -> str:
    try:
        messages = await get_messages_from_thread(thread_id)
    except Exception as e:
        stdout_log(f"Ошибка получения сообщений из треда: {e}", LogLevel.ERROR)
        if "403" in str(e):
            return "*Ошибка* доступа к треду. Добавьте меня в канал."
        else:
            return "*Ошибка* получения сообщений. Проверьте корректность ссылки. Или бота нет в закрытом канале."
    try:
        res = await summarize_dialog(messages, prompt)
    except Exception as e:
        stdout_log(f"Ошибка обращения к GPT: {e}", LogLevel.ERROR)
        return "*Ошибка* обращения к GPT. Попробуйте позже."
    return res


async def create_answer_to_questiong_by_thread(thread_id: str, question: str) -> str:
    try:
        messages = await get_messages_from_thread(thread_id)
    except Exception as e:
        stdout_log(f"Ошибка получения сообщений из треда: {e}", LogLevel.ERROR)
        if "403" in str(e):
            return "*Ошибка* доступа к треду. Добавьте меня в канал."
        else:
            return "*Ошибка* получения сообщений. Проверьте корректность ссылки. Или бота нет в закрытом канале."
    try:
        res = await create_answer_with_gpt(question, messages)
    except Exception as e:
        stdout_log(f"Ошибка обращения к GPT: {e}", LogLevel.ERROR)
        return "*Ошибка* обращения к GPT. Попробуйте позже."
    if "*Ошибка*" in res or "*Ошибка.*" in res:
        return "*Ошибка*. Нет информации для ответа на вопрос."
    return res
