from django.db import models


class Count(models.Model):
    clicks = models.IntegerField(default=0)
