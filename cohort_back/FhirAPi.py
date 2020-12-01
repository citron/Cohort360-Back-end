import requests


class FhirQueryResponse():
    def __init__(self, resp: requests.Response):
        result = resp.json()
        self.size: str = result["count"]
        self.job_id: str = result["job_id"]
        return


class FhirStatusResponse():
    def __init__(self, resp: requests.Response):
        result = resp.json()
        self.status: str = result["status"]
        return


class FhirCohortResponse():
    def __init__(self, resp: requests.Response):
        result = resp.json()
        self.group_id: str = result["group_id"]
        return


def send_cohort_count_query(json: str) -> FhirQueryResponse:
    return


def send_cohort_query(json: str) -> FhirQueryResponse:
    return


def check_cohort_status(job_id: str) -> FhirStatusResponse:
    return


def retrieve_cohort_result(cohort_id) -> FhirCohortResponse:
    return



