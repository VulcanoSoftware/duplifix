import discord
from discord.ext import commands
import hashlib

# Bot configuratie
intents = discord.Intents.default()
intents.message_content = True
intents.guild_messages = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Dictionary om berichten bij te houden
message_hashes = {}

@bot.event
async def on_ready():
    print(f'{bot.user} is nu online!')

@bot.event
async def on_message(message):
    # Negeer berichten van de bot zelf
    if message.author == bot.user:
        return

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
