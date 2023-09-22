import pandas as pd
from datetime import datetime, timedelta
import logging
from pathlib import Path
from passlib.context import CryptContext

crypto_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

config = {}

config["general_meta"] = {
    "name": "Transportation_tenant",
    "description": (
            "This tenant handles requests concerning the transportation of "
            "physical objects."
        )
}

config["ServerConfig"] = {
    "host": "<host IP FINALES>",
    "port": "<port FINALES>"
}

config["end_run_time"] = datetime(year="<year>", month="<month>", day="<day>", hour="<hour>", minute="<minute>", second="<second>")

config["operators"] = [
    {
        "username": "<user name first operator FINALES>",
        "password": "<password first operator FINALES>",
        "usergroups": ["<user groups first operator FINALES>"],
    }
]

config["tenant_user"] = {
    "username": "<user name tenant FINALES>",
    "password": "<password tenant FINALES>",
    "usergroups": ["<user groups tenant FINALES>"],
}

config["chat_server"] = {
    "host": "<host IP chat server NOT FINALES>",
    "port": "<port chat server NOT FINALES>",
    "password": crypto_context.hash(""),
    "encoding": "utf-8",
    "timestamp_layout": "%d_%m_%Y-%H_%M_%S"
}

config["logging"] = {
    "baseConfig": {
        "level": logging.INFO,
        "format": "%(asctime)s - %(levelname)s -%(name)s \n \t %(message)s \n",
        "filename": str(Path(__file__).parent.joinpath("logs", "logFile.log")),
        "encoding": "utf-8",
        "force": True  # https://stackoverflow.com/questions/12158048/changing-loggings-basicconfig-which-is-already-set
    }
}