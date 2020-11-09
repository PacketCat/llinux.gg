from lcu_driver import Connector
from pypresence import Presence
import time
import asyncio
import requests as r
import json

names = {'modename': '','phase': '', 'detailsname': '', 'starttime': 0, 'endtime': 0,
         'summonerscount': 0, 'maxsummoners': 0, 'champname': '', 'champlocale': '', 'lastphase': '', 'modeicon': ''}

def ignore(e, a):
    print(e)

loop = asyncio.get_event_loop()
connector = Connector(loop=loop)
rpc = Presence("769987445143240715", loop=loop)
rpc.connect()


@connector.ready
async def started(connection):
    print("Connected")
    print('henlo')
    print(rpc.update(state='League of Legends', large_image='chromiumclient'))
    
@connector.close
async def league_closed(connection):
    print("League closed")
    rpc.clear()
    await connector.close()

@connector.ws.register("/lol-lobby/v2/lobby", event_types=('UPDATE', 'DELETE'))
async def lobby_update(connection, event):
    if event.type == 'Update':
        names['summonerscount'] = len(event.data['members'])
        names['maxsummoners'] = event.data['gameConfig']['maxLobbySize']
        rpc.update(details='LoL - {}({})'.format(names['modename'], names['detailsname']), state = 'Lobby [{}/{}]'.format(names['summonerscount'], names['maxsummoners']))
    elif event.type == 'Delete':
        names['summonerscount'] = 0
        names['maxsummoners'] = 0
        
@connector.ws.register('/lol-champ-select/v1/current-champion', event_types=('UPDATE','CREATE'))
async def select_champion(con, event):
    ans = r.get('http://ddragon.leagueoflegends.com/cdn/10.1.1/data/ru_RU/champion.json')
    ans.json = ans.json()
    for i in ans.json['data'].keys():
        print(i, ans.json['data'][i]['key'], event.data, int(ans.json['data'][i]['key']) == int(event.data))
        if int(ans.json['data'][i]['key']) == int(event.data):
            names['champname'] = i.lower()
            names['champlocale'] = ans.json['data'][i]['name']
            print(names, ans.json['data'][i]['name'], i.lower())
            return
            
        
@connector.ws.register('/lol-lobby/v2/lobby/matchmaking/search-state', event_types=('UPDATE',))
async def searchstate(connection, event):
    if event.data['searchState'] == 'Searching':
        names['starttime'] = time.time()
        names['endtime'] = None
    elif event.data['searchState'] == 'Invalid':
        names['endtime'] = 0
        names['starttime'] = None
    elif event.data['searchState'] == 'Found':
        names['endtime'] = time.time()
        
@connector.ws.register('/lol-gameflow/v1/session', event_types= ('CREATE', 'UPDATE', 'DELETE'))
async def gstart(connection, event):
    names['modename'] = event.data['map']['gameModeName']
    names['phase'] = event.data['phase']
    names['detailsname'] = event.data['gameData']['queue']['description']
    
    if event.data['gameData']['queue']['gameMode'] == 'CLASSIC':
        names['modeicon'] = '5v5'
    elif event.data['gameData']['queue']['gameMode'] == 'ARAM':
        names['modeicon'] = 'aram'
    else:
        names['modeicon'] = 'special'
    
    print(event.data['phase'])
    
    
    if event.data['phase'] == 'Lobby':
        rpc.update(details='LoL - {}({})'.format(names['modename'], names['detailsname']), state = 'Lobby [{}/{}]'.format(names['summonerscount'], names['maxsummoners']))
    elif event.data['phase'] == 'Matchmaking':
        rpc.update(details = 
                   'LoL - {}({})'.format(names['modename'], names['detailsname']), state = 'Matchmaking', start=names['starttime'], end=names['endtime'])
    elif event.data['phase'] == 'ChampSelect':
        if names['lastphase'] == 'ChampSelect':
            return
        rpc.update(details = 'LoL - {}({})'.format(names['modename'], names['detailsname']), state = 'Champion Selection')
    elif event.data['phase'] == 'GameStart':
        names['startg'] = time.time()
        print(rpc.update(details = 'LoL - {}({})'.format(names['modename'], names['detailsname']), state = "In progress", start = time.time(), large_image=names['champname'], large_text=names['champlocale'], small_image=names['modeicon'], small_text=names['modeicon']))
    elif event.data['phase'] == 'None':
        print(rpc.update(state='League of Legends', large_image='chromiumclient'))
    elif event.data['phase'] == 'EndOfGame':
        print(rpc.update(details = 'LoL - {}({})'.format(names['modename'], names['detailsname']), state = "EOG - ", start=names['startg'], end=time.time(), large_image=names['champname'], large_text=names['champlocale'], small_image=names['modeicon'], small_text=names['modeicon']))
        
        
while True:
    try:
        print('Connecting...')
        connector.start()
    except:
        print("Connection failed, reconnect in 30 seconds")
        rpc.clear()
        time.sleep(30)
