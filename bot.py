import discord
from discord.ext import commands
import os
from openai import OpenAI
from dotenv import load_dotenv
from flask import Flask
from threading import Thread

# KEEP ALIVE SERVER
app = Flask('')

@app.route('/')
def home():
    return "Bot attivo!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

keep_alive()

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
GROQ_KEY = os.getenv("GROQ_API_KEY")

client_ai = OpenAI(
    api_key=GROQ_KEY,
    base_url="https://api.groq.com/openai/v1"
)

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Bot online come {bot.user}")

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    is_mention = bot.user in message.mentions
    is_reply_to_bot = message.reference and message.reference.resolved and message.reference.resolved.author == bot.user

    if is_mention and not is_reply_to_bot:
        async with message.channel.typing():

            messages = []
            async for msg in message.channel.history(limit=50):
                if msg.content and msg.id != message.id:
                    messages.append(f"{msg.author.name}: {msg.content}")

            messages.reverse()
            chat_text = "\n".join(messages)

            # Prompt AI 
            completion = client_ai.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": "Riassumi questa conversazione Discord in modo breve e chiaro."},
                    {"role": "user", "content": chat_text}
                ]
            )

            summary = completion.choices[0].message.content

        await message.reply(
            f"**Riassunto della conversazione (solo degli ultimi 50 messaggi):**\n{summary}",
            mention_author=False
        )

    await bot.process_commands(message)

bot.run(TOKEN)