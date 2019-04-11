import requests

from tests.util import assert_status, assert_value, req

# Create user

user_data = {
    "username": "basicuser",
    "password": "zfe754jyt5",
    "email": "zfezfz@ezgzeg.fr",
    "auth_type": "SIMPLE",
    "displayname": "Basic User",
    "firstname": "Basic",
    "lastname": "User",
}


def clean():
    tokens = req("post", "/jwt/", data={"username": user_data['username'], "password": user_data['password']})
    if tokens.status_code == 400:
        return
    req("delete", "/users/{}".format(user_data['username']), headers={'Authorization': 'Bearer ' + tokens.json()['access']})


clean()
try:

    result = req("post", "/users/", data=user_data)
    assert_status(result, 201, "create user")

    result = req("post", "/jwt/", data={"username": user_data['username'], "password": user_data['password']})
    assert_status(result, 200, "get jwt tokens")
    token = result.json()

    result = req("put", "/users/{}/".format(user_data['username']),
                 headers={'Authorization': 'Bearer ' + token['access']})
    assert_status(result, 405, "put user")

    result = req("patch", "/users/{}/".format(user_data['username']), data={"firstname": "ezfze"},
                 headers={'Authorization': 'Bearer ' + token['access']})
    assert_status(result, 200, "patch user")

    result = req("get", "/users/{}/".format(user_data['username']), headers={'Authorization': 'Bearer ' + token['access']})
    assert_status(result, 200, "get user")
    assert_value(result, "check user firstname after patch", firstname="ezfze")

    result = req("delete", "/users/{}/".format(user_data['username']), headers={'Authorization': 'Bearer ' + token['access']})
    assert_status(result, 204, "delete user")


except AssertionError as e:
    clean()
    raise e
