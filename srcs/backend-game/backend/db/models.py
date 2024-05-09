from django.db import models


class Count(models.Model):
    clicks = models.IntegerField(default=0)

    class Meta:
        managed = True


class Chat(models.Model):
    message = models.CharField(max_length=512)

    class Meta:
        managed = True


class lol(models.Model):
    message = models.CharField(max_length=512)

    class Meta:
        managed = True


class nouvelle(models.Model):
    message = models.CharField(max_length=512)

    class Meta:
        managed = True
