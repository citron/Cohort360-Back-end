import json

from django.core.validators import validate_comma_separated_integer_list

from cohort.models import BaseModel, User, Perimeter
from django.db import models


class Exploration(BaseModel):
    """
    An Exploration can contain multiple Requests.
    """
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_explorations')

    name = models.CharField(max_length=50)
    description = models.TextField(blank=True)
    favorite = models.BooleanField(default=False)

    def get_requests(self):
        return Request.objects.filter(exploration=self)


class Request(BaseModel):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_requests')

    name = models.CharField(max_length=50)
    description = models.TextField(blank=True)
    favorite = models.BooleanField(default=False)

    exploration = models.ForeignKey(Exploration, on_delete=models.CASCADE, related_name='requests')

    REQUEST_DATA_TYPE_CHOICES = [
        ("PATIENT", 'FHIR Patient'),
        ('ENCOUNTER', 'FHIR Encounter')
    ]
    data_type_of_query = models.CharField(max_length=9, choices=REQUEST_DATA_TYPE_CHOICES)

    def last_request_snapshot(self):
        return RequestQuerySnapshot.objects.filter(request__uuid=self.uuid).latest('created_at')


class RequestQuerySnapshot(BaseModel):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_request_query_snapshots')

    request = models.ForeignKey(Request, on_delete=models.CASCADE)
    serialized_query = models.TextField(default="{}")

    def save(self, *args, **kwargs):
        try:
            json.loads(self.serialized_query)
        except json.decoder.JSONDecodeError as e:
            raise ValueError('value_v1 is not a valid JSON ' + str(e))
        super(RequestQuerySnapshot, self).save(*args, **kwargs)

    def generate_result(self, perimeter):
        # TODO : generates a new RequestResult
        # result = SOLR.send_query(self.serialized_query)
        rqr = RequestQueryResult()
        rqr.request_query_history = self
        rqr.request = self.request
        rqr.perimeter = perimeter
        rqr.result_size = 42
        rqr.save()
        return rqr

    def duplicate(self):
        new_self = self
        new_self.pk = None
        new_self.save()
        return new_self

    def generate_cohort(self, name, description, perimeter):
        # TODO: launch a background process to generate a Fhir Group from this SolR request
        #       We must re-execute the query for that!
        c = Cohort()
        c.name = name
        c.description = description
        c.request_query_snapshot = self
        c.request = self.request
        c.perimeter = perimeter
        c.fhir_groups_ids = "42"
        c.save()
        return c


class RequestQueryResult(BaseModel):
    """
    This is an intermediary result giving only limited info before
    possibly generating a Cohort/Group in Fhir.
    """
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_request_query_results')

    request_query_snapshot = models.ForeignKey(RequestQuerySnapshot, on_delete=models.CASCADE)
    request = models.ForeignKey(Request, on_delete=models.CASCADE)
    perimeter = models.ForeignKey(Perimeter, on_delete=models.CASCADE)

    result_size = models.BigIntegerField()  # Number of results as returned by SolR

    refresh_every_seconds = models.BigIntegerField(default=0)
    refresh_create_cohort = models.BooleanField(default=False)

    def refresh(self):
        return self.request_query_snapshot.generate_result(self.perimeter)


class Cohort(BaseModel):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_cohorts')

    name = models.CharField(max_length=50)
    description = models.TextField(blank=True)
    favorite = models.BooleanField(default=False)

    request_query_snapshot = models.ForeignKey(RequestQuerySnapshot, on_delete=models.CASCADE)
    request = models.ForeignKey(Request, on_delete=models.CASCADE, related_name='request_cohorts')
    perimeter = models.ForeignKey(Perimeter, on_delete=models.CASCADE, related_name='perimeter_cohorts')

    fhir_groups_ids = models.TextField(validators=[validate_comma_separated_integer_list])

    COHORT_TYPE_CHOICES = [
        ("IMPORT_I2B2", "Imported from i2b2.",),
        ("MY_ORGANIZATIONS", "Organizations in which I work.",),
        ("MY_PATIENTS", "Patients that passed by all my organizations.")
    ]
    type = models.CharField(max_length=20, choices=COHORT_TYPE_CHOICES)

    result_size = models.BigIntegerField()  # Number of results as returned by SolR

    class Meta:
        unique_together = [['owner', 'fhir_groups_ids', 'type']]
