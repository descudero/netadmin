import getpass;


class Master:
    def __init__(self, AdebugLevel=0):
        self.username = getpass._raw_input(prompt='username ')
        self.password = getpass._raw_input(prompt='contrasena ')
        self.debug = AdebugLevel

    def getPassword(self):
        return self.password

    def getUsername(self):
        return self.username
