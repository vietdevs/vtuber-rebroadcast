import requests
import LiveStreams
import APIKey
from time import sleep
import logging
import sys
import asyncio
import aioconsole


async def mainConsole(manager):
    stdin, stdout = await aioconsole.get_standard_streams()
    while True:
        await asyncio.sleep(0.1)
        byte = await stdin.readline()
        cmd = byte.decode().strip('\n').split(" ")
        if cmd[0] == '':
            continue
        elif cmd[0] == 'add':
            manager.Add(cmd[1], cmd[2])
        elif cmd[0] == 'del':
            manager.Del(cmd[1])
        elif cmd[0] == 'quit' or cmd[0] == 'exit' or cmd[0] == 'q':
            sys.exit()
        else:
            print('未知的控制台命令')

if __name__ == "__main__":
    logging.basicConfig(
        format='%(asctime)s[%(levelname)s]%(threadName)s>%(message)s', level=logging.DEBUG)
    logging.info('eventloop已启动')
    manager = LiveStreams.StreamerManager()
    asyncio.ensure_future(manager.run())
    asyncio.ensure_future(mainConsole(manager))
    asyncio.get_event_loop().run_forever()
