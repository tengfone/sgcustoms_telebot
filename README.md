# Singapore Customs Checkpoint Telegram Bot

A Telegram bot that provides real-time traffic images from Singapore's customs checkpoints using LTA's DataMall API.

## Features

- View traffic images from Singapore's customs checkpoints
- Choose specific checkpoints via inline keyboard
- Get the latest images with simple commands
- User-friendly interface with inline buttons and helpful messages

## Setup

1. Clone this repository
2. Install dependencies:

   ```
   pip install -r requirements.txt
   ```

3. Create a `.env` file in the root directory with the following variables:

   ```
   TELEGRAM_TOKEN=your_telegram_bot_token
   LTA_API_KEY=your_lta_datamall_api_key
   ```

4. Run the bot:

   ```
   python bot.py
   ```

## How to Get API Keys

1. **Telegram Bot Token**: Message [@BotFather](https://t.me/BotFather) on Telegram and follow the instructions to create a new bot
2. **LTA DataMall API Key**: Register for an account at [LTA DataMall](https://datamall.lta.gov.sg/content/datamall/en/request-for-api.html) and request an API key

## Usage

1. Start the bot with `/start` command
2. Use `/checkpoints` to see a list of available customs checkpoints
3. Click on any checkpoint to get its latest traffic image
4. Use `/help` to see all available commands

## Available Commands

- `/start` - Start the bot and get a welcome message
- `/help` - Show help information
- `/checkpoints` - Show a list of available checkpoints
- `/about` - Show information about the bot
