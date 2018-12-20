import getpass;
import logging
from pymongo import MongoClient
import base64

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
        self.logger_time = logging.getLogger("timer")

        ch = logging.FileHandler('boip.log')
        ch.setLevel(0)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - @%(message)s @')
        ch.setFormatter(formatter)
        self.level_log = 10
        self.logger.addHandler(ch)
        self.logger.setLevel(self.level_log)

        self.logger = logging.getLogger("Timer")

        ch2 = logging.FileHandler('timestamps.log')
        ch2.setLevel(0)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - @%(message)s @')
        ch2.setFormatter(formatter)
        self.level_time_log = 20
        self.logger_time.addHandler(ch2)
        self.logger_time.setLevel(self.level_time_log)


    def get_password(self):
        return self.password

    def get_username(self):
        return self.username

    def connect_mongo(self):
        client = MongoClient('mongodb://127.0.0.1:27017/')
        db_connection = client.claro
        return db_connection

    def logtime(self, level, time_start, time_end, originator, method):

        message = "Method: {0} Start: {1} End {2} Duration {3}".format(str(method.__name__), str(time_start)
                                                                       , str(time_end),
                                                                       str((time_end - time_start) * 1000))

        self.logger_time.log(level=level,
                             msg=" usr " + self.username + " class " + str(type(originator).__name__) + " " + str(
                                 message))
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

    @staticmethod
    def encode(key, clear):
        enc = []
        for i in range(len(clear)):
            key_c = key[i % len(key)]
            enc_c = chr((ord(clear[i]) + ord(key_c)) % 256)
            enc.append(enc_c)
        return base64.urlsafe_b64encode("".join(enc).encode()).decode()

    @staticmethod
    def decode(key, enc):
        dec = []
        enc = base64.urlsafe_b64decode(enc).decode()
        for i in range(len(enc)):
            key_c = key[i % len(key)]
            dec_c = chr((256 + ord(enc[i]) - ord(key_c)) % 256)
            dec.append(dec_c)
        return "".join(dec)
