import os
import base64
import falcon
import logging as log
import active_directory_dao

log.basicConfig(level=log.INFO, format="[%(asctime)s][%(levelname)s]: %(message)s")
if "DEBUG" in os.environ and os.environ["DEBUG"] == "1":
    log.getLogger().setLevel(log.DEBUG)


class AuthResource:
    def __init__(self):
        self.ad_dao = active_directory_dao.ActiveDirectoryDAO()

    def on_get(self, req, res):
        if req.auth is None:
            res.status = falcon.HTTP_UNAUTHORIZED
            log.info("request has no authorization header")
            return

        auth = base64.b64decode(req.auth[6:])
        usr, pwd = auth.decode("utf-8").split(":", 1)

        auth_users = []
        x_auth_users = req.get_header('x-auth-users')
        if x_auth_users is not None:
            auth_users = x_auth_users.lower().split(',')
        log.debug("users: %s", auth_users)

        if len(auth_users) > 0 and usr.lower() not in auth_users:
            res.status = falcon.HTTP_UNAUTHORIZED
            log.info(f"{usr} not in allowed user list")
            return

        auth_groups = []
        x_auth_groups = req.get_header('x-auth-groups')
        if x_auth_groups is not None:
            auth_groups = x_auth_groups.lower().split(',')
        log.debug("groups: %s", auth_groups)

        try:
            authenticated = self.ad_dao.authenticate(usr, pwd, auth_users, auth_groups)
        except BaseException as err:
            print(f"bind error: {err}")
            authenticated = False

        if not authenticated:
            log.info("%s is not authenticated", usr)
            res.status = falcon.HTTP_UNAUTHORIZED
            return

        log.info("%s is authenticated", usr)
        res.status = falcon.HTTP_OK


api = falcon.API()
api.add_route("/auth", AuthResource())
