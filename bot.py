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

# --- LISTA NERA UTENTI ---
# Inserisci qui gli ID degli utenti da ignorare (separati da virgola)
# Esempio: BLACKLIST_ID = [123456789012345678, 987654321098765432]
BLACKLIST_ID = [958840410644557834, 881168994151829554] 

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
    print(f"Utenti in blacklist: {len(BLACKLIST_ID)}")

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
                # 1. Recupero messaggi filtrati
                messages = []
                # Cerchiamo di recuperare abbastanza messaggi per averne 100 validi
                async for msg in message.channel.history(limit=150):
                    # CONDIZIONI PER AGGIUNGERE IL MESSAGGIO:
                    # - L'autore non deve essere in BLACKLIST_ID
                    # - Il messaggio non deve essere il comando stesso
                    # - Il messaggio deve avere del testo
                    if (msg.author.id not in BLACKLIST_ID and 
                        msg.id != message.id and 
                        msg.content):
                        
                        messages.append(f"{msg.author.name}: {msg.content}")
                        
                    # Se abbiamo raggiunto 100 messaggi filtrati, ci fermiamo
                    if len(messages) >= 100:
                        break

                messages.reverse()
                chat_text = "\n".join(messages)

                # 2. Richiesta a Groq con prompt conciso
                completion = client_ai.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[
                        {
                            "role": "system", 
                            "content": (
                                "Sei un assistente riassuntivo. Sii ultra-conciso. "
                                "Usa solo punti elenco brevi. Massimo 5-7 punti. "
                                "Ignora spam e bot. Usa solo l'italiano."
                            )
                        },
                        {"role": "user", "content": f"Riassumi questi messaggi:\n{chat_text}"}
                    ],
                    temperature=0.2
                )

                summary = completion.choices[0].message.content

                # 3. Risposta
                await message.reply(
                    f"**Riassunto degli ultimi 100 messaggi (filtrati):**\n{summary}",
                    mention_author=False
                )

            except Exception as e:
                await message.reply(f"❌ Errore durante il riassunto: {e}")

    await bot.process_commands(message)

if TOKEN and GROQ_KEY:
    bot.run(TOKEN)
else:
    print("ERRORE: Mancano le chiavi API nel file .env")