import asyncio
from argparse import ArgumentParser

from ircrobots import ConnectionParams, SASLUserPass

from .       import Bot
from .config import Config, load as config_load
from .tail   import tail_log_file

async def main(config: Config):
    bot = Bot(config)

    sasl_user, sasl_pass = config.sasl

    params = ConnectionParams.from_hoststring(config.nickname, config.server)
    params.realname = config.realname
    params.password = config.password
    params.sasl = SASLUserPass(sasl_user, sasl_pass)
    params.autojoin = config.channels

    await bot.add_server("irc", params)
    await asyncio.wait([
        asyncio.create_task(tail_log_file(bot, config.log_file, config.patterns)),
        asyncio.create_task(bot.run())
    ])

if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("config")
    args   = parser.parse_args()

    config = config_load(args.config)
    asyncio.run(main(config))
