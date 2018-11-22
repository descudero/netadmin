import getpass;
import logging
from pymongo import MongoClient

import ast
import time


class Master:

    def __init__(self, AdebugLevel=0, password="", username="", logg_name="master"):

        self.communities = ["snmpUfi", "pnrw-med", "uFi08NeT", "pnrw-all"]

        if password != "" and username != "":
            self.username = username
            self.password = password
        else:
            self.username = getpass._raw_input(prompt='username ')
            self.password = getpass.getpass(prompt='password ')
        self.debug = AdebugLevel
        self.dbname = "boip.db"
        self.logger = logging.getLogger(logg_name)

        ch = logging.FileHandler('boip.log')
        ch.setLevel(0)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - @%(message)s @')
        ch.setFormatter(formatter)
        self.level_log = 10
        self.logger.addHandler(ch)
        self.logger.setLevel(self.level_log)

    def get_password(self):
        return self.password

    def get_username(self):
        return self.username

    def connect_mongo(self):
        client = MongoClient('mongodb://127.0.0.1:27017/')
        db_connection = client.claro
        return db_connection

    def log(self, level, message, originator):
        '''
        logs level
        CRITICAL	50
        ERROR	40
        WARNING	30
        INFO	20
        DEBUG	10
        NOTSET	0
        '''
        self.logger.log(level=level,
                        msg=" usr " + self.username + " class " + str(type(originator).__name__) + " " + str(message))
