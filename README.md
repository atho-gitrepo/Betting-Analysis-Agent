# Betting Analytics Service

Independent analytics system for betting bot data.

## Features
- Read-only Firebase access
- Notion database sync
- Local LLM insights (T5-small)
- Daily Telegram reports

## Setup
1. Copy `.env.example` to `.env` and fill credentials
2. Run `pip install -r requirements.txt`
3. Run `python analytics_service.py`

## Deployment
Deploy on Railway with: `railway up`

## Environment Variables
- `TELEGRAM_TOKEN` & `TELEGRAM_CHAT_ID`
- `FIREBASE_CREDENTIALS_JSON`
- `NOTION_TOKEN` & `NOTION_DATABASE_ID`
