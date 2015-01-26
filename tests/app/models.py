from django.db import models as djmodels

class MyDjangomodel(djmodels.Model):       
    mymodel = djmodels.ForeignKey('MyDjangomodel')