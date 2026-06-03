import aiohttp

from src.config import TIME_BOT_TOKEN


async def get_messages_from_thread(post_id: str) -> str:
    ids, posts = await get_thread(post_id)
    return merge_messages(ids, posts)


async def get_thread(post_id: str) -> tuple[list[str], dict]:
    ids = []
    posts = {}
    headers = {
        'Accept': 'application/json',
        'Authorization': f'Bearer {TIME_BOT_TOKEN}'
    }
    async with aiohttp.ClientSession(headers=headers) as session:
        while True:
            url = f'https://api-time.tinkoff.ru/api/v4/posts/{post_id}/thread'
            async with session.get(url) as response:
                response.raise_for_status()
                data = await response.json()
                ids.extend(data['order'])
                posts.update(data['posts'])

                if data.get('has_next'):
                    post_id = data.get('next_post_id')
                else:
                    break
    return ids, posts


def merge_messages(ids, posts):
    result = []
    for post_id in ids:
        post = posts.get(post_id)
        if post:
            result.append(get_text_from_post(post))
    return '\n\n'.join(result)


def get_text_from_post(post: dict) -> str:
    message = post.get("message", "").strip()
    attachments = post.get("props", {}).get("attachments", [])
    if not attachments:
        attachments = []
    for attachment in attachments:
        message += f"\n{attachment.get("title", "")} {attachment.get("text", "")}"
        fields = attachment.get("fields", [])
        if not fields:
            fields = []
        for field in fields:
            message += f"\n{field.get("title", "")} {field.get("value", "")}"
    return message
