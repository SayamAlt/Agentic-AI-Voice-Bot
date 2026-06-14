# Agentic AI Voice Bot

This is a voice bot that you can talk to in real time. It helps you manage your notes, calendar meetings, and email messages using your voice.

## Features

- **Notes:** You can create, read, edit, and delete notes. The bot saves these notes inside a local database file on your computer.
- **Google Calendar:** You can schedule, edit, view, and delete meetings on your Google Calendar.
- **Gmail:** You can read your recent emails and make email drafts.
- **Voice Interruption:** If you speak while the bot is speaking, the bot stops talking immediately and listens to your new words.

## Things You Need

You must install the python packages to run the bot. You can install them by running this command in your terminal:

```bash
pip install -r requirements.txt
```

You also need two files in this folder to connect to the services:
1. **.env:** A file containing your LiveKit and OpenAI API keys.
2. **credentials.json:** Your Google keys from the Google Cloud Console.

## Setting Up Your Keys

### 1. Create a .env File
Create a new file named `.env` in this folder. Add these lines and replace the text with your own keys:

```env
LIVEKIT_URL=your_livekit_server_url
LIVEKIT_API_KEY=your_livekit_api_key
LIVEKIT_API_SECRET=your_livekit_api_secret
OPENAI_API_KEY=your_openai_api_key
```

### 2. Get Google Keys
- Go to the Google Cloud Console website.
- Create a new project.
- Enable the Google Calendar API and the Gmail API for your project.
- Create an OAuth Client ID for a desktop application.
- Download the JSON file, name it `credentials.json`, and put it in this folder.

## How to Run the Bot

1. Start the bot by running this command in your terminal:
   ```bash
   python main.py dev
   ```
2. Open the LiveKit Console website in your web browser.
3. Connect using the keys from your `.env` file.
4. Speak to the bot.
