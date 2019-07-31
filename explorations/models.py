import json

from cohort.models import BaseModel, User
from django.db import models


class Perimeter(BaseModel):
    """
    A Perimeter contains either services or groups of patient
    """
    name = models.CharField(max_length=30)
    description = models.TextField(blank=True)

    DATA_TYPE_CHOICES = [
        ("GROUP", 'FHIR Group'),
        ('ORG', 'FHIR Organization(s)')
    ]
    data_type = models.CharField(max_length=5, choices=DATA_TYPE_CHOICES)
    fhir_query = models.TextField()
    # Either:
    #  1. A Fhir Group : /Group/id
    #  2. A list of FHIR Organizations : /PractionerRole/me

    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='perimeters')


class Exploration(BaseModel):
    """
    An Exploration can contain multiple Requests.
    """
    name = models.CharField(max_length=30)
    description = models.TextField(blank=True)
    favorite = models.BooleanField(default=False)
    shared = models.BooleanField(default=False)

    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='explorations')

    def get_requests(self):
        return Request.objects.filter(exploration=self)


class Request(BaseModel):
    """
    A Request is made of many organized criteria.

    A Request can be used to generate a Cohort.
    Once a Request has been used to generate a Cohort, you cannot edit its criteria.
    If you want to, you must duplicate this Request and edit the new one.

    Once a Request has been used to generate a Cohort, it can be used to generate
    a new updated Cohort (with a different number of patients).

    refresh_new_number_of_patients will be automatically refreshed if refresh_every > 0 (in seconds)
    """
    name = models.CharField(max_length=30)
    description = models.TextField(blank=True)
    shared = models.BooleanField(default=False)

    exploration = models.ForeignKey(Exploration, on_delete=models.CASCADE, related_name='requests')

    stats_number_of_patients = models.BigIntegerField(default=0)
    stats_number_of_documents = models.BigIntegerField(default=0)

    refresh_every = models.BigIntegerField(default=0)
    refresh_new_number_of_patients = models.BigIntegerField(default=0)

    serialized_query = models.TextField(default="{}")

    def save(self, *args, **kwargs):
        try:
            json.loads(self.serialized_query)
        except json.decoder.JSONDecodeError as e:
            raise ValueError('value_v1 is not a valid JSON ' + str(e))
        super(Request, self).save(*args, **kwargs)

    def get_cohorts(self):
        self.save()
        return Cohort.objects.filter(request=self)

    def duplicate(self):
        new_self = self
        new_self.pk = None
        new_self.save()
        return new_self

    def execute_query(self):
        # TODO
        # result = SOLR.send_query(self.serialized_query)
        # return result
        pass


class Cohort(BaseModel):
    name = models.CharField(max_length=30)
    description = models.TextField(blank=True)
    shared = models.BooleanField(default=False)

    request = models.ForeignKey(Request, on_delete=models.CASCADE, related_name='request_cohorts')

    perimeter = models.ForeignKey(Perimeter, on_delete=models.CASCADE, related_name='perimeter_cohorts')

    fhir_group_id = models.BigIntegerField()
