from passlib.context import CryptContext
from pathlib import Path
import logging

crypto_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


config = {}

config["chat_server"] = {
    "host": "<host IP chat server NOT FINALES>",
    "port": "<port chat server NOT FINALES>",
    "password": "<password chat server NOT FINALES>",
    "encoding": "utf-8"
}

config["name"] = "<name chat server NOT FINALES>"

config["logging"] = {
    "baseConfig": {
        "level": logging.INFO,
        "format": "%(asctime)s - %(levelname)s -%(name)s \n \t %(message)s \n",
        "filename": str(Path(__file__).parent.joinpath("logs", "logFile.log")),
        "encoding": "utf-8",
        "force": True  # https://stackoverflow.com/questions/12158048/changing-loggings-basicconfig-which-is-already-set
    }
}