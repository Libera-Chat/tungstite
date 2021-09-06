import asyncio
from argparse import ArgumentParser

from ircrobots import ConnectionParams, SASLUserPass

from .       import Bot
from .config import Config, load as config_load
from .tail   import tail_log_file

async def main(config: Config):
    bot = Bot(config)

    host, port, tls      = config.server
    sasl_user, sasl_pass = config.sasl

    params = ConnectionParams(
        config.nickname,
        host,
        port,
        tls,
        username=config.username,
        realname=config.realname,
        password=config.password,
        sasl=SASLUserPass(sasl_user, sasl_pass),
        autojoin=config.channels
    )
    await bot.add_server(host, params)
    await asyncio.wait([
        tail_log_file(bot, config.log_file, config.patterns),
        bot.run()
    ])

if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("config")
    args   = parser.parse_args()

    config = config_load(args.config)
    asyncio.run(main(config))
