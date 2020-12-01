import json
from datetime import date

from django.apps import apps

from cohort.models import User
from django.db import models

from cohort_back.FhirAPi import send_cohort_query, check_cohort_status, retrieve_cohort_result, send_cohort_count_query
from cohort_back.models import BaseModel

REQUEST_STATUS_CHOICES = [
    ("pending", "pending"),
    ("started", "started"),
    ("cancelled", "cancelled"),
    ("finished", "finished")
]
PENDING_REQUEST_STATUS = REQUEST_STATUS_CHOICES[0][0]
STARTED_REQUEST_STATUS = REQUEST_STATUS_CHOICES[1][0]
FINISHED_REQUEST_STATUS = REQUEST_STATUS_CHOICES[3][0]

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
    # refresh_intervale_seconds = models.BigIntegerField(default=0)
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
            self.generate_result()

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

    def generate_result(self):
        result = send_cohort_count_query(str(self.serialized_query))
        dm = DatedMeasure()
        dm.request_query_history = self
        dm.request = self.request
        dm.measure = result.size
        dm.save()
        return dm

    def duplicate(self):
        new_self = self
        new_self.pk = None
        new_self.save()
        return new_self

    def generate_cohort(self, name: str = None, description: str = None):
        dm = self.generate_result()

        result = send_cohort_query(str(self.serialized_query))
        c = CohortResult()
        c.name = name or (self.request.name + date.today().strftime("%y%m%d"))
        c.description = description or self.request.description
        c.request_query_snapshot = self
        c.request = self.request
        c.dated_measure = dm
        c.request_job_id = result.job_id
        c.save()
        return c


class DatedMeasure(BaseModel):
    """
    This is an intermediary result giving only limited info before
    possibly generating a Cohort/Group in Fhir.
    """
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_request_query_results')
    request_query_snapshot = models.ForeignKey(RequestQuerySnapshot, on_delete=models.CASCADE)
    request = models.ForeignKey(Request, on_delete=models.CASCADE)

    fhir_datetime = models.DateTimeField(null=False, blank=False)
    measure = models.BigIntegerField(null=False, blank=False)  # Size of potential cohort as returned by SolR
    # perimeter = models.ForeignKey(Perimeter, on_delete=models.CASCADE)

    # result_size = models.BigIntegerField()  # Number of results as returned by SolR


class CohortResult(BaseModel):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_cohorts')

    name = models.CharField(max_length=50)
    description = models.TextField(blank=True)
    favorite = models.BooleanField(default=False)

    request_query_snapshot = models.ForeignKey(RequestQuerySnapshot, on_delete=models.CASCADE)
    request = models.ForeignKey(Request, on_delete=models.CASCADE, related_name='request_cohorts')

    fhir_group_id = models.CharField(max_length=64, blank=True)
    dated_measure = models.ForeignKey(DatedMeasure, related_name="cohort", on_delete=models.PROTECT)

    request_job_id = models.TextField(blank=True)
    request_job_status = models.CharField(max_length=10, choices=REQUEST_STATUS_CHOICES,
                                          default=PENDING_REQUEST_STATUS)

    # will depend on the right (pseudo-anonymised or nominative) you have on the care_site
    type = models.CharField(max_length=20, choices=COHORT_TYPE_CHOICES, default=MY_COHORTS_COHORT_TYPE)
    # rqr = models.ForeignKey(RequestResult, on_delete=models.CASCADE)

    class Meta:
        unique_together = [['owner', 'fhir_group_id', 'type']]

    def check_request_status(self):
        resp = check_cohort_status(str(self.request_job_id))
        if resp.status == "finished":
            self.retrieve_result()

        return resp

    def retrieve_result(self):
        resp = retrieve_cohort_result(self.request_job_id)
        self.fhir_group_id = resp.group_id
        return resp

    @property
    def result_size(self):
        return self.dated_measure.measure

