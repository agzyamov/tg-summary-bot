import os
import asyncio
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
from telethon import TelegramClient
from telethon.errors import FloodWaitError
from openai import OpenAI

# Load environment variables
load_dotenv()

# Telegram credentials
api_id = int(os.getenv("TELEGRAM_API_ID"))
api_hash = os.getenv("TELEGRAM_API_HASH")
channels = os.getenv("CHANNELS", "").split(",")
chat_id = os.getenv("CHAT_ID")

# OpenRouter credentials
openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
openai_client = OpenAI(
    api_key=openrouter_api_key,
    base_url="https://openrouter.ai/api/v1",
    default_headers={"Authorization": f"Bearer {openrouter_api_key}"}
)

client = TelegramClient("safe_session", api_id, api_hash)

async def summarize(title, text):
    # prompt = f"Summarize key insights from the last 24 hours in the Telegram chat or channel in Russian language'{title}':\n\n{text}"
    prompt = f"""
    Проанализируй сообщения из Telegram-чата за последние 24 часа и сделай краткое саммари на русском языке.

    Твоя задача — помочь занятому человеку быстро понять, стоит ли возвращаться к обсуждению. Изложи в сжатой форме, какие были:
    - ключевые темы и обсуждения,
    - интересные идеи, инсайты, споры,
    - важные вопросы или новости.

    Каждую тему оцени по **весу** (насколько она была активной, важной, обсуждаемой) — по шкале от 1 до 5, где:
    - 1 — упомянули вскользь,
    - 3 — средняя активность или интерес,
    - 5 — очень бурное обсуждение или критически важная информация.

    Если обсуждения были поверхностные или пустые — скажи об этом. Не пересказывай все сообщения, выдели только суть. Структурируй ответ **по пунктам с весами** для удобства восприятия.

    Вот сообщения:\n\n{text}
    """

    try:
        response = openai_client.chat.completions.create(
            model="openai/gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=600,
            temperature=0.4
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Error generating summary: {e}"

async def fetch_messages_safe(entity):
    try:
        yesterday = datetime.now(timezone.utc) - timedelta(days=1)
        messages = await client.get_messages(entity, limit=200, offset_date=datetime.now(timezone.utc))
        return "\n".join([msg.message for msg in messages if msg.message and msg.date > yesterday])
    except FloodWaitError as e:
        print(f"⚠️ Flood wait — sleeping {e.seconds} seconds...")
        await asyncio.sleep(e.seconds)
        return await fetch_messages_safe(entity)
    except Exception as e:
        print(f"Error fetching messages: {e}")
        return ""

async def main():
    await client.start()
    print("✅ Telegram authorization successful.")

    summaries = []

    # Каналы
    for ch in channels[:min(5, len(channels))]:
        ch = ch.strip()
        if not ch:
            continue

        print(f"\n📥 Processing channel: {ch}")
        try:
            entity = await client.get_entity(ch)
            text = await fetch_messages_safe(entity)

            if not text.strip():
                summaries.append(f"## {ch}\n\nNo recent messages in the last 24 hours.\n\n")
            else:
                summary = await summarize(ch, text)
                summaries.append(f"## {ch}\n\n{summary}\n\n")

            await asyncio.sleep(3)
        except Exception as e:
            summaries.append(f"## {ch}\n\nError: {e}\n\n")

    # Чат по ID
    if chat_id:
        print(f"\n💬 Processing chat ID: {chat_id}")
        try:
            entity = await client.get_entity(int(chat_id))
            text = await fetch_messages_safe(entity)

            if not text.strip():
                summaries.append(f"## Chat {chat_id}\n\nNo recent messages in the last 24 hours.\n\n")
            else:
                summary = await summarize(f"Chat {chat_id}", text)
                summaries.append(f"## Chat {chat_id}\n\n{summary}\n\n")

            await asyncio.sleep(3)
        except Exception as e:
            summaries.append(f"## Chat {chat_id}\n\nError: {e}\n\n")

    # Сохраняем результат
    with open("summary_safe.md", "w", encoding="utf-8") as f:
        f.writelines(summaries)

    print("\n✅ Done! Summary saved to summary_safe.md")

# Run
asyncio.run(main())