import os
import re
import ssl
import logging as log
from ldap3 import Tls, Server, Connection, ALL, ALL_ATTRIBUTES, SUBTREE
from ldap3.core.exceptions import LDAPBindError, LDAPException, LDAPStartTLSError
from cachetools import cached, TTLCache

log.basicConfig(level=log.INFO, format="[%(asctime)s][%(levelname)s]: %(message)s")
if "DEBUG" in os.environ and os.environ["DEBUG"] == "1":
    log.getLogger().setLevel(log.DEBUG)

AD_HOST = os.environ["AD_HOST"]
AD_PORT = os.environ["AD_PORT"]
AD_DOMAIN = os.environ["AD_DOMAIN"]
AD_BASEDN = os.environ["AD_BASEDN"]


class ActiveDirectoryDAO:
    def __init__(self):
        pass

    def authenticate(self, username, password, auth_users, auth_groups):
        ad_groups = []
        try:
            ad_groups = self.fetch_ad_groups(username, password)
        except LDAPBindError:
            log.error("binding user: [%s] (failed)", username)
            return False
        except LDAPException as ldapErr:
            log.error("ldap error: [%s]", ldapErr)
            return False
        except Exception as err:
            log.error("general error: [%s]", err)
            return False

        if auth_users is not None and auth_groups is not None:
            return self.check_user(username, auth_users) or self.check_groups(ad_groups, auth_groups)

        if auth_groups is None:
            return self.check_user(username, auth_users)

        if auth_users is None:
            return self.check_groups(ad_groups, auth_groups)

    @cached(cache=TTLCache(maxsize=1024, ttl=1800))
    def fetch_ad_groups(self, username, password):
        log.debug("binding user: [%s]", username)
        tls = Tls(validate=ssl.CERT_NONE, version=ssl.PROTOCOL_TLSv1_2)
        s = Server(host=AD_HOST, port=int(AD_PORT), tls=tls, get_info="ALL")
        c = Connection(
            s,
            user=f"{AD_DOMAIN}\\{username}",
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

        c.start_tls()
        log.debug("tls status: %s", c.tls_started)

        c.bind()

        # fetch user object and extract groups
        log.debug("searching for entry: sAMAccountName=%s", username)
        c.search(search_base=AD_BASEDN,
                 search_filter=f"(sAMAccountName={username})",
                 search_scope=SUBTREE,
                 attributes=["memberOf"])

        # just a check... should not be 0 unless they are not in the active container
        if len(c.response) == 0:
            log.warn("no entities in ldap search response")
            raise Exception("no entities in ldap search response")

        # collect ad groups
        ad_groups = []
        for entry in c.response:
            ad_groups += entry["attributes"]["memberOf"]

        if log.getLogger().isEnabledFor(log.DEBUG):
            for ad_group in ad_groups:
                log.debug("ad_group: %s", ad_group)

        return ad_groups

    @staticmethod
    def check_user(username, auth_users):
        if auth_users is None or len(auth_users) == 0:
            return True

        return username.lower() in auth_users

    @staticmethod
    def check_groups(ad_groups, auth_groups):
        if auth_groups is None or len(auth_groups) == 0:
            return True

        auth_group_names = [auth_group.lower() for auth_group in auth_groups]

        ad_group_names = []
        for ad_group in ad_groups:
            match = re.search("cn=(.*?),.*", ad_group.lower())
            if match:
                ad_group_names.append(match.group(1))
                log.debug("matched: %s from %s", match.group(1), match.group(0))

        log.debug("common groups: %s", set(auth_group_names).intersection(ad_group_names))

        return len(set(auth_group_names).intersection(ad_group_names)) > 0
