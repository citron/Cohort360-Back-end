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

admin_ids = {
    "username": "admin",
    "password": "admin123456789"
}

exploration_data = {
    "name": "test",
    "description": "test descr",
    "favorite": False,
    "owner_id": "9312efd0-06eb-4068-9132-bef3f1ea5aec",
}

request_data = {
    "name": "reqtest",
    "description": "test req descr",
    "shared": False,
    "refresh_every": 7500
}


def clean():
    tokens = req("post", "/jwt/", data={"username": user_data['username'], "password": user_data['password']})
    if tokens.status_code == 400:
        return
    req("delete", "/users/{}".format(user_data['username']),
        headers={'Authorization': 'Bearer ' + tokens.json()['access']})


clean()
try:
    result = req("post", "/jwt/", data=admin_ids)
    assert_status(result, 200, "get jwt tokens for admin user")
    admin_token = result.json()

    result = req("post", "/users/", data=user_data)
    assert_status(result, 201, "create user")

    result = req("post", "/jwt/", data={"username": user_data['username'], "password": user_data['password']})
    assert_status(result, 200, "get jwt tokens for basic user")
    token = result.json()

    result = req("put", "/users/{}/".format(user_data['username']),
                 headers={'Authorization': 'Bearer ' + token['access']})
    assert_status(result, 405, "put user")

    result = req("patch", "/users/{}/".format(user_data['username']), data={"firstname": "ezfze"},
                 headers={'Authorization': 'Bearer ' + token['access']})
    assert_status(result, 200, "patch user")

    result = req("get", "/users/{}/".format(user_data['username']),
                 headers={'Authorization': 'Bearer ' + token['access']})
    assert_status(result, 200, "get user")
    assert_value(result, "check user firstname after patch", firstname="ezfze")

    result = req("get", "/groups/care/add/{}/".format(user_data['username']),
                 headers={'Authorization': 'Bearer ' + token['access']})
    assert_status(result, 403, "add user to care group with user token should fail")

    result = req("get", "/groups/care/add/{}/".format(user_data['username']),
                 headers={'Authorization': 'Bearer ' + admin_token['access']})
    assert_status(result, 200, "add user to care group with admin token should succeed")

    result = req("get", "/groups/care/remove/{}/".format(user_data['username']),
                 headers={'Authorization': 'Bearer ' + token['access']})
    assert_status(result, 403, "remove user from care group with token should fail")

    result = req("get", "/groups/care/remove/{}/".format(user_data['username']),
                 headers={'Authorization': 'Bearer ' + admin_token['access']})
    assert_status(result, 200, "remove user from care group with admin token should succeed")

    exploration_data["shared"] = False
    result = req("post", "/explorations/", data=exploration_data,
                 headers={'Authorization': 'Bearer ' + admin_token['access']})
    assert_status(result, 201, "create exploration with admin user")
    exploration_uuid = result.json()['uuid']

    exploration_data["shared"] = True
    result = req("post", "/explorations/", data=exploration_data,
                 headers={'Authorization': 'Bearer ' + admin_token['access']})
    assert_status(result, 201, "create shared exploration with admin user")
    exploration_uuid_shared = result.json()['uuid']

    result = req("get", "/explorations/?owner_id={}&limit=1000000".format(exploration_data["owner_id"]),
                 headers={'Authorization': 'Bearer ' + token['access']})
    assert_status(result, 200, "get admin shared explorations from basic user")
    # FIXME:
    # assert exploration_uuid not in [r['uuid'] for r in result.json()["results"]]
    assert exploration_uuid_shared in [r['uuid'] for r in result.json()["results"]]

    request_data['exploration_id'] = exploration_uuid
    request_data['shared'] = False
    result = req("post", "/requests/", data=request_data,
                 headers={'Authorization': 'Bearer ' + admin_token['access']})
    assert_status(result, 201, "create request with admin user")
    request_uuid = result.json()['uuid']

    request_data['shared'] = True
    result = req("post", "/requests/", data=request_data,
                 headers={'Authorization': 'Bearer ' + admin_token['access']})
    assert_status(result, 201, "create shared request with admin user")
    request_uuid_shared = result.json()['uuid']

    result = req("delete", "/requests/{}/".format(request_uuid),
                 headers={'Authorization': 'Bearer ' + token['access']})
    assert_status(result, 404, "delete admin request with basic user should fail")

    result = req("delete", "/requests/{}/".format(request_uuid),
                 headers={'Authorization': 'Bearer ' + admin_token['access']})
    assert_status(result, 204, "delete admin request with admin user should succeed")
    result = req("delete", "/requests/{}/".format(request_uuid_shared),
                 headers={'Authorization': 'Bearer ' + admin_token['access']})
    assert_status(result, 204, "delete admin shared request with admin user should succeed")

    result = req("delete", "/explorations/{}/".format(exploration_uuid),
                 headers={'Authorization': 'Bearer ' + token['access']})
    assert_status(result, 403, "delete admin exploration with basic user should fail")

    result = req("delete", "/explorations/{}/".format(exploration_uuid),
                 headers={'Authorization': 'Bearer ' + admin_token['access']})
    assert_status(result, 204, "delete admin exploration with admin user should succeed")
    result = req("delete", "/explorations/{}/".format(exploration_uuid_shared),
                 headers={'Authorization': 'Bearer ' + admin_token['access']})
    assert_status(result, 204, "delete admin shared exploration with admin user should succeed")

    result = req("delete", "/users/{}/".format(user_data['username']),
                 headers={'Authorization': 'Bearer ' + token['access']})
    assert_status(result, 204, "delete user")


except AssertionError as e:
    clean()
    raise e
