import asyncio, os
from collections import OrderedDict
from typing      import AsyncIterator, List, Optional, Pattern
from typing      import OrderedDict as TOrderedDict

import aiofiles
from .       import Bot
from .common import EmailInfo, LimitedOrderedDict

async def tail_log_file(
        bot:      Bot,
        filename: str,
        patterns: List[Pattern]
        ):

    queue: TOrderedDict[str, EmailInfo] = LimitedOrderedDict(max=8)

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
            if line is not None:
                servers = list(bot.servers.values())
                if servers:
                    await servers[0].log_read_line(line)
            else:
                asyncio.sleep(0.1)

            if not os.path.isfile(filename):
                # we've been rotated, but no new file yet
                while not os.path.isfile(filename):
                    await asyncio.sleep(0.1)
                break
            elif not inode == os.stat(filename).st_ino:
                # we've been rotated and there's a new file
                break

        await file.close()
