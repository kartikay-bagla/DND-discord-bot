import discord
from discord.ext import commands
import Secrets
import json
from firebase_logger import FirebaseClient
meta_file = 'meta.json'
meta_collection = 'metadata'

# Firebase setup
fclient = FirebaseClient(Secrets.FIREBASE_CRED_PATH)

# Discord setup
intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents)

# util functions
def get_preference_firestore():
    data = fclient.get_preference(meta_collection)
    with open(meta_file, 'w', encoding='utf-8') as file:
        json.dump(data, file, ensure_ascii=False, indent=4)

def save_preference(guild_id, preference_type, preference_id):
    with open(meta_file, 'r') as file:
        data = json.load(file)
    data[str(guild_id)][preference_type] = preference_id
    fclient.set_preference(data, meta_collection)
    with open(meta_file, 'w') as file:
        json.dump(data, file, indent=4)
        
def get_preference(guild_id, key: str):
    with open(meta_file, 'r') as file:
        data = json.load(file)
        return data.get(str(guild_id), {}).get(key)

def log_firebase(ctx, players:list):
    fcollection = fclient.get_collection(str(ctx.guild.id))
    return fclient.log_players(fcollection, players)

def get_role(ctx, role_name: str):
    role_id = get_preference(ctx.guild.id, role_name)
    for i in ctx.guild.roles:
        if i.id == role_id:
            return i

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

# setup 
@bot.event
async def on_ready():
    print('-'*50)
    print(f'{bot.user} has connected to Discord!')
    get_preference_firestore()
    print('retreived')
    print('-'*50)

# test command
@bot.command(name='hello')
async def on_hello(ctx):
    print('-'*50)
    print("printing hello")
    await send_message(ctx, 'hello')
    print('-'*50)

# server specific setup
@bot.command(name='setrole')
async def set_role(ctx, role_for: str, *roles: discord.Role):
    print('-'*50)
    if role_for == 'player':
        save_preference(ctx.guild.id, 'player_role', [role.id for role in roles])
    elif role_for == 'gm':
        save_preference(ctx.guild.id, 'gm_role', [role.id for role in roles])
    elif role_for == 'suspend':
        save_preference(ctx.guild.id, 'suspended_role', [role.id for role in roles])
    elif role_for == 'mod':
        save_preference(ctx.guild.id, 'mod_role', [role.id for role in roles])
    else:
        await send_message(ctx,f'select valid rolefor : player, gm, suspended, mod')
        print('select valid option')
        print('-'*50)
        return
    print(f'set role for {role_for}')
    for role in roles:
        if role.mentionable:
            await send_message(ctx,f'{role_for} role set to {role.mention}')
        else:
            await send_message(ctx,f'{role_for} role set to {role.name}')
    print('-'*50)


@bot.command(name='setchannel')
async def set_channel(ctx, channel: discord.TextChannel):
    save_preference(ctx.guild.id, 'channel', channel.id)
    await send_message(ctx, f'Output channel set to {channel.mention}')

@bot.command(name='loadmembers')
async def set_logger(ctx):
    print('-'*50)
    player_role = get_role(ctx, 'player_role')
    if player_role:
        dnd_players = [i for i in ctx.guild.members if (not i.bot) and(player_role in i.roles)]
        count = log_firebase(ctx, dnd_players)
        print(f'{count} players logged')
        await send_message(ctx,f'{count} players logged')
    else:
        await send_message(ctx,'Player role not set, set it with !setplayerrole')
    print('-'*50)

# logging
@bot.command(name='logsession')
async def log_session(ctx, *players: discord.Member):
    print('-'*50)
    gm_role = get_role(ctx, 'gm_role')
    if not gm_role:
        await send_message(ctx,'No gm role set')
        print('No gm role set')
    elif gm_role not in ctx.author.roles:
        await send_message(ctx,'Command can only be used by gms')
        print('Command can only be used by gms')
    elif not players:
        await send_message(ctx,'No players entered')
        print('No players entered')
    else:
        fcollection = fclient.get_collection(str(ctx.guild.id))
        fclient.log_session(fcollection,list(players), ctx.author)
        message = f'Session logged for:\n'
        ps = [i.id for i in players]
        print(f"logged session for : {ps}")
        for i in players:
            message += f'{i.name}\n'
        message += f'session logged by {ctx.author.name}\n'
        await send_message(ctx,message)
    print('-'*50)

# purging
@bot.command(name='purgeinactive')
async def purge_inactive(ctx):
    print('-'*50)
    mod_role = get_role(ctx, 'mod_role')
    if mod_role not in ctx.author.roles:
        print('insufficient permissions')
        await send_message(ctx, 'you must be a mod to run this command')
        return
    player_role = get_role(ctx, 'player_role')
    gm_role = get_role(ctx, 'gm_role')
    suspended_role = get_role(ctx, 'suspended_role')
    if player_role and mod_role and gm_role and suspended_role:
        test_players = [i for i in ctx.guild.members if (player_role in i.roles) and (mod_role not in i.roles)]
        fcollection = fclient.get_collection(str(ctx.guild.id))
        inactive = fclient.get_inactive_players(fcollection,test_players)
        message = 'pruged : \n'
        for player in inactive:
            await player.remove_roles(player_role, gm_role)
            await player.add_roles(suspended_role)
            print(f'removed roles for {player.name}')
            message += f'{player.name}\n'
        await send_message(ctx, message)
    else:
        print('set valid player, mod, gm and suspended roles!')
        await send_message(ctx, 'set valid player, mod, gm and suspended roles!')
    print('-'*50)

@bot.command(name='purgeinactivegm')
async def purge_inactive_gm(ctx):
    print('-'*50)
    mod_role = get_role(ctx, 'mod_role')
    if mod_role not in ctx.author.roles:
        print('insufficient permissions')
        await send_message(ctx, 'you must be a mod to run this command')
        return
    gm_role = get_role(ctx, 'gm_role')
    suspended_role = get_role(ctx, 'suspended_role')
    if mod_role and gm_role and suspended_role:
        test_gms = [i for i in ctx.guild.members if (gm_role in i.roles) and (mod_role not in i.roles)]
        fcollection = fclient.get_collection(str(ctx.guild.id))
        inactive = fclient.get_inactive_gms(fcollection,test_gms)
        message = 'purged gms : \n'
        for gm in inactive:
            await gm.remove_roles(gm_role)
            print(f'removed role for {gm.name}')
            message += f'{gm.name}\n'
        await send_message(ctx, message)
    else:
        print('set valid mod, gm and suspended roles!')
        await send_message(ctx, 'set valid mod, gm and suspended roles!')
    print('-'*50)

bot.run(Secrets.BOT_TOKEN)