import prepare_settings
        
from unittest import TestCase, main       
from django_documents.documents import Model      
from django_documents import related
from django_documents import fields
from django_documents.serializer import JsonSerializer,  JsonUnSerializer
       
"""
class Category(Model):       
    name = fields.CharField()
    subcategories = related.ListOf('Category')

"""
from app.models import MyDjangomodel

class TestRecursiveDefinitionDjOneOf(TestCase):
    
    def test(self):

        mymodel = MyDjangomodel()
        mysecond_model = MyDjangomodel()
        mymodel.mymodel = mysecond_model
"""            
        

       
class TestRecursiveDefinitionListOf(TestCase):
    
    def test(self):

        slapen = Category(name="slapen")
        hotel = Category(name="hotel")
        slapen.subcategories = [hotel]
            
        json = JsonSerializer().serialize(slapen)
        retrieved_slapen = JsonUnSerializer().unserialize(json)
        
        self.assertEqual(slapen.name, retrieved_slapen.name)   
        self.assertEqual(slapen.subcategories[0].name, retrieved_slapen.subcategories[0].name)   

"""
class Mymodel(Model):       
#     mymodel = related.OneOf('Mymodel')
    id = fields.CharField(blank = False, null = False, max_length = 36, auto_created = True)
    site = fields.CharField(max_length = 40, blank = True, null = True)
    name = fields.CharField(max_length = 40)
    rootCategories = related.ListOf('Mymodel')


class TestRecursiveDefinitionOneOf(TestCase):
    
    def test(self):

        mymodel = Mymodel()
        mysecond_model = Mymodel()
        mymodel.mymodel = mysecond_model
            
        json = JsonSerializer().serialize(mymodel)
        retrieved_mymodel = JsonUnSerializer().unserialize(json)
        
    def test_describe(self):
        import simplejson as json
        print json.dumps(Mymodel._meta.describe(recursive=True))
        
      
        
if __name__ == '__main__':
    main()               