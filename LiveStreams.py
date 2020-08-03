import logging
import sys
from time import sleep
import datetime
import requests
import main
import youtube_util
import APIKey
import asyncio
import Rebroadcast
import queue
import Discord


class StreamerManager:
    discord = None
    streamers = {}

    def __init__(self, discord=None):
        self.discord = discord

    def Add(self, name, channelId):
        for streamername, streamer in list(self.streamers.items()):
            if streamer.channelId == channelId or streamername == name:
                print(f'已经添加过了[{name}]{streamer.channelId}')
                return f'已经添加过了[{name}]{streamer.channelId}'
        self.streamers[name] = Streamer(name, channelId, self.discord)
        print('成功添加:['+name+']'+channelId)
        return '成功添加:['+name+']'+channelId

    def Del(self, string):
        for name, streamer in list(self.streamers.items()):
            if streamer.channelId == string or name == string:
                streamer.cancel()
                self.streamers.pop(name)
                print('成功删除'+string)
                return '成功删除'+string
        print('找不到'+string)
        return '找不到'+string

    def List(self):
        tmp = []
        for name, streamer in list(self.streamers.items()):
            tmp.append(str(streamer))
        if tmp==[]:
            print('当前的监控列表\n没有正在监控的vtb')
            return '当前的监控列表\n没有正在监控的vtb'
        print('当前的监控列表\n'+'\n'.join(tmp))
        return '当前的监控列表\n'+'\n'.join(tmp)


class Streamer:
    state = None
    rbcThread = None
    queue = None
    discord = None

    def __init__(self, name, channelId, discord=None):
        self.name = name
        self.channelId = channelId
        self.task = asyncio.ensure_future(self.autocheck())
        self.discord = discord

    def __str__(self):
        return f'[{self.name}]{self.channelId}:{self.getState()}'

    def __repr__(self):
        return (self.name, self.channelId)

    def cancel(self):
        self.task.cancel()

    async def check(self):
        # logging.debug('直播状态检测:'+self.name)
        state = await youtube_util.getLiveVideoId(self.channelId)
        # logging.debug(f'直播状态:[{self.name}]{state}')
        return state

    async def autocheck(self):
        while True:
            state = await self.check()
            logging.debug(f'直播状态:{state}原状态:{self.state}')
            if state != self.state:
                await self.changeRebroadcast(state)
                self.state = state
            await asyncio.sleep(15)

    async def changeRebroadcast(self, state):
        logging.debug(f'改变转播状态:[{self.name}]{state}')
        if not state is None:  # 正在直播中
            self.startRebroadcast()
            await self.sendMessage(
                f'{self.name}{self.getState("detail")}')
        else:  # 不在直播中
            self.stopRebroadcast()
            await self.sendMessage(f'{self.name}直播已结束')

    def startRebroadcast(self):
        if not self.rbcThread is None:
            self.queue.put('stop')
            self.rbcThread = None
            self.queue = None
        self.queue = queue.Queue()
        self.queue.put((self.name, state))
        self.rbcThread = Rebroadcast.RebroadcastThread(self.queue)
        self.rbcThread.start()

    def stopRebroadcast(self):
        if not self.rbcThread is None:
            self.queue.put('stop')
            self.rbcThread = None
            self.queue = None

    def getState(self, type='simple'):
        if type == 'simple':
            if self.state is None:
                return '未直播'
            else:
                return '正在直播中:{state}'
        elif type == 'detail':
            if self.state is None:
                return '未直播'
            else:
                return '正在直播中:https://www.youtube.com/watch?v={state}\n转播链接:https://live.acedroidx.top/?stream={self.name}'

    async def sendMessage(self, msg):
        if self.discord is None:
            logging.warning('Streamer.discord is None')
            return
        await self.discord.send_message(msg)
