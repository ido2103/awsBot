import discord
from discord.ext import commands
import json

class Misc(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def ping(self, ctx):
        """Responds with Pong! and the latency."""
        latency = round(self.bot.latency * 1000)  # Convert latency to milliseconds
        await ctx.send(f'Pong! {latency}ms')

    @commands.command()
    async def stats(self, ctx):
        """Shows the stats of the user."""
        with open("stats.json", "r") as file:
            json_file = json.load(file)
        num_correct = 0
        num_incorrect = 0
        percentage = 0
        for index, user in enumerate(json_file):
            if user["user"] == ctx.author.name:
                num_correct = json_file[index]["correct"]
                num_incorrect = json_file[index]["incorrect"]
                if num_incorrect != 0:
                    percentage = num_correct / (num_correct + num_incorrect) * 100
                    percentage = round(percentage, 2)
                else:
                    percentage = 0
        embed = discord.Embed(colour=3, title=f"{ctx.author}'s stats")
        embed.add_field(name=f"Correct", value=num_correct, inline=False)
        embed.add_field(name=f"Incorrect", value=num_incorrect, inline=False)
        embed.add_field(name=f"Percentage", value=percentage, inline=False)
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Misc(bot))
