from django.db import models

from cohort.models import BaseModel, User


class Vote(BaseModel):
    issue_id = models.IntegerField()
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='issues_users')

    VOTE_CHOICES = [
        (1, 'Positive vote'),
        (0, 'Neutral vote'),
        (-1, 'Negative vote')
    ]
    vote = models.IntegerField(choices=VOTE_CHOICES, default=0)
