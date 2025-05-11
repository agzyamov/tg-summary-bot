# Telegram Summary Bot 🤖

A Python script that connects to your Telegram account, fetches messages from selected channels or groups, and generates a daily summary using OpenAI's GPT-4o.

## ✨ Features

- Authenticates securely via Telethon session
- Fetches recent messages from channels you belong to
- Handles Telegram rate limits with retry logic
- Summarizes content using OpenAI GPT-4o
- Outputs structured Markdown summary (`summary_safe.md`)

## 🛠 Requirements

- Python 3.8+
- A Telegram API key and hash (from https://my.telegram.org)
- An OpenAI API key (from https://platform.openai.com)

## 🚀 Setup

```bash
git clone https://github.com/your-username/tg-summary-bot.git
cd tg-summary-bot

python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

pip install -r requirements.txt