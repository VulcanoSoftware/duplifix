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

@bot.event
async def on_ready():
    print(f'{bot.user} is online!')
    # Start de achtergrondtaak voor console clearing
    bot.loop.create_task(periodieke_console_clear())
    # Controleer historische berichten bij opstarten
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
    for guild in bot.guilds:
        for channel in guild.text_channels:
            try:               
                # Verzamel ALLE berichten
                messages = []
                async for message in channel.history(limit=None):
                    if not message.author.bot:
                        messages.append(message)
                
                # Groepeer berichten op inhoud
                message_groups = {}
                for message in messages:
                    content = message.content.strip().lower()
                    if content:  # Negeer lege berichten
                        if content not in message_groups:
                            message_groups[content] = []
                        message_groups[content].append(message)
                
                # Verwijder duplicaten, behoud het oudste bericht
                total_duplicates = 0
                for content, msg_list in message_groups.items():
                    if len(msg_list) > 1:
                        # Sorteer op datum, oudste eerst
                        msg_list.sort(key=lambda x: x.created_at)
                        
                        # Behoud het eerste (oudste) bericht, verwijder de rest
                        for duplicate in msg_list[1:]:
                            try:
                                await duplicate.delete()
                                total_duplicates += 1
                            except discord.errors.Forbidden:
                                print(f'Geen rechten om bericht te verwijderen')
                            except Exception as e:
                                print(f'Fout bij verwijderen: {e}')
                
            except discord.Forbidden:
                print(f'Geen toegang tot kanaal: {channel.name}')
            except Exception as e:
                print(f'Fout bij controleren van kanaal {channel.name}: {e}')
    

@bot.event
async def on_message(message):
    # Negeer berichten van de bot zelf
    if message.author == bot.user:
        return

    # Voeg een cooldown check toe
    current_time = time.time()
    if hasattr(bot, 'last_check_time') and current_time - bot.last_check_time < 10:
        return
    
    bot.last_check_time = current_time

    # Bereken een hash van de berichtinhoud
    content_hash = hashlib.md5(message.content.encode()).hexdigest()
    
    # Controleer of dit bericht al eerder is gezien in dit kanaal
    channel_id = str(message.channel.id)
    if channel_id not in message_hashes:
        message_hashes[channel_id] = {}
    
    if content_hash in message_hashes[channel_id]:
        # Als het bericht een duplicaat is, verwijder het nieuwe bericht
        try:
            await message.delete()
            await message.channel.send(f"Dubbel bericht gedetecteerd en verwijderd van {message.author.mention}", delete_after=5)
        except discord.errors.Forbidden:
            print("Geen rechten om het bericht te verwijderen")
    else:
        # Voeg het nieuwe bericht toe aan de hash dictionary
        message_hashes[channel_id][content_hash] = {
            'content': message.content,
            'author': message.author.id,
            'timestamp': message.created_at
        }

    await bot.process_commands(message)

# Commando om de cache te wissen
@bot.command()
@commands.has_permissions(administrator=True)
async def clear_cache(ctx):
    message_hashes.clear()
    await ctx.send("Cache is gewist!")

# Start de bot (vervang 'YOUR_TOKEN' met je Discord bot token)
bot.run('YOUR_TOKEN')
