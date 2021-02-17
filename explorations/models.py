# from __future__ import annotations
import json
from datetime import date
from django.apps import apps

from cohort.models import User
from django.db import models

from cohort_back.models import BaseModel
from cohort_back.settings import format_json_request

PENDING_REQUEST_STATUS = "pending"
STARTED_REQUEST_STATUS = "started"
CANCELLED_REQUEST_STATUS = "cancelled"
FINISHED_REQUEST_STATUS = "finished"
FAILED_REQUEST_STATUS = "failed"

REQUEST_STATUS_CHOICES = [
    (PENDING_REQUEST_STATUS, PENDING_REQUEST_STATUS),
    (STARTED_REQUEST_STATUS, STARTED_REQUEST_STATUS),
    (CANCELLED_REQUEST_STATUS, CANCELLED_REQUEST_STATUS),
    (FAILED_REQUEST_STATUS, FAILED_REQUEST_STATUS),
    (FINISHED_REQUEST_STATUS, FINISHED_REQUEST_STATUS)
]

COHORT_TYPE_CHOICES = [
    ("IMPORT_I2B2", "Previous cohorts imported from i2b2.",),
    ("MY_ORGANIZATIONS", "Organizations in which I work (care sites with pseudo-anonymised reading rights).",),
    ("MY_PATIENTS", "Patients that passed by all my organizations (care sites with nominative reading rights)."),
    ("MY_COHORTS", "Cohorts I created in Cohort360")
]

I2B2_COHORT_TYPE = COHORT_TYPE_CHOICES[0][0]
MY_ORGANISATIONS_COHORT_TYPE = COHORT_TYPE_CHOICES[1][0]
MY_PATIENTS_COHORT_TYPE = COHORT_TYPE_CHOICES[2][0]
MY_COHORTS_COHORT_TYPE = COHORT_TYPE_CHOICES[3][0]

REQUEST_DATA_TYPE_CHOICES = [
    ("PATIENT", 'FHIR Patient'),
    ('ENCOUNTER', 'FHIR Encounter')
]
PATIENT_REQUEST_TYPE = REQUEST_DATA_TYPE_CHOICES[0][0]


class Request(BaseModel):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_requests')

    name = models.CharField(max_length=50)
    description = models.TextField(blank=True)
    favorite = models.BooleanField(default=False)

    data_type_of_query = models.CharField(max_length=9, choices=REQUEST_DATA_TYPE_CHOICES, default=PATIENT_REQUEST_TYPE)

    def last_request_snapshot(self):
        return RequestQuerySnapshot.objects.filter(request__uuid=self.uuid).latest('created_at')

    def saved_snapshot(self):
        return self.query_snapshots.filter(saved=True).first()


class RequestQuerySnapshot(BaseModel):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_request_query_snapshots')
    request = models.ForeignKey(Request, on_delete=models.CASCADE, related_name='query_snapshots')

    serialized_query = models.TextField(default="{}")
    refresh_every_seconds = models.BigIntegerField(default=0)
    refresh_create_cohort = models.BooleanField(default=False)

    previous_snapshot = models.ForeignKey("RequestQuerySnapshot", related_name="next_snapshots",
                                          on_delete=models.SET_NULL, null=True)
    is_active_branch = models.BooleanField(default=True)
    saved = models.BooleanField(default=False)

    @property
    def active_next_snapshot(self):
        rqs_model = apps.get_model('explorations', 'RequestQuerySnapshot')
        next_snapshots = rqs_model.objects.filter(previous_snapshot=self)
        return next_snapshots.filter(is_active_branch=True).first()

    def refresh(self):
        if self.refresh_create_cohort:
            self.generate_cohort()
        else:
            self.generate_measure()

    def save(self, *args, **kwargs):
        try:
            json.loads(str(self.serialized_query))
        except json.decoder.JSONDecodeError as e:
            raise ValueError(f"serialized_query is not a valid JSON {e}")
        super(RequestQuerySnapshot, self).save(*args, **kwargs)

    def save_snapshot(self):
        previous_saved = self.request.saved_snapshot
        if previous_saved is not None:
            previous_saved.saved = False
            previous_saved.save()

        self.saved = True
        self.save()

    # def create_empty_dated_measure(self) -> DatedMeasure:
    def create_empty_dated_measure(self):
        dm = DatedMeasure(
            request_query_snapshot=self,
            request=self.request,
            owner=self.owner,
        )
        dm.save()
        return dm

    # def generate_measure(self, auth_headers) -> DatedMeasure:
    def generate_measure(self, auth_headers):
        dm = self.create_empty_dated_measure()

        # import explorations.tasks as tasks
        # task = tasks.get_count_task.delay(auth_headers, format_json_request(str(self.serialized_query)), dm.uuid)
        from explorations.tasks import get_count_task
        task = get_count_task.delay(auth_headers, format_json_request(str(self.serialized_query)), dm.uuid)
        dm.count_task_id = task.id
        dm.save()

        return dm

    def duplicate(self):
        new_self = self
        new_self.pk = None
        new_self.save()
        return new_self

    def generate_cohort(self, auth_headers, name: str = None, description: str = None, dm_uuid: str = ""):
        if dm_uuid:
            dm = DatedMeasure.objects.filter(uuid=dm_uuid).first()
            if dm is None:
                raise Exception(f"You provided a dated_measure_id '{dm_uuid}', but not dated_measure was found")
        else:
            dm = self.create_empty_dated_measure()

        cr = CohortResult(
            owner=self.owner,
            request_query_snapshot=self,
            request=self.request,
            name=name or (self.request.name + date.today().strftime("%y%m%d")),
            description=description or self.request.description,
            dated_measure=dm
        )
        cr.save()

        # import explorations.tasks as tasks
        # task = tasks.create_cohort_task.delay(auth_headers, format_json_request(str(self.serialized_query)), cr.uuid)
        from explorations.tasks import create_cohort_task
        task = create_cohort_task.delay(auth_headers, format_json_request(str(self.serialized_query)), cr.uuid)
        cr.create_task_id = task.id
        cr.save()

        return cr


class DatedMeasure(BaseModel):
    """
    This is an intermediary result giving only limited info before
    possibly generating a Cohort/Group in Fhir.
    """
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_request_query_results')
    request_query_snapshot = models.ForeignKey(RequestQuerySnapshot, on_delete=models.CASCADE)
    request = models.ForeignKey(Request, on_delete=models.CASCADE)

    fhir_datetime = models.DateTimeField(null=True, blank=False)
    measure = models.BigIntegerField(null=True, blank=False)  # Size of potential cohort as returned by SolR

    count_task_id = models.TextField(blank=True)
    request_job_id = models.TextField(blank=True)
    request_job_status = models.CharField(max_length=10, choices=REQUEST_STATUS_CHOICES,
                                          default=PENDING_REQUEST_STATUS)
    request_job_fail_msg = models.TextField(blank=True)
    request_job_duration = models.TextField(blank=True)


class CohortResult(BaseModel):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_cohorts')

    name = models.CharField(max_length=50)
    description = models.TextField(blank=True)
    favorite = models.BooleanField(default=False)

    request_query_snapshot = models.ForeignKey(RequestQuerySnapshot, on_delete=models.CASCADE)
    request = models.ForeignKey(Request, on_delete=models.CASCADE, related_name='request_cohorts')

    fhir_group_id = models.CharField(max_length=64, blank=True)
    dated_measure = models.ForeignKey(DatedMeasure, related_name="cohort", on_delete=models.PROTECT)

    create_task_id = models.TextField(blank=True)
    request_job_id = models.TextField(blank=True)
    request_job_status = models.CharField(max_length=10, choices=REQUEST_STATUS_CHOICES,
                                          default=PENDING_REQUEST_STATUS)
    request_job_fail_msg = models.TextField(blank=True)
    request_job_duration = models.TextField(blank=True)

    # will depend on the right (pseudo-anonymised or nominative) you have on the care_site
    type = models.CharField(max_length=20, choices=COHORT_TYPE_CHOICES, default=MY_COHORTS_COHORT_TYPE)

    class Meta:
        unique_together = []

    @property
    def result_size(self):
        return self.dated_measure.measure

