import discord
from discord.ext import commands


class MyHelpCommand(commands.DefaultHelpCommand):
    async def send_pages(self):
        destination = self.get_destination()
        e = discord.Embed(color=discord.Color.blurple(), description='')
        for page in self.paginator.pages:
            e.description += page
        await destination.send(embed=e)


class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.allowed_channels = ['bot-commands', 'staff-bot-commands']
        self.exempt_guild_id = 1230504895946166374
        self.error_log_channel_id = 1266060072820408513
    

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("Missing required argument.")
        elif isinstance(error, commands.CommandNotFound):
            await ctx.send("Command not found.")
        elif isinstance(error, commands.CheckFailure):
            await ctx.send("This command can only be used in designated bot channels.")
        else:
            channel = self.bot.get_channel(self.error_log_channel_id)
            embed = discord.Embed(color=discord.Colour.dark_red(), title=f"Command: {ctx.command} "
                                                                         f"\nArguments: {ctx.current_argument}")
            embed.add_field(name=f"{ctx.author.name}'s Exception", value=f"{error}", inline=False)
            embed.add_field(name=f"Information:", value=f"Guild: {ctx.guild}\n Channel:{ctx.channel} \n"
                                                        f" Link: {ctx.message.jump_url}", inline=False)
            await channel.send(embed=embed)
    
    @commands.Cog.listener()
    async def on_ready(self):
        print(f'Logged in as {self.bot.user}')

async def setup(bot):
    await bot.add_cog(Moderation(bot))