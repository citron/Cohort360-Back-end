from rest_framework.request import Request

from cohort_back.FhirAPi import FhirCountResponse, FhirCohortResponse, FhirValidateResponse


def format_json_request(json_req: str) -> str:
    """
    Called to format a json query stored in RequestQuerySnapshot
    to the format read by Fhir API
    :param json_req:
    :type json_req:
    :return:
    :rtype:
    """
    raise NotImplementedError()


def retrieve_perimeters(json_req: str) -> [str]:
    """
    Called to retrieve care_site_ids (perimeters) from a Json request
    :param json_req:
    :type json_req:
    :return:
    :rtype:
    """
    return None


def get_fhir_authorization_header(request: Request) -> dict:
    """
    Called when a request is about to be made to external Fhir API
    :param request:
    :type request:
    :return:
    :rtype:
    """
    raise NotImplementedError()


def post_count_cohort(json_file: str, auth_headers) -> FhirCountResponse:
    """
    Called to ask a Fhir API to compute the size of a cohort given
    the request in the json_file
    :param json_file:
    :type json_file:
    :param auth_headers:
    :type auth_headers:
    :return:
    :rtype:
    """
    raise NotImplementedError()


def post_create_cohort(json_file: str, auth_headers) -> FhirCohortResponse:
    """
    Called to ask a Fhir API to create a cohort given the request
    in the json_file
    :param json_file:
    :type json_file:
    :param auth_headers:
    :type auth_headers:
    :return:
    :rtype:
    """
    raise NotImplementedError()


def post_validate_cohort(json_file: str, auth_headers) -> FhirValidateResponse:
    """
    Called to ask a Fhir API to validate the format of the json_file
    :param json_file:
    :type json_file:
    :param auth_headers:
    :type auth_headers:
    :return:
    :rtype:
    """
    raise NotImplementedError()
