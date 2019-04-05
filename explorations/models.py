from cohort.models import BaseModel, User
from django.db import models


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

    def __save__(self, *args, **kwargs):
        super(Request, self).save(*args, **kwargs)

    def get_cohorts(self):
        return Cohort.objects.filter(request=self)

    def duplicate(self):
        new_self = self
        new_self.pk = None
        new_self.save()
        return new_self


class Cohort(BaseModel):
    name = models.CharField(max_length=30)
    description = models.TextField(blank=True)
    shared = models.BooleanField(default=False)

    request = models.ForeignKey(Request, on_delete=models.CASCADE, related_name='cohorts')
