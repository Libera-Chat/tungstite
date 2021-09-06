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
                for pattern in patterns:
                    if match := pattern.search(line):
                        groups = dict(match.groupdict())

                        if "id" in groups:
                            id = groups["id"]
                            if not id in queue:
                                queue[id] = EmailInfo()
                            info = queue[id]
                        else:
                            info = EmailInfo()

                        if "to" in groups:
                            info.to     = groups["to"]
                        if "from" in groups:
                            info._from  = groups["from"]
                        if "status" in groups:
                            info.status = groups["status"]
                        if "reason" in groups:
                            info.reason = groups["reason"]

                        if (info.to is not None and
                                info._from  is not None and
                                info.status is not None and
                                info.reason is not None):

                            servers = list(bot.servers.values())
                            if servers:
                                await servers[0].email_sent(info)

                        break
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
