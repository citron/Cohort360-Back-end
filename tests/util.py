import json

import requests

API_URL = "https://localhost:44455"


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


class Error(Exception):
    def __init__(self, result, name):
        self.result = result
        self.name = name

    def __str__(self):
        return "Error appended while doing: {}\nStatus code: {}\nResponse: {}".format(self.name,
                                                                                      self.result.status_code,
                                                                                      self.result.content)


def assert_status(result, expected_status_code, name):
    if result.status_code != expected_status_code:
        raise Error(result, name)


def assert_value(result, name, **kwargs):
    j = result.json()
    for k, v in kwargs.items():
        if j[k] != v:
            raise Error(result, name)
