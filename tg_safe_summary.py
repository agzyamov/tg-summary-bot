import os
import asyncio
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
from telethon import TelegramClient
from telethon.errors import FloodWaitError
from openai import OpenAI

# Load environment variables
load_dotenv()


print("LOADED KEY:", os.getenv("OPENROUTER_API_KEY"))

# Telegram API credentials
api_id = int(os.getenv("TELEGRAM_API_ID"))
api_hash = os.getenv("TELEGRAM_API_HASH")
channels = os.getenv("CHANNELS", "").split(",")

# OpenRouter API key
openrouter_api_key = os.getenv("OPENROUTER_API_KEY")

# Correct OpenAI client for OpenRouter
openai_client = OpenAI(
    api_key=openrouter_api_key,
    base_url="https://openrouter.ai/api/v1",
    default_headers={
        "Authorization": f"Bearer {openrouter_api_key}"
    }
)

# Telegram session
client = TelegramClient("safe_session", api_id, api_hash)

# GPT-based summarization
async def summarize(channel_name, text):
    prompt = f"Summarize key insights from the last 24 hours in the Telegram channel {channel_name}:\n\n{text}"
    try:
        response = openai_client.chat.completions.create(
            model="openai/gpt-3.5-turbo",  # You can switch to "deepseek-ai/deepseek-moe"
            messages=[{"role": "user", "content": prompt}],
            max_tokens=600,
            temperature=0.4
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Error generating summary: {e}"

# Safe message fetching from Telegram
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

# Main loop
async def main():
    await client.start()
    print("✅ Telegram authorization successful.")

    summaries = []
    max_channels = min(5, len(channels))

    for ch in channels[:max_channels]:
        ch = ch.strip()
        if not ch:
            continue

        print(f"\n📥 Processing: {ch}")
        try:
            entity = await client.get_entity(ch)
            text = await fetch_messages_safe(entity)

            if not text.strip():
                summaries.append(f"## {ch}\n\nNo recent messages in the last 24 hours.\n\n")
                continue

            summary = await summarize(ch, text)
            summaries.append(f"## {ch}\n\n{summary}\n\n")

            await asyncio.sleep(3)  # Avoid rate limits
        except Exception as e:
            summaries.append(f"## {ch}\n\nError: {e}\n\n")

    with open("summary_safe.md", "w", encoding="utf-8") as f:
        f.writelines(summaries)

    print("\n✅ Done! Summary saved to summary_safe.md")

# Run the script
asyncio.run(main())