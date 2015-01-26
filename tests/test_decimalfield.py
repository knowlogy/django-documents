import prepare_settings #@UnusedImport
        
from unittest import TestCase, main       
from django_documents.documents import DataAspect      
from django_documents import fields
from django_documents.serializer import XMLSerializer, XMLUnserializer, JsonSerializer,  JsonUnSerializer
from decimal import Decimal
       

class Data(DataAspect):       
    price = fields.DecimalField(max_digits = 5, decimal_places = 3)


       
class TestAbstractSuperclass(TestCase):
        
    def testSerializationJson(self):
        data = Data()     
        data.price = Decimal('12.555') 
        
        data.full_clean()
        
        json_str = JsonSerializer().serialize(data)
        print json_str
        
        uDate = JsonUnSerializer().unserialize(json_str)
    
        self.assertEqual(uDate.price, Decimal('12.555'))
        print uDate.price
           

        
if __name__ == '__main__':
    main()           