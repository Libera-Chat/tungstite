import asyncio, time, traceback
from collections import OrderedDict
from datetime    import datetime
from typing      import Dict, Optional
from typing      import OrderedDict as TOrderedDict

from irctokens import build, Line
from ircrobots import Capability
from ircrobots import Bot as BaseBot
from ircrobots import Server as BaseServer

from ircchallenge       import Challenge
from ircstates.numerics import *
from ircrobots.matching import Response, SELF, ANY

from .common import EmailInfo, LimitedOrderedDict, human_duration
from .config import Config

CAP_OPER = Capability(None, "solanum.chat/oper")

# not in ircstates yet...
RPL_RSACHALLENGE2      = "740"
RPL_ENDOFRSACHALLENGE2 = "741"
RPL_YOUREOPER          = "381"

class Server(BaseServer):
    def __init__(self,
            bot:    BaseBot,
            name:   str,
            config: Config):

        self._config = config
        self._email_queue: TOrderedDict[str, EmailInfo] = \
            LimitedOrderedDict(8)
        self._emails:      TOrderedDict[str, EmailInfo] = \
            LimitedOrderedDict(config.history)

        super().__init__(bot, name)
        self.desired_caps.add(CAP_OPER)

    def set_throttle(self, rate: int, time: float):
        # turn off throttling
        pass

    async def _oper_challenge(self,
            oper_name: str,
            oper_pass: str,
            oper_file: str):

        try:
            challenge = Challenge(keyfile=oper_file, password=oper_pass)
        except Exception:
            traceback.print_exc()
        else:
            await self.send(build("CHALLENGE", [oper_name]))
            challenge_text = Response(RPL_RSACHALLENGE2,      [SELF, ANY])
            challenge_stop = Response(RPL_ENDOFRSACHALLENGE2, [SELF])
            #:lithium.libera.chat 740 sandcat :foobarbazmeow
            #:lithium.libera.chat 741 sandcat :End of CHALLENGE

            while True:
                challenge_line = await self.wait_for({
                    challenge_text, challenge_stop
                })
                if challenge_line.command == RPL_RSACHALLENGE2:
                    challenge.push(challenge_line.params[1])
                else:
                    retort = challenge.finalise()
                    await self.send(build("CHALLENGE", [f"+{retort}"]))
                    break

    async def log_read_line(self, line: str):
        now = int(time.time())
        for pattern in self._config.patterns:
            if match := pattern.search(line):
                groups = dict(match.groupdict())

                if "id" in groups:
                    id = groups["id"]
                    if not id in self._email_queue:
                        self._email_queue[id] = EmailInfo(now)
                    info = self._email_queue[id]
                else:
                    info = EmailInfo(now)

                if "to" in groups:
                    info.to     = groups["to"]
                if "from" in groups:
                    info._from  = groups["from"]
                if "status" in groups:
                    info.status = groups["status"]
                if "reason" in groups:
                    info.reason = groups["reason"]

                if (info.finalised() and
                        info._from in self._config.froms):

                    self._emails[info.to.lower()] = info
                    log = self._config.log_line.format(**{
                        "email":  info.to,
                        "status": info.status,
                        "reason": info.reason
                    })
                    await self.send_raw(log)

    async def line_read(self, line: Line):
        if line.command == RPL_WELCOME:
            await self.send(build("MODE", [self.nickname, "+g"]))
            oper_name, oper_pass, oper_file = self._config.oper
            await self._oper_challenge(oper_name, oper_pass, oper_file)

        elif line.command == RPL_YOUREOPER:
            # we never want snotes
            await self.send(build("MODE", [self.nickname, "-s"]))

        elif (line.command == "PRIVMSG" and
                line.source is not None and
                not self.is_me(line.hostmask.nickname)):

            target  = line.params[0]
            message = line.params[1]

            if self.is_me(target):
                # a private message
                cmd, _, args = message.partition(" ")
                await self.cmd(
                    line.hostmask.nickname,
                    self.nickname,
                    cmd.lower(),
                    args,
                    line.tags
                )
            elif (self.is_channel(target) and
                    line.params[1].startswith("!")):
                # a channel command
                # [1:] to cut off !
                cmd, _, args = message[1:].partition(" ")
                await self.cmd(
                    line.hostmask.nickname,
                    target,
                    cmd.lower(),
                    args,
                    line.tags
                )

    async def cmd(self,
            who:     str,
            target:  str,
            command: str,
            args:    str,
            tags:    Optional[Dict[str, str]]):

        if tags and "solanum.chat/oper" in tags:
            attrib  = f"cmd_{command}"
            if hasattr(self, attrib):
                outs = await getattr(self, attrib)(who, args)
                for out in outs:
                    await self.send(build("NOTICE", [target, out]))

    async def cmd_emailstate(self,
            nick:  str,
            sargs: str):

        args = sargs.split(None, 1)
        if args:
            email = args[0]
            key   = email.lower()
            if key in self._emails:
                info  = self._emails[key]
                ts    = datetime.utcfromtimestamp(info.ts).isoformat()
                since = human_duration(int(time.time()-info.ts))

                return [
                    f"{ts} ({since} ago)"
                    f" {info.to} is \x02{info.status}\x02: {info.reason}"
                ]
            else:
                return [f"I don't have {email} in my history"]
        else:
            return ["Please provide an email address"]

    def line_preread(self, line: Line):
        print(f"< {line.format()}")
    def line_presend(self, line: Line):
        print(f"> {line.format()}")

class Bot(BaseBot):
    def __init__(self, config: Config):
        super().__init__()
        self._config = config

    def create_server(self, name: str):
        return Server(self, name, self._config)

