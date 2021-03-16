from riotwatcher import LolWatcher
import pandas as pd
import requests
import datetime
#GLOBALS
#---------------------------------------------------------#

pd.set_option("display.max_rows", None,"display.max_columns", 500, "expand_frame_repr", True, "html.table_schema", True)
api_key = 'RIOT API KEY HERE'
lol_watcher = LolWatcher(api_key)
my_region = 'euw1'

version = requests.get('https://ddragon.leagueoflegends.com/api/versions.json').json()[0]
datadragon = lol_watcher.data_dragon.champions(version, False, None)
champions = {}
for champion in datadragon["data"]:
    key = int(datadragon["data"][champion]["key"])
    champions[key] = champion

#---------------------------------------------------------#

#FUNCTIONS
#---------------------------------------------------------#


def switch(queue):
    switcher = {
        'blind': 430,
        'draft': 400,
        'solo': 420,
        'flex': 440,
        'aram': 450
    }
    return switcher.get(queue, 0)


def switchv2(queue):
    switcher = {
        430: 'blind',
        400: 'draft',
        420: 'solo',
        440: 'flex',
        450: 'aram'
    }
    return switcher.get(queue, 0)

def championId_to_name(id: int):
    return champions[id]


def championName_to_Id(championname: str):
    champId = list(champions.keys())[list(champions.values()).index(championname)]
    return champId


def get_ranked_stats(id: int):
    my_ranked_stats = lol_watcher.league.by_summoner(my_region, id)
    rankedstats = my_ranked_stats[0]
    return rankedstats


def get_sumdetails(sumname: str):
    response = lol_watcher.summoner.by_name(my_region, sumname)
    return response


def getSummonerId(sumname: str):
    response = lol_watcher.summoner.by_name(my_region, sumname)
    return response['accountId']


def print_sumdetails(sumname: str):
    response = lol_watcher.summoner.by_name(my_region, sumname)
    rankedstats=get_ranked_stats(response['id'])
    stats = sumname +" "+str(rankedstats['tier'])+" "+ str(rankedstats['rank']) + " "+str(rankedstats['wins'])+" wins/ "+ str(rankedstats['losses'])+" losses"
    return stats


def winrate(winloss: list):
    return winloss[0] / (winloss[0] + winloss[1]) * 100


def get_Match_List_Champ(sumname: str, queue: int, champion: int):
    summonerId = getSummonerId(sumname)
    summonermatches = lol_watcher.match.matchlist_by_account(my_region, summonerId, {str(queue)}, None, None, None, 50,
                                                             {13}, {champion})
    return summonermatches


def get_Match_list(sumname: str):
    summonerId = getSummonerId(sumname)
    summonermatches = lol_watcher.match.matchlist_by_account(my_region, summonerId, None, None, None, None, 10,
                                                            {13}, None)
    matchhistory = []
    for match in summonermatches['matches']:
        champion = championId_to_name(match['champion'])
        gameId = match['gameId']
        matchInfo = lol_watcher.match.by_id(my_region, gameId)
        #print(matchInfo['participants'])
        # Find participant ID
        participantId = 0
        for player in matchInfo['participantIdentities']:
            if player['player']['summonerName'] == sumname:
                participantId = player['participantId']
                # Use participant ID to determine which team player is on
        #print(matchInfo['participants'][participantId-1]['stats'])
        playerstat = matchInfo['participants'][participantId-1]['stats']
        if playerstat['win']:
            winlose = 'Victory'
        else:
            winlose = 'Defeat'
        queue = switchv2(matchInfo['queueId'])
        gametime = str(datetime.timedelta(seconds=matchInfo['gameDuration']))
        kda = str(playerstat['kills'])+'/'+str(playerstat['deaths'])+'/'+str(playerstat['assists'])
        mh = {}
        mh['champion'] = champion
        mh['queue'] = queue
        mh['win']= winlose
        mh['kda'] = kda
        mh['tDamage'] = str(playerstat['totalDamageDealt'])
        mh['gameTime'] = gametime

        matchhistory.append(mh)
    Stats = pd.DataFrame(matchhistory)
    return Stats


def displayWinrates(matchList: dict, sumname: str):
    win_loss = [0, 0]
    champion_winrates = {}
    counter = 0
    kills = 0
    deaths = 0
    assists = 0
    # Parse through matchlist
    for match in matchList['matches']:
        champion = championId_to_name(match['champion'])
        gameId = match['gameId']
        # Access match data
        matchInfo = lol_watcher.match.by_id(my_region, gameId)
        if matchInfo['gameDuration'] > 270:
            # Find participant ID
            participantId = 0
            for player in matchInfo['participantIdentities']:
                if player['player']['summonerName'] == sumname:
                    participantId = player['participantId']

            # Use participant ID to determine which team player is on
            if participantId <= 5:
                tparticipantId = 0
            else:
                tparticipantId = 1

            # Increments win/loss counters for overall and per champion
            if matchInfo['teams'][tparticipantId]['win'] == 'Win':
                win_loss[0] += 1
                if champion in champion_winrates:
                    champion_winrates[champion][0] += 1
                else:
                    champion_winrates[champion] = [1, 0, 0]
            else:
                win_loss[1] += 1
                if champion in champion_winrates:
                    champion_winrates[champion][1] += 1
                else:
                    champion_winrates[champion] = [0, 1, 0]
            champion_winrates[champion][2] += 1
            playerstat = matchInfo['participants'][participantId - 1]['stats']
            counter += 1
            kills += playerstat['kills']
            deaths += playerstat['deaths']
            assists += playerstat['assists']

    # Sort champions in descending order of games
    kda = str(round(kills/counter, 2)) + '/' + str(round(deaths/counter, 2)) + '/' + str(round(assists/counter, 2))
    champion_winrates = dict(sorted(champion_winrates.items(), reverse=True, key=lambda x: x[1][2]))
    champion_list = []
    champion_winrates_list = []

    for champion in champion_winrates:
        # returns champion winrates and checks for plural games
        percentage = '%.2f' % (winrate(champion_winrates[champion]))
        games = champion_winrates[champion][2]

        champion_list.append(champion)
        champion_winrates_list.append(float(percentage))
        result = str(champion)+" "+ kda +" "+ str(percentage) + '% '+ str(games)
        if games == 1:
            result += ' game'
        else:
            result += ' games'
    return result