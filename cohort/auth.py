from requests import post

from cohort_back.settings import JWT_SERVER_URL


class IDServer:
    @classmethod
    def check_ids(cls, username, password):
        resp = post("{}/jwt/".format(JWT_SERVER_URL), data={"username": username, "password": password})
        if resp.status_code != 200:
            raise ValueError("Invalid username or password")
        return resp.json()

    @classmethod
    def user_info(cls, jwt_access_token):
        resp = post("{}/jwt/user_info/".format(JWT_SERVER_URL), data={"token": jwt_access_token})
        if resp.status_code == 200:
            return resp.json()
        raise ValueError("Invalid JWT Access Token")

    @classmethod
    def verify_jwt(cls, access_token):
        resp = post("{}/jwt/verify/".format(JWT_SERVER_URL), data={"token": access_token})
        return resp.status_code == 200
