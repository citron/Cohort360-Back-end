import jwt
from requests import post

import cohort_back.settings as settings

jwt_headers = {settings.JWT_APP_HEADER: settings.JWT_APP_NAME}


class IDServer:
    @classmethod
    def check_ids(cls, username, password):
        if settings.SERVER_VERSION.lower() == "dev":
            return {
                settings.JWT_SERVER_ACCESS_KEY: "refreshToken",
                settings.JWT_SERVER_REFRESH_KEY: "accessToken",
            }

        resp = post("{}/jwt/".format(settings.JWT_SERVER_URL), data={
            "username": username, "password": password
        })
        if resp.status_code != 200:
            raise ValueError("Invalid username or password")
        return resp.json()

    @classmethod
    def user_info(cls, jwt_access_token):
        if settings.SERVER_VERSION.lower() == "dev":
            return dict(
                username=4163302,
                email="squall@balamb_garden.bal",
                firstname="Squall",
                lastname="Leonheart"
            )

        resp = post("{}/jwt/user_info/".format(
            settings.JWT_SERVER_URL),
            data={"token": jwt_access_token}
        )
        if resp.status_code == 200:
            return resp.json()
        raise ValueError("Invalid JWT Access Token")

    @classmethod
    def verify_jwt(cls, access_token):
        if settings.SERVER_VERSION.lower() == "dev":
            return dict(
                username=4163302,
            )

        if settings.JWT_SIGNING_KEY is not None:
            try:
                return jwt.decode(
                    access_token, settings.JWT_SIGNING_KEY, leeway=15,
                    algorithm=settings.JWT_ALGORITHM
                )
            except jwt.exceptions.InvalidSignatureError:
                pass
        else:
            resp = post("{}/jwt/verify/".format(
                settings.JWT_SERVER_URL), data={"token": access_token}
            )
            if resp.status_code == 200:
                return jwt.decode(
                    access_token, verify=False, verify_exp=True, leeway=15,
                    algorithm=settings.JWT_ALGORITHM
                )
        raise ValueError("Invalid JWT Access Token")

    @classmethod
    def refresh_jwt(cls, refresh):
        if settings.SERVER_VERSION.lower() == "dev":
            return {
                settings.JWT_SERVER_ACCESS_KEY: "refreshToken",
                settings.JWT_SERVER_REFRESH_KEY: "accessToken",
            }

        resp = post(
            "{}/jwt/refresh/".format(settings.JWT_SERVER_URL),
            data=dict(refresh=refresh), headers=jwt_headers
        )
        if resp.status_code == 200:
            return resp.json()
        raise ValueError("Invalid JWT Refresh Token")
