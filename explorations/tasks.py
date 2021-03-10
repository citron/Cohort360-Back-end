from time import sleep

from celery import shared_task

import cohort_back.settings as fhir_api
from explorations.models import CohortResult, STARTED_REQUEST_STATUS, FAILED_REQUEST_STATUS, FINISHED_REQUEST_STATUS, \
    DatedMeasure


def update_instance_failed(instance, msg, job_duration, fhir_job_id):
    instance.request_job_status = FAILED_REQUEST_STATUS
    instance.request_job_fail_msg = msg
    instance.request_job_duration = job_duration
    instance.request_job_id = fhir_job_id
    instance.save()


def log_create_task(id, msg):
    print(f"[CohortTask] [CohortResult uuid: {id}] {msg}")


@shared_task
def create_cohort_task(auth_headers: dict, json_file: str, cohort_uuid: str):
    print(f"Task opened for cohort {cohort_uuid}")

    # in case of small lattency in database saving (when calling this task)
    cr = None
    tries = 0
    while cr is None and tries <= 5:
        cr = CohortResult.objects.filter(uuid=cohort_uuid).first()
        if cr is None:
            log_create_task(cohort_uuid, f"Error: could not find CohortResult to update after {tries - 1} sec")
            tries = tries + 1
            sleep(1)

    if cr is None:
        log_create_task(cohort_uuid, f"Error: could not find CohortResult to update after 5 sec")
        return

    cr.request_job_status = STARTED_REQUEST_STATUS
    cr.save()
    cr.dated_measure.request_job_status = STARTED_REQUEST_STATUS
    cr.dated_measure.save()

    log_create_task(cohort_uuid, "Asking fhir to create cohort")
    resp = fhir_api.post_create_cohort(json_file, auth_headers)

    if resp.success:
        cr.dated_measure.fhir_datetime = resp.fhir_datetime
        cr.dated_measure.measure = resp.count
        cr.dated_measure.request_job_id = resp.fhir_job_id
        cr.dated_measure.request_job_status = FINISHED_REQUEST_STATUS
        cr.dated_measure.request_job_duration = resp.job_duration
        cr.dated_measure.save()

        cr.fhir_group_id = resp.group_id
        cr.request_job_id = resp.fhir_job_id
        cr.request_job_status = FINISHED_REQUEST_STATUS
        cr.request_job_duration = resp.job_duration
        cr.save()

        log_create_task(cohort_uuid, "CohortResult and dated measure updated")
    else:
        update_instance_failed(cr, resp.err_msg, resp.job_duration, resp.fhir_job_id)
        update_instance_failed(cr.dated_measure, resp.err_msg, resp.job_duration, resp.fhir_job_id)
        log_create_task(cohort_uuid, resp.err_msg)


def log_count_task(id, msg):
    print(f"[CountTask] [DM uuid: {id}] {msg}")


@shared_task
def get_count_task(auth_headers: dict, json_file: str, dm_uuid: str):
    # in case of small lattency in database saving (when calling this task)
    dm = None
    tries = 0
    while dm is None and tries <= 5:
        dm = DatedMeasure.objects.filter(uuid=dm_uuid).first()
        if dm is None:
            log_count_task(dm_uuid, f"Error: could not find DatedMeasure to update after {tries - 1} sec")
            tries = tries + 1
            sleep(1)

    if dm is None:
        log_count_task(dm_uuid, "Error: could not find DatedMeasure to update")
        return

    dm.request_job_status = STARTED_REQUEST_STATUS
    dm.save()

    log_count_task(dm_uuid, "Asking fhir to get count")
    resp = fhir_api.post_count_cohort(json_file, auth_headers)

    if resp.success:
        dm.fhir_datetime = resp.fhir_datetime
        dm.measure = resp.count
        dm.measure_male = resp.count_male
        dm.measure_unknown = resp.count_unknown
        dm.measure_deceased = resp.count_deceased
        dm.measure_alive = resp.count_alive
        dm.measure_female = resp.count_female
        dm.request_job_status = FINISHED_REQUEST_STATUS
        dm.request_job_duration = resp.job_duration
        dm.request_job_id = resp.fhir_job_id
        dm.save()
        log_count_task(dm_uuid, "Dated measure updated")
    else:
        update_instance_failed(dm, resp.err_msg, resp.job_duration, resp.fhir_job_id)
        log_count_task(dm_uuid, resp.err_msg)

