# MegumiBot.py
import os
import random

import aioconsole
import discord
from discord.ext import commands
from dotenv import load_dotenv

import Music


class MegumiBot(commands.Cog):
    def __init__(self, robot: commands.Bot):
        self.bot = robot

    # Displays a list of commands
    @commands.command(name='help')
    async def help(self, ctx):
        response = (f"**General Commands**\n"
                    f"!help - Display a list of commands\n"
                    f"\n"
                    f"**Random Commands**\n"
                    f"!coinflip - Flips a coin\n"
                    f"!roll XdY - Rolls X number of dice with Y number of faces\n"
                    f"\n"
                    f"**Audio Commands**\n"
                    f"!join - Joins the user's voice channel\n"
                    f"!leave - Clears the playlist and leaves the voice channel\n"
                    f"!play QUERY - Plays audio from a search query (or URL)\n"
                    f"!now - Displays the currently playing audio\n"
                    f"!pause - Pauses the audio player\n"
                    f"!resume - Resumes the audio player\n"
                    f"!skip - Skips the current audio\n"
                    f"!skipto INDEX - Skips the current audio and plays entry at given INDEX\n"
                    f"!stop - Stops the audio player and clears the playlist\n"
                    f"!queue - Displays the playlist\n"
                    f"!shuffle - Shuffles the playlist\n"
                    f"!swap X Y - Swaps the playlist entries at indices X and Y\n"
                    f"!remove INDEX - Removes an entry from the playlist at the given INDEX\n"
                    f"")
        await ctx.send(response)

    # Rolls specified number of dice with specified number of faces
    @commands.command(name='coinflip')
    async def coinflip(self, ctx):
        n = random.randint(0, 1)
        if n == 0:
            await ctx.send(f'{ctx.message.author.mention}: Heads')
        if n == 1:
            await ctx.send(f'{ctx.message.author.mention}: Tails')

    @commands.command(name='roll')
    async def roll(self, ctx, args):
        try:
            x = int(args.split('d')[0])  # Number of dice
            y = int(args.split('d')[1])  # Number of faces
        except ValueError:
            return await ctx.send(f"X and Y must be integers")

        if x < 1 or y < 1:
            return await ctx.send(f"X and Y must be at least 1")
        response = f"{ctx.message.author.mention}: {x}d{y} = "

        sum_of_rolls = 0
        for i in range(x):
            roll = random.randint(1, y)
            sum_of_rolls += roll

            response += f"{roll}"
            if i != x - 1:
                response += f" + "

        response += f" = {sum_of_rolls}\n"

        await ctx.send(response)


# Retrieves bot token from .env file
load_dotenv()
token = os.getenv('DISCORD_TOKEN')

# Client represents a connection to Discord that handles events, tracks state,
# and interacts with Discord APIs
bot = commands.Bot(command_prefix='!')

# Removes the default help command
bot.remove_command('help')

bot.add_cog(MegumiBot(bot))
bot.add_cog(Music.Music(bot))


@bot.event
async def on_ready():
    print(f'{bot.user.name} has connected to the following guilds:')
    for guild in bot.guilds:
        print(f'{guild.name} (id: {guild.id})')

    # Changes bot status
    await bot.change_presence(activity=discord.Game(name='with frens <3'))


# Console commands for bot
async def background_task():
    await bot.wait_until_ready()
    current_guild = bot.guilds[0]
    current_channel = current_guild.channels[0]
    while not bot.is_closed():
        console_input = await aioconsole.ainput('')
        args = console_input.split()

        # Display connected guilds and channels
        if args[0] == '!connected':
            print(f'{bot.user.name} is connected to the following guilds and channels:')
            for guild in bot.guilds:
                print(f'{guild.name}')
                for channel in guild.channels:
                    print(f'\t{channel.name}')
            print(f'')

        # Displays current guild and channel
        if args[0] == '!display':
            print(f'Current Guild: {current_guild.name}\n'
                  f'Current Channel: {current_channel.name}\n')

        # Selects a guild by name or ID
        if args[0] == '!guild':
            found = False
            for guild in bot.guilds:
                if guild.name == console_input[7:] or guild.id == args[1]:
                    current_guild = guild
                    found = True
                    print(f'Changed guild to {guild.name}')
                    break
            if not found:
                print(f'Unable to change guild')

        # Selects a channel by name or ID
        if args[0] == '!channel':
            found = False
            for channel in current_guild.channels:
                if channel.name == console_input[9:] or channel.id == args[1]:
                    current_channel = channel
                    found = True
                    print(f'Changed channel to {channel.name}')
                    break
            if not found:
                print(f'Unable to change channel')

        # Sends message to current selected channel
        if args[0] == '!say':
            await current_channel.send(console_input[5:])


bot.loop.create_task(background_task())
bot.run(token)
