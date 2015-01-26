import prepare_settings
        
from unittest import TestCase, main        
from django_documents.documents import Model
from django_documents import fields
from django_documents import related
from django_documents.register import get_model
from django_documents.utils import get_class

class Restaurant(Model):
    name = fields.CharField(max_length = 20, blank = False, null= False, verbose_name = {"nl": "Naam","de":"Name","en": "Name"})


    

class MetaDataTestCase(TestCase):

    def test_correct_serialization_meta_attributes(self):

        meta = Restaurant._meta.describe()
        print meta
        
class TestRunTimeCreationClass(TestCase):
    
    def create_clazz(self, json):
        pass
    
    
    def test_create_class(self):
        dynClass = type("test.DynamicType",(Model,), {'__module__' : "test" , 'text':fields.CharField()})
        a = dynClass()
        a.test = 'Hello'
        
        self.assertEquals('Hello', a.test)
        
        
    def test_create_class_structure(self):
        
        self.assertTrue(get_model("test.NewDynamicType") is None)
        
        dynClass = type("NewDynamicType",(Model,), {'__module__' : "test" , 'text':fields.CharField()})
        
        self.assertTrue(get_model("test.NewDynamicType") is not None)
        
        
        dynClass2 = type("NewDynamicType2",(Model,), {'__module__' : "test" , 'text':fields.CharField(), 'name': related.OneOf("test.NewDynamicType")})
        a = dynClass2()
        
        a.test = 'Hello'
        a.name = dynClass()           # note that we to create a class, think about how we have to create these
        a.name.test = "Hello again"
        
            
        self.assertEquals('Hello', a.test)
        self.assertEquals('Hello again', a.name.test)
        
        meta = dynClass2._meta.describe()
        print meta
                        
    def test_create_class_struction_with_stringnames(self):
        
        self.assertTrue(get_model("test.NewDynamicType") is None)
        
        attributes = {}
        clazz = get_class("persistent.fields.CharField")
        attributes['__module__'] = "test"
        attributes['text'] = clazz()
        
        
        #
        
        Role = type("Meta", (), {"name": {"nl": "Brug", "de": "Brcke"}, 'clazz' : Restaurant })
        attributes['Role'] = Role 
        
        
        dynClass2 = type("NewDynamicType2",(Model,), attributes)
        
        self.assertTrue(get_model("test.NewDynamicType2") is not None)
        self.assertTrue( dynClass2.Role.clazz is not None )
        
        instance = dynClass2()
        instance.test = "Hello"
            
if __name__ == '__main__':
    main()  