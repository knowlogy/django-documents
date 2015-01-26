import prepare_settings
        
from unittest import TestCase, main       
from django_documents.documents import DataAspect      
from django_documents import fields
from datetime import date
from django_documents.serializer import XMLSerializer, XMLUnserializer, JsonSerializer,  JsonUnSerializer
import datetime
       

class HistoricData(DataAspect):       
    annoDate = fields.DateTimeField()


       
class TestAbstractSuperclass(TestCase):
        
    def testSerializationJson(self):
        historicData = HistoricData()     
        historicData.annoDate = datetime.datetime(2013,5,22,10,30) 
        
        json_str = JsonSerializer().serialize(historicData)
        print json_str
        
        uHistoricSpot = JsonUnSerializer().unserialize(json_str)
    
        self.assertEqual(uHistoricSpot.annoDate, datetime.datetime(2013,5,22,10,30))
           

        
if __name__ == '__main__':
    main()           