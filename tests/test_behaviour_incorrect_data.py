import prepare_settings #@UnusedImport
import types        
from unittest import TestCase, main       
from django_documents.documents import Model      
from django_documents import fields, related
from django_documents.serializer import  JsonUnSerializer, JsonSerializer


TYPE_SHOPPING_FACILITY  = [
    ("A", { "nl": u"a", "de": u"a", "en": u"a"}),
    ("B", { "nl": u"a", "de": u"a", "en": u"a"}),
    ("C", { "nl": u"a", "de": u"a", "en": u"a"}),
]    


class ShopFacility(Model):
    values = related.ListOf(types.StringType, choices = TYPE_SHOPPING_FACILITY, null = True, verbose_name = {"nl": u"Types"})
       
from django_documents.utils import get_fqclassname_forclass
       
class TestShowIgnoreIncorrectListOfValueUnserialization(TestCase):
        
    def testSerializationJson(self):
        
        json = '{"values": ["A", "B"], "_clazz": "test_behaviour_incorrect_data.ShopFacility"}'
        
        shopFacility = ShopFacility()    
        shopFacility.values = ['A','B','D'] # added a incorrect value, but it is ignored!!!
        shopFacility = JsonUnSerializer().unserialize(json)
        shopFacility.full_clean()
        
        self.assertFalse('D' in shopFacility.values)
            
           

        
if __name__ == '__main__':
    main()  