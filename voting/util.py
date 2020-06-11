import requests

from cohort_back.settings import VOTING_GITLAB


def req_url(method, end, data=None):
    url = VOTING_GITLAB['api_url'] + "/projects/" + VOTING_GITLAB['project_id'] + end
    print(url)
    return getattr(requests, method)(
        url,
        headers={"PRIVATE-TOKEN": VOTING_GITLAB['private_token']},
        data=data)
