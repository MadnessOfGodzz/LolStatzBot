import discord
import leagueAPI_requests as api
client = discord.Client()

from discord.ext import commands
from dotenv import load_dotenv

bot = commands.Bot(command_prefix='%')


@bot.command(name='ac', help='%ac <summonername>  |shows account details')
async def accountdetails(ctx, sumname):
    ac = api.print_sumdetails(sumname)
    await ctx.send("```"+ ac+ "```")


@bot.command(name='st', help='%st <summonername> <championname> <queuetype>  |shows stats on champ per queuetype. '
                             'queuetypes: blind, draft, solo, flex, aram')
async def champwinrate(ctx, sumname, championname, queue):
    queuecode = api.switch(queue)
    champion = api.championName_to_Id(championname)
    wr = api.displayWinrates(api.get_Match_List_Champ(sumname, queuecode, champion), sumname)
    await ctx.send("```"+wr+"```")


@bot.command(name='mh', help='%mh <summonername>  |shows matchhistory of past 10 games')
async def matchhistory(ctx, sumname):
    mh = api.get_Match_list(sumname)
    print(mh)
    await ctx.send(mh)

bot.run('DISCORD KEY HERE')
