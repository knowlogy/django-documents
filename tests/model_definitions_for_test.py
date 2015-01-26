from django_documents import fields
from django_documents import documents as persistentmodels
from django_documents import related       

import types        

class ModelWithFloatField(persistentmodels.Model):
    float = fields.FloatField()
    
        
class ModelWithAllBaseFields(persistentmodels.Model):
    float = fields.FloatField()
    date = fields.DateField()
    char = fields.CharField()
    integer = fields.IntegerField()
    

class ModelWithOneOffField(persistentmodels.Model):
    name = fields.CharField()
    oneOf = related.OneOf(ModelWithAllBaseFields)
    
    
class ModelWithListOffStringType(persistentmodels.Model):
    name = fields.CharField()
    listOfString = related.ListOf(types.StringType)
    
    
class ModelWithListModelWithAllBaseFields(persistentmodels.Model):
    name = fields.CharField()
    listOf = related.ListOf(ModelWithAllBaseFields)
    
class ModelWithMapOffStringType(persistentmodels.Model):
    name = fields.CharField()
    mapOf = related.MapOf(types.StringType)


class ModelWithMapModelWithAllBaseFields(persistentmodels.Model):
    name = fields.CharField()
    mapOf = related.MapOf(ModelWithAllBaseFields)
    
    
class ContactInfo(persistentmodels.Model):
    email = fields.CharField()

class Party(persistentmodels.Model):
    name  = fields.CharField()
    name2 = fields.CharField() 
    contactInfo = related.OneOf(ContactInfo)
