# Music.py

import discord
import youtube_dl
from discord.ext import commands

# Silence bug report messages
from Song import Song
from VoiceState import VoiceState
from YTDLError import YTDLError
from YTDLSource import YTDLSource

youtube_dl.utils.bug_reports_message = lambda: ''


# youtube-dl is a command line program used to download videos from sites
class Music(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.voice_states = {}

    def get_voice_state(self, ctx: commands.Context):
        state = self.voice_states.get(ctx.guild.id)
        if not state:
            state = VoiceState(self.bot, ctx)
            self.voice_states[ctx.guild.id] = state

        return state

    def cog_unload(self):
        for state in self.voice_states.values():
            self.bot.loop.create_task(state.stop())

    def cog_check(self, ctx: commands.Context):
        if not ctx.guild:
            raise commands.NoPrivateMessage('This command can\'t be used in DM channels.')

        return True

    async def cog_before_invoke(self, ctx: commands.Context):
        ctx.voice_state = self.get_voice_state(ctx)

    async def cog_command_error(self, ctx: commands.Context, error: commands.CommandError):
        await ctx.send('An error occurred: {}'.format(str(error)))

    # Joins the sender's voice channel
    @commands.command(name='join', aliases=['connect'])
    async def _join(self, ctx: commands.Context):

        destination = ctx.author.voice.channel
        if ctx.voice_state.voice:
            await ctx.voice_state.voice.move_to(destination)
            return

        ctx.voice_state.voice = await destination.connect()

    # Clears the queue and leaves the voice channel
    @commands.command(name='leave', aliases=['disconnect'])
    async def _leave(self, ctx: commands.Context):
        if not ctx.voice_state.voice:
            return await ctx.send('Not connected to any voice channel')

        await ctx.voice_state.stop()
        del self.voice_states[ctx.guild.id]

    # Sets the volume of the player
    @commands.command(name='volume')
    async def _volume(self, ctx: commands.Context, *, volume: int):
        if not ctx.voice_state.is_playing:
            return await ctx.send('Nothing is currently being played')
        if 0 > volume > 100:
            return await ctx.send('Volume must be between 0 and 100')
        ctx.voice_state.volume = volume / 100
        await ctx.send('Volume of the player set to {}%'.format(volume))

    # Displays the currently playing audio
    @commands.command(name='now', aliases=['current', 'playing'])
    async def _now(self, ctx: commands.Context):
        if not ctx.voice_state.voice.is_playing():
            return await ctx.send('Nothing is currently being played')
        await ctx.send(embed=ctx.voice_state.current.create_embed())

    # Pauses the currently playing audio
    @commands.command(name='pause')
    async def _pause(self, ctx: commands.Context):
        if ctx.voice_state.voice.is_playing():
            ctx.voice_state.voice.pause()
            await ctx.send('Audio player has been paused')

    # Resumes a currently paused audio
    @commands.command(name='resume')
    async def _resume(self, ctx: commands.Context):
        if ctx.voice_state.voice.is_paused():
            ctx.voice_state.voice.resume()
            await ctx.send('Audio player has resumed')

    # Skips the current audio
    @commands.command(name='skip')
    async def _skip(self, ctx: commands.Context):
        if not ctx.voice_state.is_playing:
            return await ctx.send('Nothing is currently being played')

        ctx.voice_state.skip()
        await ctx.send(f'Skipped **{ctx.voice_state.current.source.title}**')

    # Skips the current audio and plays specified index if it exists
    @commands.command(name='skipto')
    async def _skipto(self, ctx: commands.Context, index: int):
        try:
            i = int(index)
        except ValueError:
            return await ctx.send(f'Index must be an integer')

        if not ctx.voice_state.is_playing:
            return await ctx.send('Nothing is currently being played')

        if len(ctx.voice_state.songs) == 0:
            return await ctx.send('Audio playlist is empty')

        # Move entry at index to front of queue
        song = ctx.voice_state.songs._queue[i - 1]
        ctx.voice_state.songs.remove(i - 1)
        ctx.voice_state.songs._queue.appendleft(song)

        ctx.voice_state.skip()
        await ctx.send(f'Skipped **{ctx.voice_state.current.source.title}**')

    # Stops playing audio and clears the queue
    @commands.command(name='stop')
    async def _stop(self, ctx: commands.Context):
        ctx.voice_state.songs.clear()
        ctx.voice_state.voice.stop()
        await ctx.send('Audio player has stopped')

    # Shows the audio playlist
    @commands.command(name='queue', aliases=['playlist'])
    async def _queue(self, ctx: commands.Context):
        if len(ctx.voice_state.songs) == 0:
            return await ctx.send('Audio playlist is empty')

        queue = ''
        for i, song in enumerate(ctx.voice_state.songs, start=0):
            queue += '`{0}.` [**{1.source.title}**]({1.source.url})\n'.format(i + 1, song)

        embed = (discord.Embed(description='**{} tracks:**\n\n{}'.format(len(ctx.voice_state.songs), queue)))
        await ctx.send(embed=embed)

    # Shuffles the audio playlist
    @commands.command(name='shuffle')
    async def _shuffle(self, ctx: commands.Context):
        if len(ctx.voice_state.songs) == 0:
            return await ctx.send('Audio playlist is empty')

        ctx.voice_state.songs.shuffle()
        await ctx.send('Audio playlist has been shuffled')

    # Swaps two entries in audio paylist
    @commands.command(name='swap', aliases=['switch'])
    async def _swap(self, ctx: commands.Context, x, y):
        try:
            x = int(x)
            y = int(y)
        except ValueError:
            return await ctx.send(f'Indices must be integers')

        if len(ctx.voice_state.songs) == 0:
            return await ctx.send('Audio playlist is empty')

        ctx.voice_state.songs.swap(x - 1, y - 1)
        await ctx.send(f'Swapped entries of indices **{x}** and **{y}**')

    # Removes a song from the playlist at a given index
    @commands.command(name='remove')
    async def _remove(self, ctx: commands.Context, index):
        try:
            i = int(index)
        except ValueError:
            response = f'Index must be an integer'
            return await ctx.send(response)

        if len(ctx.voice_state.songs) == 0:
            return await ctx.send('Audio playlist is empty')

        title = ctx.voice_state.songs.get_title(i - 1)
        ctx.voice_state.songs.remove(i - 1)
        await ctx.send(f'Removed **{title}** from the playlist')

    # Adds a song to the end of playlist
    @commands.command(name='play')
    async def _play(self, ctx: commands.Context, *, search: str):
        if not ctx.voice_state.voice:
            await ctx.invoke(self._join)

        async with ctx.typing():
            try:
                source = await YTDLSource.create_source(ctx, search, loop=self.bot.loop)
            except YTDLError as e:
                await ctx.send('An error occurred while processing this request: {}'.format(str(e)))
            else:
                song = Song(source)

                await ctx.voice_state.songs.put(song)
                await ctx.send('Enqueued {}'.format(str(source)))

    # Verifies the audio player's voice state
    @_join.before_invoke
    @_play.before_invoke
    async def ensure_voice_state(self, ctx: commands.Context):
        if not ctx.author.voice or not ctx.author.voice.channel:
            raise commands.CommandError('You are not connected to any voice channel')

        if ctx.voice_client:
            if ctx.voice_client.channel != ctx.author.voice.channel:
                raise commands.CommandError('Already in a voice channel')
