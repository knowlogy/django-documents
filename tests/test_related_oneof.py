import prepare_settings
        
from unittest import TestCase, main        
from django_documents.serializer import PythonSerializer, PythonDeserializer,XMLSerializer, XMLUnserializer, JsonSerializer,  JsonUnSerializer
from django_documents import documents as models, fields, related
import types

class ModelWithOneOffField(models.Model):
    oneOf = related.OneOf(types.DictType)


class TestSerializationOneOfDictPython(TestCase):
    
    def testSerializationNoAttributeSetted(self):
        model = ModelWithOneOffField() 
        adict = PythonSerializer().serialize(model)
        
        self.assertEqual(adict['oneOf'], None)
       
    
    def testSerialization(self):
        model = ModelWithOneOffField() 
        model.oneOf = {"location": {"lat": 0.8, "lng": 0.9}, "name": "test", "elements": ['zirconicum', 'helium']}
       
        adict = PythonSerializer().serialize(model)
        self.assertEqual(adict['oneOf']["location"]["lat"], 0.8)
        self.assertEqual(adict['oneOf']["name"], "test")
        self.assertEqual(adict['oneOf']["elements"], ['zirconicum', 'helium'])
        
        unser_model = PythonDeserializer().unserialize(adict, ModelWithOneOffField)
    
        self.assertEqual(unser_model.oneOf, model.oneOf)

        
class BaseSerializationTestCase(TestCase):
       
    def checkModelWithAllBaseFields(self, instance, unser_instance):
        #self.assertEqual( instance.name, unser_instance.name)
        pass
        
    def checkModelWithOneOffField(self, instance, unser_instance):
        if instance.oneOf is not None:
            self.checkModelWithAllBaseFields(instance.oneOf, unser_instance.oneOf)
        
    def checkModelWithListOffStringType(self, instance, unser_instance):
        self.assertEqual( instance.name, unser_instance.name)
        if instance.listOfString is not None:
            for i in range(len(instance.listOfString)):
                self.assertEqual(instance.listOfString[i], unser_instance.listOfString[i])
                
    def _run_serialization(self, serializerClass, unserializerClass):
        serializer = serializerClass()
        unserializer = unserializerClass()            
        value = serializer.serialize(self.instance)
        print value
        self.unser_instance = unserializer.unserialize(value, self.ModelClass)

class TestModelWithBaseFieldsEmpty(BaseSerializationTestCase):

    def setUp(self):
        self.ModelClass = ModelWithOneOffField
        self.instance = ModelWithOneOffField()
        
    def test_son(self):
        self._run_serialization(JsonSerializer, JsonUnSerializer)                                
        self.checkModelWithAllBaseFields(self.instance, self.unser_instance)
    
    def test_xml(self):
        self._run_serialization(XMLSerializer, XMLUnserializer)
        self.checkModelWithAllBaseFields(self.instance, self.unser_instance)   
        

        
class TestModelWithBaseFieldsEmptySetted(BaseSerializationTestCase):
    
    def setUp(self):
        self.instance = ModelWithOneOffField()
        self.instance.oneOf =  {"location": {"lat": 0.8, "lng": 0.9}, "name": "test", "elements": ['zirconicum', 'helium']}
        self.ModelClass = ModelWithOneOffField
    
    
    def checkModelWithAllBaseFields(self, instance, unser_instance):
        self.assertEqual( instance.oneOf, unser_instance.oneOf)
    
        
    def test_filled_instance_xml(self):
        self._run_serialization(XMLSerializer, XMLUnserializer)
        self.checkModelWithAllBaseFields(self.instance, self.unser_instance)

    def test_filled_instance_json(self):
        self._run_serialization(JsonSerializer, JsonUnSerializer)                                
        self.checkModelWithAllBaseFields(self.instance, self.unser_instance)
        

        
        
if __name__ == '__main__':
    main()   