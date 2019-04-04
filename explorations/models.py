from cohort.models import BaseModel, User
from django.db import models


class Exploration(BaseModel):
    name = models.CharField(max_length=30)
    description = models.TextField(blank=True)
    favorite = models.BooleanField(default=False)

    owner = models.ForeignKey(User, on_delete=models.CASCADE)


class Request(BaseModel):
    name = models.CharField(max_length=30)
    description = models.TextField(blank=True)

    stats_number_of_patients = models.BigIntegerField()
    exploration = models.ForeignKey(Exploration, on_delete=models.CASCADE)

    def create_cohort(self):
        Cohort()


class Cohort(BaseModel):
    name = models.CharField(max_length=30)
    description = models.TextField(blank=True)

    request = models.ForeignKey(Request, on_delete=models.CASCADE)