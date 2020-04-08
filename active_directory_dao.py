import os
from ldap3 import Server, Connection, ALL, ALL_ATTRIBUTES

AD_DOMAIN = os.environ["AD_DOMAIN"]
AD_HOST = os.environ["AD_HOST"]
AD_PORT = os.environ["AD_PORT"]

class ActiveDirectoryDAO:
    def __init__(self):
        pass

    def bind_user(self, username, password):
        s = Server(host=AD_HOST, port=int(AD_PORT), use_ssl=True, get_info="ALL")
        c = Connection(
            s,
            user=f"{username}@{AD_DOMAIN}",
            password=password,
            auto_bind=True,
            version=3,
            authentication='SIMPLE',
            client_strategy='SYNC',
            auto_referrals=True,
            check_names=True,
            read_only=True,
            lazy=False,
            raise_exceptions=False)

        return True if c.bind() else False
