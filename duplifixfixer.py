import discord
from discord.ext import commands
from datetime import datetime, timedelta
import hashlib
import os
import asyncio 
import time

# Bot configuratie
intents = discord.Intents.default()
intents.message_content = True
intents.guild_messages = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Dictionary om berichten bij te houden
message_hashes = {}

# Functie om dubbele berichten op te slaan
def save_duplicate_message(message):
    with open('duplifixfixer.txt', 'a', encoding='utf-8') as f:
        f.write(f"{message.content.strip()}\n")

# Functie om dubbele berichten te laden
def load_duplicate_messages():
    if not os.path.exists('duplifixfixer.txt'):
        return set()
    
    duplicates = set()
    with open('duplifixfixer.txt', 'r', encoding='utf-8') as f:
        for line in f:
            content = line.strip().lower()
            duplicates.add(content)
    return duplicates

def clean_duplifixfixer_file():
    try:
        # Lees alle berichten
        unique_messages = set()
        if os.path.exists('duplifixfixer.txt'):
            with open('duplifixfixer.txt', 'r', encoding='utf-8') as f:
                for line in f:
                    # Haal alleen de berichtinhoud op (eerste deel voor de |)
                    content = line.strip().split('|')[0].lower()
                    unique_messages.add(content)
        
        # Schrijf unieke berichten terug
        with open('duplifixfixer.txt', 'w', encoding='utf-8') as f:
            for message in sorted(unique_messages):  # Sorteer voor betere leesbaarheid
                f.write(f"{message}\n")
        
        return unique_messages
    except Exception as e:
        print(f"Fout bij opschonen van duplifixfixer.txt: {e}")
        return set()

@bot.event
async def on_ready():
    print(f'{bot.user} is online!')
    # Start de achtergrondtaak voor console clearing
    bot.loop.create_task(periodieke_console_clear())
    # Eerst het bestand opschonen
    global known_duplicates
    known_duplicates = clean_duplifixfixer_file()
    await check_historical_messages()

# Nieuwe functie voor periodieke console clearing
async def periodieke_console_clear():
    laatste_clear = datetime.now()
    while True:
        if datetime.now() - laatste_clear > timedelta(hours=6):
            os.system('cls' if os.name == 'nt' else 'clear')
            laatste_clear = datetime.now()
            print(f'{bot.user} is online!')  # Herprint de status message
        await asyncio.sleep(60)  # Check elke minuut

async def check_historical_messages():
    
    # Verzamel eerst ALLE berichten van ALLE kanalen
    all_messages = {}  # content -> list of messages
    
    for guild in bot.guilds:
        for channel in guild.text_channels:
            try:               
                async for message in channel.history(limit=None):
                    if not message.author.bot:
                        content = message.content.strip().lower()
                        if content:  # Negeer lege berichten
                            if content not in all_messages:
                                all_messages[content] = []
                            all_messages[content].append(message)
                            await asyncio.sleep(5)  # 5 seconden vertraging bij elk bericht
                
                await asyncio.sleep(5)  # 5 seconden vertraging tussen kanalen
            except discord.Forbidden:
                print(f'Geen toegang tot kanaal: {channel.name}')
            except Exception as e:
                print(f'Fout bij verzamelen uit kanaal {channel.name}: {e}')
    
    
    # Verwerk nu alle dubbele berichten
    duplicates_removed = 0
    for content, messages in all_messages.items():
        if len(messages) > 1:
            messages.sort(key=lambda x: x.created_at)
            
            for duplicate in messages[1:]:
                try:
                    await asyncio.sleep(5)  # 5 seconden vertraging voor verwijdering
                    await duplicate.delete()
                    save_duplicate_message(duplicate)
                    known_duplicates.add(content)
                    duplicates_removed += 1
                except discord.errors.Forbidden:
                    print(f'Geen rechten om bericht te verwijderen in {duplicate.channel.name}')
                except Exception as e:
                    print(f'Fout bij verwijderen: {e}')
            await asyncio.sleep(5)  # 5 seconden vertraging tussen groepen duplicaten
    

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    content = message.content.strip().lower()
    await asyncio.sleep(5)  # 5 seconden vertraging voor eerste controle
    
    # Check eerst tegen bekende duplicaten uit het bestand
    if content in known_duplicates:
        try:
            await asyncio.sleep(5)  # 5 seconden vertraging voor verwijdering
            await message.delete()
            await message.channel.send(f"Dubbel bericht gedetecteerd en verwijderd van {message.author.mention}", delete_after=5)
            return
        except discord.errors.Forbidden:
            print("Geen rechten om het bericht te verwijderen")
    
    # Check vervolgens tegen alle recente berichten in alle kanalen
    for guild in bot.guilds:
        for channel in guild.text_channels:
            try:
                async for old_message in channel.history(limit=100):
                    await asyncio.sleep(5)  # 5 seconden vertraging voor elke berichtcontrole
                    if old_message.id != message.id and old_message.content.strip().lower() == content:
                        try:
                            await asyncio.sleep(5)  # 5 seconden vertraging voor verwijdering
                            await message.delete()
                            save_duplicate_message(message)
                            known_duplicates.add(content)
                            await message.channel.send(f"Dubbel bericht gedetecteerd en verwijderd van {message.author.mention}", delete_after=5)
                            return
                        except discord.errors.Forbidden:
                            print("Geen rechten om het bericht te verwijderen")
                await asyncio.sleep(5)  # 5 seconden vertraging tussen kanaal checks
            except discord.Forbidden:
                continue
            except Exception as e:
                print(f"Fout bij controleren van kanaal: {e}")

    await bot.process_commands(message)

# Commando om de cache te wissen
@bot.command()
@commands.has_permissions(administrator=True)
async def clear_cache(ctx):
    message_hashes.clear()
    await ctx.send("Cache is gewist!")

# Start de bot (vervang 'YOUR_TOKEN' met je Discord bot token)
bot.run('YOUR_TOKEN')
