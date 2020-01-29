from voting.models import GitlabIssue
from voting.util import req_url

from datetime import datetime


def gitlab_date_to_dt(date_str):
    if date_str is None:
        return None
    if '.' in date_str:
        date_str = date_str.split('.')[0]
    return datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S")


def get_or_create_gitlab_issue(r):
    try:
        gi = GitlabIssue.objects.get(iid=r['iid'])
    except GitlabIssue.DoesNotExist:
        gi = GitlabIssue()
        gi.iid = r['iid']

    gi.state = r['state']
    gi.labels = ','.join(r['labels'])

    gi.gitlab_created_at = gitlab_date_to_dt(r['created_at'])
    gi.gitlab_updated_at = gitlab_date_to_dt(r.get('updated_at', None))
    gi.gitlab_closed_at = gitlab_date_to_dt(r.get('closed_at', None))
    gi.title = r['title']
    gi.description = r['description']
    if gi.description is None:
        gi.description = ''
    gi.save()
    return gi


def update_with_gitlab_issues():
    per_page = 100
    page = 0

    all_results = []
    while True:
        url = "/issues?per_page={}&page={}".format(per_page, page)
        res = req_url("get", url)

        if res.status_code != 200:
            raise ConnectionError("Query to gitlab did not succeed: url={}, status={} and error={}".format(
                url, res.status_code, res.text
            ))

        results = res.json()

        all_results.extend(results)

        if len(results) == 100:
            page += 1
        else:
            break

    for r in all_results:
        get_or_create_gitlab_issue(r)
