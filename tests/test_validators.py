import prepare_settings
        
from unittest import TestCase, main  

from django_documents import fields
from django_documents import documents as persistentmodels
from django_documents.documents import ObjectValidationError


class Person(persistentmodels.Model):
    """
    this is the definition of a simple model
    """
    first_name = fields.CharField(max_length = 10)
    last_name = fields.CharField()     

CODES = (('nl','Nederland'),('de', 'Duitsland'),)

class Thing(persistentmodels.Model):
    
    country = fields.CharField(choices = CODES)


class TestValidation(TestCase):
    
    
    def test_simple_use(self):
        person = Person()
        person.first_name = "Barucheeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee"
        try:
            person.full_clean()
            self.fail("expected an exception")
        except ObjectValidationError, ove:
            pass    
            print ove
            
            
    def test_choices(self):
        t = Thing()
        t.country = 'aa'
        try:
            t.full_clean()
            self.fail("expected an exception")
        except ObjectValidationError, ove:
            pass    
            print ove
                        
            
       
        
if __name__ == '__main__':
    main()    