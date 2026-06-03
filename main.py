import uvicorn
from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route, Mount

from src.time_messages_handler import init_background_websocket
from src.general import create_summary_for_thread, create_answer_to_questiong_by_thread
from src.stats_pusher import metrics_app, stats_pusher
from src.logger import stdout_log, LogLevel


async def health_check(request):
    return JSONResponse({'status': 200})


async def summarize_thread(request):
    data = await request.form()
    splited = data.get('text', '').split()
    root_id = data.get('root_id', '')
    await stats_pusher('api_summarize', data.get('user_id', 'unknown'))
    if len(splited) > 0 and '/' in splited[0]:
        thread_id = splited.pop(0).split('/')[-1]
    else:
        thread_id = root_id
    prompt = ' '.join(splited) if len(splited) > 0 else ''
    stdout_log(
        f"Получены данные для summarize_thread: {thread_id}, {prompt}", LogLevel.INFO
    )
    if len(thread_id) < 10:
        return JSONResponse(
            {
                'text': (
                    'Невозможно определить thread_id. Вызовите внутри треда ИЛИ После slash команды укажите '
                    'ссылку на тред.\nИли воспользуйтесь ```@summarize```.'
                ),
                'username': 'summarize',
            }
        )
    return JSONResponse(
        {
            'text': await create_summary_for_thread(thread_id, prompt),
            'username': 'summarize',
        }
    )


async def answer_to_question(request):
    data = await request.form()
    await stats_pusher('answer_to_question', data.get('user_id', 'unknown'))
    thread_id = data.get('thread_id', '')
    question = data.get('question', '')
    return JSONResponse({'text': await create_answer_to_questiong_by_thread(thread_id, question)})


app = Starlette(
    routes=[
        Route('/healthz', health_check),
        Route('/summarize', summarize_thread, methods=["POST"]),
        Route('/answer', answer_to_question, methods=["POST"]),
        Mount('/metrics', app=metrics_app),
    ],
    on_startup=[init_background_websocket],
)

if __name__ == '__main__':
    uvicorn.run(app)
