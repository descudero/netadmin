from config.Master import Master
from itsdangerous import (TimedJSONWebSignatureSerializer
                          as Serializer, BadSignature, SignatureExpired)


class UserApp():
    def __init__(self, master, app):
        self.master = master
        self.app = app
        self.username = 0
        self.id = 0
        self.hash = "na"

    __tablename__ = 'users'

    def hash_password(self, password):
        self.password_hash = Master.encode(password)

    def verify_password(self, password):

        return Master.decode(password, self.password_hash)

    def generate_auth_token(self, expiration=600):
        s = Serializer(self.app.config['SECRET_KEY'], expires_in=expiration)
        return s.dumps({'id': self.id})

    def save(self):
        connection = self.master.db_connect()
        with connection.cursor() as cursor:
            sql = f'''INSERT INTO {UserApp.__tablename__}(username,password_hash) \
                VALUES('{self.username}','{self.password_hash}')
                '''
            result = cursor.execute(sql)
            connection.commit()
            self.uid = cursor.lastrowid

    @staticmethod
    def verify_auth_token(token, app):
        s = Serializer(app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except SignatureExpired:
            return None  # valid token, but expired
        except BadSignature:
            return None  # invalid token
        user = UserApp.query.get(data['id'])
        return user

    @staticmethod
    def query(uid, master, app):
        connection = master.db_connect()
        with connection.cursor() as cursor:
            sql = f'''SELECT * from users WHERE uid='{uid}'; '''
            data = cursor.fetchone(sql)
            user = UserApp(app=app, master=master)
            if data:
                user.id = data['uid']
                user.username = data['username']
                user.password_hash = data['password_hash']
