from django.db import models

# Create your models here.

class Users(models.Model):
    id = models.AutoField(primary_key=True)
    phone = models.CharField(max_length=255)
    upass = models.CharField(max_length=255)
    faceimg = models.CharField(max_length=255)
    nickname = models.CharField(max_length=255)
    state = models.CharField(max_length=255)
    msg = models.CharField(max_length=255)
    cts = models.CharField(max_length=255)
    sex = models.CharField(max_length=255)
    ulike = models.CharField(max_length=255)
    role = models.CharField(max_length=255)
    school = models.CharField(max_length=255)
    major = models.CharField(max_length=255)
    age = models.IntegerField(null=True,blank=True)
    email = models.CharField(max_length=255)