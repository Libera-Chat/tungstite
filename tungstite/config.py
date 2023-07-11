from dataclasses import dataclass
from os.path     import expanduser
from re          import compile as re_compile
from typing      import Any, List, Optional, Pattern, Set, Tuple

import yaml

@dataclass
class Config(object):
    server:   str
    nickname: str
    username: str
    realname: str
    password: str
    channels: List[str]
    sasl:     Tuple[str, str]
    oper:     Tuple[str, str, str]

    log_file: str
    log_line: str
    patterns: List[Pattern]
    froms:    Set[str]
    history:  int

def load(filepath: str):
    with open(filepath) as file:
        config_yaml = yaml.safe_load(file.read())

    nickname = config_yaml["nickname"]

    oper_name = config_yaml["oper"]["name"]
    oper_pass = config_yaml["oper"]["pass"]
    oper_file = expanduser(config_yaml["oper"]["file"])

    return Config(
        config_yaml["server"],
        nickname,
        config_yaml.get("username", nickname),
        config_yaml.get("realname", nickname),
        config_yaml["password"],
        config_yaml["channels"],
        (config_yaml["sasl"]["username"], config_yaml["sasl"]["password"]),
        (oper_name, oper_pass, oper_file),
        expanduser(config_yaml["log-file"]),
        config_yaml["log-line"],
        [re_compile(p) for p in config_yaml["patterns"]],
        set(config_yaml["froms"]),
        config_yaml["history"]
    )
