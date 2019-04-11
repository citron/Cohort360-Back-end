import requests


class Error(Exception):
    def __init__(self, result, name):
        self.result = result
        self.name = name

    def __str__(self):
        return "Error appended while doing: {}\nStatus code: {}\Error: {}".format(self.name, self.result.status_code,
                                                                                  self.result.content)


def assert_status(result, expected_status_code, name):
    if result.status_code != expected_status_code:
        raise Error(result, name)


API_URL = "http://127.0.0.1:8002"

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
    tokens = requests.post(API_URL + "/jwt/",
                           data={"username": user_data['username'], "password": user_data['password']})
    if tokens.status_code == 400:
        return
    requests.delete(API_URL + "/users/{}".format(user_data['username']),
                    headers={'Authorization': 'Bearer ' + tokens.json()['access']})

try:

    result = requests.post(API_URL + "/users/", data=user_data)
    print(result.__dict__)
    assert_status(result, 201, "create user")

    result = requests.post(API_URL + "/jwt/",
                           data={"username": user_data['username'], "password": user_data['password']})
    assert_status(result, 200, "get jwt tokens")

    

    result = requests.delete(API_URL + "/users/{}".format(user_data['username']),
                    headers={'Authorization': 'Bearer ' + result.json()['access']})
    assert_status(result, 204, "delete user")


except AssertionError as e:
    clean()
    raise e
