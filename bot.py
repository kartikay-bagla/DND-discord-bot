import discord
from discord.ext import commands
from datetime import datetime
import Secrets
import json
meta_file = 'meta.json'

intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents)
with open(meta_file) as meta:
    metadata = json.load(meta)

def save_preference(guild_id, channel_id):
    with open(meta_file, 'r') as file:
        data = json.load(file)
    data[str(guild_id)] = {"output_channel": channel_id}
    with open(meta_file, 'w') as file:
        json.dump(data, file, indent=4)
        
def get_preference(guild_id, key):
    with open(meta_file, 'r') as file:
        data = json.load(file)
        return data.get(str(guild_id), {}).get(key)
    
def log_firebase(players:list):
    pass
    
def log_message(players:list):
    pass

async def send_message(ctx, message: str):
    channel_id = get_preference(ctx.guild.id, 'output_channel')
    if channel_id:
        channel = bot.get_channel(channel_id)
        if channel:
            await channel.send(message)
        else:
            await ctx.send("Output channel is not set or not found.")
    else:
        await ctx.send(message)

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')

@bot.command(name='hello')
async def on_hello(ctx):
    print("printing hello")
    await send_message(ctx, 'hello')

@bot.command(name='setchannel')
async def set_channel(ctx, channel: discord.TextChannel):
    save_preference(ctx.guild.id, channel.id)
    await ctx.send(f'Output channel set to {channel.mention}')

@bot.command(name='logsession')
async def log_session(ctx, *players: discord.Member):
    if not players:
        await send_message(ctx,'No players entered')
    else:
        message = f'Session logged for:\n'
        ps = [i.id for i in players]
        print(f"logged session for : {ps}")
        for i in players:
            message += f'{i.mention}\n'
        await send_message(ctx,message)

bot.run(Secrets.BOT_TOKEN)