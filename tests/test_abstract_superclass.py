from test_serialization_default import BaseSerializationTestCase        
from unittest import main      
from django_documents.serializer import JsonSerializer, JsonUnSerializer, XMLSerializer, XMLUnserializer
from django_documents.documents import Model, DataAspect      
from django_documents import related
from django_documents import fields
       

class DataAspectClass(DataAspect):       
    name = fields.CharField()
       
       
class AbstractBaseClass(Model):       
    id = fields.CharField(max_length = 30)
    
    class Meta:
        abstract = True
        
class ChildClass(AbstractBaseClass):
    data = related.OneOf(DataAspectClass)
       
#test incorrect arguments

class ChildChildClass(ChildClass):
    lenght = fields.IntegerField()
       
class TestAbstractSuperclass(BaseSerializationTestCase):
    
    
    def setUp(self):
        self.instance = ChildClass(id = "121212")
        self.instance.data = DataAspectClass(name = "hello")
        self.ModelClass = ChildClass
    
    def check(self):
        self.assertEqual( self.instance.id, self.unser_instance.id)
        self.assertEqual( self.instance.data.name, self.unser_instance.data.name)
            
    
    def test_serialization_json(self):
        self._run_serialization(JsonSerializer, JsonUnSerializer) 
        self.check()
        
    
    
    def test_serialization_xml(self):
        self._run_serialization(XMLSerializer, XMLUnserializer) 
        self.check()

class TestSuperclass(BaseSerializationTestCase):
   
    def setUp(self):
        self.instance = ChildChildClass(id = "121212")
        self.instance.data = DataAspectClass(name = "hello")
        self.lenght = 10
        self.ModelClass = ChildChildClass
        
    def check(self):
        self.assertEqual( self.instance.id, self.unser_instance.id)
        self.assertEqual( self.instance.data.name, self.unser_instance.data.name)
        self.assertEqual( self.instance.lenght, self.unser_instance.lenght)
    
    def test_serialization_json(self):
        self._run_serialization(JsonSerializer, JsonUnSerializer) 
        self.check()
    
    
    def test_serialization_xml(self):
        self._run_serialization(XMLSerializer, XMLUnserializer) 
        self.check()
     

    
       
        
if __name__ == '__main__':
    main()           