import os
import re
import ssl
import logging as log
from ldap3 import Tls, Server, Connection, ALL, ALL_ATTRIBUTES, SUBTREE
from ldap3.core.exceptions import LDAPBindError

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
        log.debug("binding user: [%s]", username)
        tls = Tls(validate=ssl.CERT_NONE, version=ssl.PROTOCOL_TLSv1_2)
        s = Server(host=AD_HOST, port=int(AD_PORT), tls=tls, get_info="ALL")
        try:
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

            c.bind()
        except LDAPBindError:
            log.error("binding user: [%s] (failed)", username)
            return False

        # if we don't have any auth_groups, we are done.
        if auth_groups is None or len(auth_groups) == 0:
            return True

        # fetch user object and extract groups
        log.debug("searching for entry: sAMAccountName=%s", username)
        c.search(search_base=AD_BASEDN,
                 search_filter=f"(sAMAccountName={username})",
                 search_scope=SUBTREE,
                 attributes=["memberOf"])

        # just a check... should not be 0 unless they are not in the active container
        if len(c.response) == 0:
            log.warn("no entities in ldap search response")
            return False

        # collect ad groups
        ad_groups = []
        for entry in c.response:
            ad_groups += entry["attributes"]["memberOf"]

        if log.getLogger().isEnabledFor(log.DEBUG):
            for ad_group in ad_groups:
                log.debug("ad_group: %s", ad_group)

        return self.check_groups(ad_groups, auth_groups)

    @staticmethod
    def check_groups(ad_groups, auth_groups):
        auth_group_names = [auth_group.lower() for auth_group in auth_groups]

        ad_group_names = []
        for ad_group in ad_groups:
            match = re.search("cn=(.*?),.*", ad_group.lower())
            if match:
                ad_group_names.append(match.group(1))
                log.debug("matched: %s from %s", match.group(1), match.group(0))

        log.debug("common groups: %s", set(auth_group_names).intersection(ad_group_names))

        return len(set(auth_group_names).intersection(ad_group_names)) > 0
