import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
GROQ_KEY = os.getenv("GROQ_API_KEY")

client = OpenAI(
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

    if bot.user in message.mentions:

        async with message.channel.typing():

            messages = []

            async for msg in message.channel.history(limit=50):
                if msg.content and msg.id != message.id:
                    messages.append(f"{msg.author.name}: {msg.content}")

            messages.reverse()

            chat_text = "\n".join(messages)

            completion = client.chat.completions.create(
                model="llama3-70b-8192",
                messages=[
                    {"role": "system", "content": "Riassumi questa conversazione Discord in modo breve e chiaro."},
                    {"role": "user", "content": chat_text}
                ]
            )

            summary = completion.choices[0].message.content

        await message.reply(
            f"📋 **Riassunto della conversazione:**\n{summary}",
            mention_author=False
        )

    await bot.process_commands(message)

bot.run(TOKEN)