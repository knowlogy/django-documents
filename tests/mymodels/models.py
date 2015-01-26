from django.db import models

class MyModel1(models.Model):
    a1 = models.TextField()

class MyModel2(models.Model):
    a2 = models.ForeignKey("MyModel1")   