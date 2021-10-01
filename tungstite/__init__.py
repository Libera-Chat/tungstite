import asyncio, time, traceback
from datetime    import datetime
from typing      import cast, Dict, Iterable, List, Optional, Tuple
from uuid        import uuid4

from irctokens import build, Line
from ircrobots import Capability
from ircrobots import Bot as BaseBot
from ircrobots import Server as BaseServer

from ircchallenge       import Challenge
from ircstates.numerics import *
from ircrobots.matching import Response, SELF, ANY

from .common import EmailInfo, human_duration, LimitedList, LimitedOrderedDict
from .config import Config

CAP_OPER = Capability(None, "solanum.chat/oper")

# not in ircstates yet...
RPL_RSACHALLENGE2      = "740"
RPL_ENDOFRSACHALLENGE2 = "741"
RPL_YOUREOPER          = "381"

STATUS_CACHE: Dict[str, str] = {}

class Server(BaseServer):
    def __init__(self,
            bot:    BaseBot,
            name:   str,
            config: Config):

        self._config = config

        self._emails_incomplete: LimitedOrderedDict[str, EmailInfo] = \
            LimitedOrderedDict(8)

        self._emails_complete:   LimitedList[Tuple[str, EmailInfo]] = \
            LimitedList(config.history)

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

    async def _print_log(self, info: EmailInfo):
        log = self._config.log_line.format(**{
            "email":  info.to,
            "status": info.status,
            "reason": info.reason
        })
        await self.send_raw(log)

    async def log_read_line(self, line: str):
        now = int(time.time())
        for pattern in self._config.patterns:
            if match := pattern.search(line):
                groups = dict(match.groupdict())

                id = groups.get("id", str(uuid4()))
                if not id in self._emails_incomplete:
                    self._emails_incomplete[id] = EmailInfo(id, now)
                info = self._emails_incomplete[id]

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

                    del self._emails_incomplete[id]

                    # only log when a queued email's status changes
                    status = cast(str, info.status)
                    if (id not in STATUS_CACHE or
                            not STATUS_CACHE[id] == status):
                        STATUS_CACHE[id] = status
                        await self._print_log(info)

                    cache_key = cast(str, info.to).lower()
                    self._emails_complete.add((cache_key, info))

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
                    line.hostmask.nickname,
                    cmd.lower(),
                    args,
                    line.tags
                )
            elif (self.is_channel(target) and
                    message.startswith("!")):
                # a channel command
                # [1:] to cut off "!"
                cmd, _, args = message[1:].partition(" ")
                await self.cmd(
                    line.hostmask.nickname,
                    target,
                    cmd.lower(),
                    args,
                    line.tags
                )

            elif (self.is_channel(target) and
                    len(parts := message.split(None, 1)) > 1):

                nick  = self.nickname_lower
                pings = {f"{nick}{c}" for c in [":", "," ""]}
                if self.casefold(parts[0]) in pings:
                    # a channel highlight command
                    cmd, _, args = parts[1].partition(" ")
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
            email      = args[0]
            search_key = email.lower()

            outs: List[str] = []
            for cache_key, info in self._emails_complete:
                if cache_key == search_key:
                    ts    = datetime.utcfromtimestamp(info.ts).isoformat()
                    since = human_duration(int(time.time()-info.ts))
                    outs.append(
                        f"{ts} ({since} ago)"
                        f" {info.to} is \x02{info.status}\x02:"
                        f" {info.reason}"
                    )

            # [:3] so we show, at max, the 3 most recent states
            return outs[:3] or [f"I don't have {email} in my history"]
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

