import discord
from discord.ext import commands
from datetime import datetime
import Secrets
import json
from firebase_logger import FirebaseClient
meta_file = 'meta.json'
fclient = FirebaseClient(Secrets.FIREBASE_CRED_PATH)

intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents)
with open(meta_file) as meta:
    metadata = json.load(meta)

def save_preference(guild_id, preference_type, preference_id):
    with open(meta_file, 'r') as file:
        data = json.load(file)
    data[str(guild_id)][preference_type] = preference_id
    with open(meta_file, 'w') as file:
        json.dump(data, file, indent=4)
        
def get_preference(guild_id, key: str):
    with open(meta_file, 'r') as file:
        data = json.load(file)
        return data.get(str(guild_id), {}).get(key)

def log_firebase(ctx, players:list):
    fcollection = fclient.get_collection(str(ctx.guild.id))
    return fclient.log_players(fcollection, players)


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

@bot.command(name='loadmembers')
async def set_logger(ctx):
    player_role = None
    player_role_id = get_preference(ctx.guild.id, 'player_role')
    for i in ctx.guild.roles:
        if i.id == player_role_id:
            player_role = i
            break
    if player_role:
        dnd_players = [i for i in ctx.guild.members if (not i.bot) and(player_role in i.roles)]
        count = log_firebase(ctx, dnd_players)
        print(f'{count} players logged')
        await send_message(ctx,f'{count} players logged')
    else:
        await send_message(ctx,'Player role not set, set it with !setplayerrole')

@bot.command(name='hello')
async def on_hello(ctx):
    print("printing hello")
    await send_message(ctx, 'hello')

@bot.command(name='setplayerrole')
async def set_player_role(ctx, role: discord.Role):
    save_preference(ctx.guild.id, 'player_role', role.id)
    if role.mentionable:
        await send_message(ctx,f'Output channel set to {role.mention}')
    else:
        await send_message(ctx,f'Output channel set to {role.name}')

@bot.command(name='setchannel')
async def set_channel(ctx, channel: discord.TextChannel):
    save_preference(ctx.guild.id, 'channel', channel.id)
    await send_message(f'Output channel set to {channel.mention}')

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