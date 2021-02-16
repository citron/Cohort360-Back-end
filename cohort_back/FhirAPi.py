class FhirValidateResponse:
    def __init__(self, success: bool = False, err_msg: str = ""):
        self.success = success
        self.err_msg = err_msg


class FhirCountResponse(FhirValidateResponse):
    def __init__(self, count: int = None, fhir_datetime=None, fhir_job_id: str = "", job_duration=None,
                 success: bool = False, err_msg: str = ""):
        super(FhirCountResponse, self).__init__(success=success, err_msg=err_msg)
        self.count = count
        self.fhir_datetime = fhir_datetime
        self.job_duration = job_duration
        self.fhir_job_id = fhir_job_id


class FhirCohortResponse(FhirCountResponse):
    def __init__(self, count: int = None, group_id: str = "", fhir_datetime=None, fhir_job_id: str = "",
                 job_duration=None, success: bool = False, err_msg: str = ""):
        super(FhirCohortResponse, self).__init__(count=count, fhir_datetime=fhir_datetime, fhir_job_id=fhir_job_id,
                                                 job_duration=job_duration, success=success, err_msg=err_msg)
        self.group_id = group_id
