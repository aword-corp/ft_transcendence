from django.db import models


class Count(models.Model):
    clicks = models.IntegerField(default=0)

class Chat(models.Model):
    message = models.CharField(max_length=100)