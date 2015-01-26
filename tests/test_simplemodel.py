import prepare_settings
        
from unittest import TestCase, main  

from django_documents import fields
from django_documents import documents as persistentmodels


class Person(persistentmodels.Model):
    """
    this is the definition of a simple model
    """
    first_name = fields.CharField()
    last_name = fields.CharField()     

class Duck(persistentmodels.Model):
    name = fields.CharField()


class TestAbstractSuperclass(TestCase):
    
    
    def test_simple_use(self):
        person = Person()
        person.first_name = "Baruch"
        person.last_name = "Spinoza"
        
        self.assertEqual("Baruch", person.first_name)
        self.assertEqual("Spinoza", person.last_name)
    
    def test_use_with_arguments(self):
        
        person = Person(first_name = "Baruch", last_name = "Spinoza")
        
        self.assertEqual("Baruch", person.first_name)
        self.assertEqual("Spinoza", person.last_name)
    
        person2 = Person(first_name = "Socrates", last_name = "OokSocrates")
        
        self.assertEqual("Socrates", person2.first_name)
        self.assertEqual("OokSocrates", person2.last_name)
    
            
    def test_default_value(self):
        test = Duck()
        test.name = "Socrates"
        self.assertEqual("Socrates", test.name)
            

        
if __name__ == '__main__':
    main()    