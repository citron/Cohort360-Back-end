import requests

from cohort_back.settings import VOTING_GITLAB


def req_url(method, end, data=None):
    url = VOTING_GITLAB['api_url'] + "/projects/" + VOTING_GITLAB['project_id'] + end

    return getattr(requests, method)(
        url,
        headers={"PRIVATE-TOKEN": VOTING_GITLAB['private_token']},
        data=data)


def post_gitlab_issue(data: dict={}):
    url = f"{VOTING_GITLAB['api_url']}/projects/" \
          f"{VOTING_GITLAB['project_id']}/issues"

    return requests.post(
        url,
        headers={"PRIVATE-TOKEN": VOTING_GITLAB['private_token']},
        data=data
    )
