from unittest import TestCase, main  
import prepare_settings

from django_documents import fields
from django_documents import documents as persistentmodels
from django_documents.serializer import JsonSerializer, JsonUnSerializer

class Vehicle(persistentmodels.Model):
    name = fields.CharField()
    

class Registration(persistentmodels.Model):
    licenceNumber = fields.CharField()     
    
class Car(Vehicle):    
    type = fields.CharField()

class RegisteredCar(Car, Registration):
    pass



class MultiInheritanceTest(TestCase):

    def test_multipleInheritance(self):
        
        registerdCar = RegisteredCar(type = "test", name="mycar", licenceNumber = "we-we-we" )
        self.assertEqual("we-we-we", registerdCar.licenceNumber)
        self.assertEqual("test", registerdCar.type)

        ajson = JsonSerializer().serialize(registerdCar)
        
        unser_registerdCar = JsonUnSerializer().unserialize(ajson)
        self.assertEqual("we-we-we", unser_registerdCar.licenceNumber)
        self.assertEqual("test", unser_registerdCar.type)


        
if __name__ == '__main__':
    main() 