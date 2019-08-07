import getpass
import json

import requests
from requests import post
import time

print("Please enter your APHP username: ")
username = input()

print("Please enter your APHP password: ")
password = getpass.getpass()

API_URL = "http://localhost:44455"


def debug_curl(url, method, data, headers):
    command = "curl -X {method} -H {headers} -d '{data}' '{url}'"
    headers = ['"{0}: {1}"'.format(k, v) for k, v in headers.items() if
               k in ["Authorization", "Accept", "Accept-Language"]] if headers else []
    headers = " -H ".join(headers)
    data = data if data else {}
    return "\x1b[1;33m" + command.format(method=method, data=json.dumps(data), headers=headers,
                                         url=url) + " | python -m json.tool" + "\x1b[0m"


def req(method, url, data=None, headers=None):
    print(debug_curl(API_URL + url, method, data, headers))
    result = getattr(requests, method)(API_URL + url, data=data, headers=headers)
    return result


resp = post("https://jwt-auth.eds.aphp.fr/jwt/", data={"username": username, "password": password})

if resp.status_code != 200:
    print("Identification error!")
    print(resp.text)
    exit(1)

access_token = resp.json()['access']

my_perimeters = req("get", "/perimeters", headers={'Authorization': 'Bearer ' + access_token})
print(my_perimeters.json())
