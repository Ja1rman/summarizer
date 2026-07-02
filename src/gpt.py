from typing import Any

import httpx
from langchain_core.messages import BaseMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from src.config import GPT_TOKEN


LLM_BASE_URL = "https://llm-proxy.t-tech.team"
REQUEST_TIMEOUT_SECONDS = 350
SUMMARY_MODEL = "tgpt/gemma-3-27b-it"
ANSWER_MODEL = "tgpt/t-pro-it-2-0-fp8"
SUMMARY_MODEL_KWARGS = {
    "presence_penalty": -1,
    "top_p": 0.2,
}
ANSWER_MODEL_KWARGS = {
    "presence_penalty": 0,
    "temperature": 0,
    "top_p": 0.2,
}

SUMMARY_SYSTEM_PROMPT = (
    "На основе предоставленных сообщений из треда составь краткий пересказ обсуждения на русском языке.\n"
    "Требования:\n"
    "- Выдели ключевые вопросы пользователя и финальные ответы/решения со стороны поддержки.\n"
    "- Исключи неинформативные реплики (например, приветствия, благодарности).\n"
    "- Сохрани хронологическую последовательность основных смысловых шагов.\n"
    "- Будь кратким, но точным: цель - быстро понять суть обсуждения без чтения всего треда.\n"
    "- Если в треде есть итоговое решение проблемы - укажи его отдельно в конце."
)

SUMMARY_PROMPT = ChatPromptTemplate.from_messages(
    [
        ("system", SUMMARY_SYSTEM_PROMPT),
        (
            "human",
            "Дополнительные пожелания пользователя к резюме:\n{user_prompt}\n\n"
            "Сообщения треда:\n{thread_text}",
        ),
    ]
)

ANSWER_SYSTEM_PROMPT = (
    "ОБЩИЕ ПРИНЦИПЫ:\n"
    "- Ты бот, который на основе предыдущего схожего треда отвечает на новый вопрос. "
    "В старом обсуждении может не быть ответа на новый вопрос, даже если тема или симптомы похожи.\n"
    "- Нельзя аппрувить никакие действия пользователя, выражать мнение, делать выводы о приоритетах задач. "
    "Можно только давать конкретные ответы на вопросы.\n"
    "- Не придумывай данные, события, источники, не связывай старые события как причину нового сбоя.\n"
    "- Не переноси причину, решение или статус из предыдущего треда на новый вопрос без явной фактической связи.\n"
    "- Если связь предыдущего обсуждения с новым вопросом слабая или формальная, считай, что информации недостаточно.\n"
    "ИНСТРУКЦИЯ:\n"
    "1. Сначала внутренне оцени релевантность previous_thread к new_question, но не выводи эту оценку.\n"
    "2. Если в треде есть полный или частичный ответ на вопрос пользователя, используй эту информацию и ответь на вопрос.\n"
    "3. Если в треде нет нужной информации, но можно дать безопасную общую диагностику или следующий шаг "
    "без выдумывания фактов и без привязки к старому инциденту, ответь.\n"
    "4. Если для ответа нужно предположить неизвестные факты, причину, статус работ, владельца или внешний контекст, "
    "пришли ровно строку '*Ошибка*.'\n"
    "5. Нельзя писать, что вопрос снят, обращение обработано, неактуально, нельзя ничего аппрувить. "
    "Если в предыдущем обсуждении пользователь сам закрыл вопрос, пришли только решение, которое к этому привело.\n"
    "6. Не цитируй и не пересказывай текст вопроса и треда, не вставляй их части в ответ.\n"
    "7. Ответ должен содержать только суть решения/диагностики или конкретный следующий шаг, "
    "без вводных фраз и рассуждений о том, как ты думал.\n"
    "8. Ответ не должен превышать 1000 символов и 5 предложений.\n"
    "9. Если ты не можешь дать конкретный ответ или план действий, пришли ровно строку '*Ошибка*.'\n"
    "ВНУТРЕННЯЯ ПРОВЕРКА ПЕРЕД ОТВЕТОМ:\n"
    "- относится ли previous_thread к new_question по фактам, а не только по общим словам;\n"
    "- есть ли в previous_thread решение, диагностика или проверка, применимая к new_question;\n"
    "- не является ли ответ догадкой;\n"
    "- не звучит ли ответ как подтверждение действий пользователя.\n"
)

ANSWER_PROMPT = ChatPromptTemplate.from_messages(
    [
        ("system", ANSWER_SYSTEM_PROMPT),
        (
            "human",
            "<previous_thread>\n{thread_text}\n</previous_thread>\n\n"
            "<new_question>\n{question}\n</new_question>\n\n"
            "Ответь строго по инструкции из системного сообщения.",
        ),
    ]
)


async def summarize_dialog(text: str, promt: str = "") -> str:
    messages = SUMMARY_PROMPT.format_messages(
        user_prompt=promt or "Не указаны.",
        thread_text=text,
    )
    return await gpt_request(
        model=SUMMARY_MODEL,
        messages=messages,
        max_tokens=1500,
        model_kwargs=SUMMARY_MODEL_KWARGS,
    )


async def create_answer_with_gpt(question: str, text: str) -> str:
    messages = ANSWER_PROMPT.format_messages(
        thread_text=text,
        question=question,
    )
    return await gpt_request(
        model=ANSWER_MODEL,
        messages=messages,
        max_tokens=600,
        model_kwargs=ANSWER_MODEL_KWARGS,
        extra_body={
            "chat_template_kwargs": {
                "enable_thinking": False,
            },
        },
    )


async def gpt_request(
    *,
    model: str,
    messages: list[BaseMessage],
    max_tokens: int,
    model_kwargs: dict[str, Any],
    extra_body: dict[str, Any] | None = None,
) -> str:
    async with httpx.AsyncClient(
        verify=False,
        timeout=REQUEST_TIMEOUT_SECONDS,
    ) as http_async_client:
        llm = ChatOpenAI(
            model=model,
            api_key=GPT_TOKEN,
            base_url=LLM_BASE_URL,
            max_tokens=max_tokens,
            timeout=REQUEST_TIMEOUT_SECONDS,
            max_retries=0,
            http_async_client=http_async_client,
            extra_body=extra_body,
            **model_kwargs,
        )
        result = await llm.ainvoke(messages)
        return _message_content_to_text(result.content).replace('@', '')


def _message_content_to_text(content: str | list[Any]) -> str:
    if isinstance(content, str):
        return content

    text_parts = []
    for part in content:
        if isinstance(part, str):
            text_parts.append(part)
        elif isinstance(part, dict) and isinstance(part.get("text"), str):
            text_parts.append(part["text"])
        else:
            text_parts.append(str(part))
    return "\n".join(text_parts)
