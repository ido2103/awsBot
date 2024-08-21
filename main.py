import discord
from discord.ext import commands
import os
from googlesearch import search
import asyncio

# Read the token from token.txt
with open('token.txt', 'r') as file:
    TOKEN = file.read().strip()

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix=';', intents=intents)

# Add this function
def is_allowed_channel(ctx):
    if ctx.guild is None:
        print(f'{ctx.author} tried to use a command in a DM')
        return True
    if ctx.guild.id != 1266050232836165716:
        return True
    return ctx.channel.name in ['bot-commands', 'staff-bot-commands']

# Add this before loading cogs
bot.add_check(is_allowed_channel)

# Load cogs
async def load():
    for file_name in os.listdir('.'):
        if file_name.endswith('.py') and file_name != 'main.py':
            await bot.load_extension(f'{file_name[:-3]}')
            print(f'Loaded {file_name}')

async def main():
    await load()
    await bot.start(TOKEN)

if __name__ == '__main__':
    asyncio.run(main())    
    
    
