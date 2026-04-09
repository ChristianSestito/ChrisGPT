import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
from flask import Flask
from threading import Thread
from transformers import pipeline

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
# SETUP & TOKEN
# ==========================
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# ==========================
# MODELLO LOCALE (IT5)
# ==========================
try:
    # Utilizziamo text2text-generation per massima compatibilità con IT5
    summarizer = pipeline("text2text-generation", model="it5/it5-base-news-summarization")
except Exception as e:
    print(f"Errore caricamento modello: {e}")
    summarizer = pipeline("text-generation", model="it5/it5-base-news-summarization")

def generate_summary(chat_text):
    """Genera il riassunto utilizzando il modello locale."""
    try:
        # Prepariamo l'input limitando i caratteri per la memoria del modello
        input_text = f"Riassumi la seguente conversazione Discord: {chat_text[:3500]}"
        
        res = summarizer(input_text, max_length=300, min_length=80, do_sample=False)
        
        # Recupera il testo generato indipendentemente dalla chiave usata dal modello
        return res[0].get('generated_text', res[0].get('summary_text', "Errore nella generazione."))
    except Exception as e:
        return f"❌ Errore locale: {e}"

# ==========================
# EVENTI BOT
# ==========================
@bot.event
async def on_ready():
    print(f"Bot locale pronto come {bot.user}")

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    # Controlla se il bot è menzionato
    is_mention = bot.user in message.mentions
    # Ignora le risposte dirette ai messaggi del bot per evitare loop
    is_reply_to_bot = message.reference and message.reference.resolved and message.reference.resolved.author == bot.user

    if is_mention and not is_reply_to_bot:
        async with message.channel.typing():
            
            # Recupero degli ultimi 100 messaggi
            messages = []
            async for msg in message.channel.history(limit=101):
                if msg.content and msg.id != message.id:
                    messages.append(f"{msg.author.name}: {msg.content}")

            messages.reverse()
            chat_text = "\n".join(messages)

            # Generazione tramite funzione locale
            summary = generate_summary(chat_text)

        # Risposta finale simile allo stile del primo codice
        await message.reply(
            f"**Riassunto degli ultimi 100 messaggi:**\n{summary}",
            mention_author=False
        )

    await bot.process_commands(message)

# ==========================
# AVVIO
# ==========================
if TOKEN:
    bot.run(TOKEN)
else:
    print("ERRORE: Inserisci il DISCORD_TOKEN nel file .env")