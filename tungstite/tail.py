import asyncio, os
from collections import OrderedDict
from typing      import AsyncIterator, cast, List, Optional, Pattern
from typing      import OrderedDict as TOrderedDict

import aiofiles
from .       import Bot, Server
from .common import EmailInfo, LimitedOrderedDict

async def tail_log_file(
        bot:      Bot,
        filename: str,
        patterns: List[Pattern]
        ):

    seek = True
    while True:
        file  = await aiofiles.open(filename, "r")
        inode = os.stat(file.fileno()).st_ino
        if seek:
            seek = False
            while await file.read():
                pass

        while True:
            line = await file.readline()
            if not line == "":
                servers = list(bot.servers.values())
                if servers:
                    server = cast(Server, servers[0])
                    await server.log_read_line(line)
            else:
                await asyncio.sleep(0.1)

            if not os.path.isfile(filename):
                # we've been rotated, but no new file yet
                while not os.path.isfile(filename):
                    await asyncio.sleep(0.1)
                break
            elif not inode == os.stat(filename).st_ino:
                # we've been rotated and there's a new file
                break

        await file.close()
