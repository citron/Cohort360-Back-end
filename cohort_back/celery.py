from __future__ import absolute_import, unicode_literals
import os
from typing import TypeVar

from celery import Celery

# set the default Django settings module for the 'celery' program.
# from cohort.import_i2b2 import get_unique_patient_count_from_org_union
from cohort.import_i2b2 import OmopCohort, get_user_care_sites_cohorts, OmopCareSiteCohort
from explorations.models import STARTED_REQUEST_STATUS, PENDING_REQUEST_STATUS

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cohort_back.settings')

app = Celery('cohort_back')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()


#
# app.conf.beat_schedule = {
#     'add-every-30-seconds': {
#         'task': 'cohort_back.celery.import_i2b2',
#         'schedule': 5.0
#     },
# }
# app.conf.timezone = 'UTC'


BaseOmopCohort = TypeVar("BaseOmopCohort", OmopCohort, OmopCareSiteCohort)


def create_cohort(user, cohort: BaseOmopCohort, cohort_type):
    from explorations.models import CohortResult, Request, RequestQuerySnapshot, DatedMeasure, FINISHED_REQUEST_STATUS
    name = cohort.name[:50]
    description = cohort.description[:50]
    fhir_id = cohort.fhir_id
    create_date = cohort.creation_date
    size = cohort.size

    # If this cohort already exists, do not create it again
    cohorts = CohortResult.objects.filter(owner=user, name=name, fhir_groups_id=fhir_id, type=cohort_type)
    if cohorts.count() == 1:
        cohort = cohorts.first()
        cohort.name = name
        cohort.description = description
        cohort.type = cohort_type
        cohort.save()

        dm = cohort.dated_measure
        dm.measure = size
        dm.fhir_datetime = create_date
        dm.save()
        return cohort

    r = Request(
        owner=user,
        name=name,
        description=description
    )
    r.save()

    rqs = RequestQuerySnapshot(
        owner=user,
        request=r,
        serialized_query="{}"
    )
    rqs.save()

    dm = DatedMeasure(
        owner=user,
        request_query_snapshot=rqs,
        request=r,
        measure=size,
        fhir_datetime=create_date
    )
    dm.save()

    c = CohortResult(
        owner=user,
        name=name,
        description=description,
        dated_measure=dm,
        request_query_snapshot=rqs,
        request=r,
        fhir_groups_id=fhir_id,
        type=cohort_type,
        request_status=FINISHED_REQUEST_STATUS
    )
    c.save()

    return c


@app.task()
def import_i2b2():
    from cohort.models import User
    from cohort.import_i2b2 import get_users_cohorts, get_user_care_sites_cohorts
    from explorations.models import CohortResult, I2B2_COHORT_TYPE, MY_ORGANISATIONS_COHORT_TYPE,\
        MY_PATIENTS_COHORT_TYPE

    users = User.objects.all()
    usernames = [u.username for u in users]

    cohorts = get_users_cohorts(usernames)
    care_sites = get_user_care_sites_cohorts(usernames)

    for user in users:
        user_cohorts = [c for c in cohorts if c.username == user.username]
        user_care_sites = [c for c in care_sites if c.username == user.username]

        for cohort in user_cohorts:
            create_cohort(user, cohort, I2B2_COHORT_TYPE)

        created_cohorts = []
        for care_site in user_care_sites:
            if care_site.right_read_data_nominative:
                created_cohorts.append(create_cohort(user, care_site, MY_ORGANISATIONS_COHORT_TYPE))
            if care_site.right_read_data_pseudo_anonymised:
                create_cohort(user, care_site, MY_PATIENTS_COHORT_TYPE)

        # Delete old organizations that do not exist anymore
        CohortResult.objects \
            .filter(owner=user, type__in=[MY_ORGANISATIONS_COHORT_TYPE, MY_PATIENTS_COHORT_TYPE]) \
            .exclude(uuid__in=[c.uuid for c in created_cohorts]).delete()


@app.task()
def update_gitlab_issues():
    from voting.celery import update_with_gitlab_issues

    update_with_gitlab_issues()


@app.task()
def get_pending_jobs_status():
    from explorations.models import CohortResult, REQUEST_STATUS_CHOICES
    crs = CohortResult.objects.filter(
        request_job_status__in=[PENDING_REQUEST_STATUS, STARTED_REQUEST_STATUS]
    )

    for cr in crs:
        cr.check_request_status()

