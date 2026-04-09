import discord
from discord.ext import commands
import os
from openai import OpenAI
from dotenv import load_dotenv
from flask import Flask
from threading import Thread

# ==========================
# KEEP ALIVE SERVER
# ==========================
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

# ==========================
# SETUP & API CONFIG
# ==========================
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
GROQ_KEY = os.getenv("GROQ_API_KEY")

# Usiamo Groq tramite l'interfaccia OpenAI (molto stabile)
client_ai = OpenAI(
    api_key=GROQ_KEY,
    base_url="https://api.groq.com/openai/v1"
)

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# ==========================
# EVENTI
# ==========================
@bot.event
async def on_ready():
    print(f"Bot (Groq API) pronto come {bot.user}")

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    is_mention = bot.user in message.mentions
    is_reply_to_bot = (
        message.reference 
        and message.reference.resolved 
        and message.reference.resolved.author == bot.user
    )

    if is_mention and not is_reply_to_bot:
        async with message.channel.typing():
            try:
                # 1. Recupero 100 messaggi
                messages = []
                async for msg in message.channel.history(limit=101):
                    if msg.content and msg.id != message.id:
                        messages.append(f"{msg.author.name}: {msg.content}")

                messages.reverse()
                chat_text = "\n".join(messages)

                # 2. Richiesta a Groq (Llama 3 è velocissimo e parla italiano)
                completion = client_ai.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[
                        {
                            "role": "system", 
                            "content": "Sei un assistente che riassume conversazioni Discord. "
                                       "Crea un riassunto in italiano, chiaro, usando punti elenco. "
                                       "Ignora i messaggi di spam o i comandi del bot."
                        },
                        {"role": "user", "content": f"Riassumi questi 100 messaggi:\n{chat_text}"}
                    ]
                )

                summary = completion.choices[0].message.content

                # 3. Risposta
                await message.reply(
                    f"**Riassunto degli ultimi 100 messaggi:**\n{summary}",
                    mention_author=False
                )

            except Exception as e:
                await message.reply(f"❌ Errore durante il riassunto: {e}")

    await bot.process_commands(message)

if TOKEN and GROQ_KEY:
    bot.run(TOKEN)
else:
    print("ERRORE: Assicurati di avere DISCORD_TOKEN e GROQ_API_KEY nel file .env")