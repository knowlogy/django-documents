import prepare_settings
        
from unittest import TestCase, main        
from django_documents.serializer import PythonSerializer, PythonDeserializer,XMLSerializer, XMLUnserializer, JsonSerializer,  JsonUnSerializer
from datetime import date
from model_definitions_for_test import ModelWithAllBaseFields, ModelWithOneOffField, ModelWithListOffStringType, ModelWithFloatField       


class TestSerializationFloatPython(TestCase):
    
    def testSerializationNoAttributeSetted(self):
        model = ModelWithFloatField() 
        adict = PythonSerializer().serialize(model)
        
        self.assertEqual(adict['float'], None)
       
    
    def testSerializationFloat(self):
        model = ModelWithFloatField() 
        model.float = 4.56
       
        adict = PythonSerializer().serialize(model)
        unser_model = PythonDeserializer().unserialize(adict, ModelWithFloatField)
    
        self.assertEqual(unser_model.float, model.float)

class TestSerializationFloat(TestCase):
    
    def testSerializationFloat(self):
        model = ModelWithFloatField() 
        model.float = 4.56
       
        ajson = JsonSerializer().serialize(model)
        print ajson
        import simplejson as json
        
        dict =  json.loads(ajson)
        self.assertEqual(dict['float'], 4.56)
        
class BaseSerializationTestCase(TestCase):
       
    def checkModelWithAllBaseFields(self, instance, unser_instance):
        self.assertEqual( instance.date, unser_instance.date)
        self.assertEqual( instance.integer, unser_instance.integer)
        self.assertEqual( instance.char, unser_instance.char)
        self.assertEqual( instance.float, unser_instance.float)
    
    def checkModelWithOneOffField(self, instance, unser_instance):
        self.assertEqual( instance.name, unser_instance.name)
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
        self.ModelClass = ModelWithAllBaseFields
        self.instance = ModelWithAllBaseFields()
        
    def test_son(self):
        self._run_serialization(JsonSerializer, JsonUnSerializer)                                
        self.checkModelWithAllBaseFields(self.instance, self.unser_instance)
    
    def test_xml(self):
        self._run_serialization(XMLSerializer, XMLUnserializer)
        self.checkModelWithAllBaseFields(self.instance, self.unser_instance)   
        

        
class TestModelWithBaseFieldsEmptySetted(BaseSerializationTestCase):
    
    def setUp(self):
        self.instance = ModelWithAllBaseFields()
        self.instance.date = date(1968, 9, 17)
        self.instance.integer = 8
        self.instance.char  = 'ab'
        self.instance.float = 12.3
        self.ModelClass = ModelWithAllBaseFields
        
    def test_filled_instance_xml(self):
        self._run_serialization(XMLSerializer, XMLUnserializer)
        self.checkModelWithAllBaseFields(self.instance, self.unser_instance)

    def test_filled_instance_json(self):
        self._run_serialization(JsonSerializer, JsonUnSerializer)                                
        self.checkModelWithAllBaseFields(self.instance, self.unser_instance)
        

class TestModelWithOneOffFieldEmpty(BaseSerializationTestCase):
    
    def setUp(self):
        self.ModelClass = ModelWithOneOffField
        self.instance = self.ModelClass()
    
    def test_empty_instance_xml(self):
        self._run_serialization(XMLSerializer, XMLUnserializer)
        self.checkModelWithOneOffField(self.instance, self.unser_instance)
        
    def test_empty_instance_json(self):
        self._run_serialization(JsonSerializer, JsonUnSerializer)          
        self.checkModelWithOneOffField(self.instance, self.unser_instance)       
        
class TestModelWithOneOffFieldSetted(BaseSerializationTestCase):
        
    def setUp(self):
        self.ModelClass = ModelWithOneOffField
        self.instance = ModelWithOneOffField()
        self.instance.name = "test"
        self.instance.oneOf = ModelWithAllBaseFields()
        self.instance.oneOf.date = date(1968, 9, 17)
        self.instance.oneOf.integer = 8
        self.instance.oneOf.char  = 'ab'
        self.instance.oneOf.float = 12.3
        
    def test_filled_instance_xml(self):
        self._run_serialization(XMLSerializer, XMLUnserializer)
        self.checkModelWithOneOffField(self.instance, self.unser_instance)    

    def test_filled_instance_json(self):
        self._run_serialization(JsonSerializer, JsonUnSerializer)          
        self.checkModelWithOneOffField(self.instance, self.unser_instance)            
        

class TestModelWithListOffStringTypeEmpty(BaseSerializationTestCase):
    
    def setUp(self):
        self.ModelClass = ModelWithListOffStringType
        self.instance = ModelWithListOffStringType()
        
    def test_empty_instance_xml(self):
        self._run_serialization(XMLSerializer, XMLUnserializer)         
        self.checkModelWithListOffStringType(self.instance, self.unser_instance)
        
    def test_empty_instance_json(self):
        self._run_serialization(JsonSerializer, JsonUnSerializer)          
        self.checkModelWithListOffStringType(self.instance, self.unser_instance)
   
            

class TestModelWithListOffStringTypeSetted(BaseSerializationTestCase):

    def setUp(self):
        self.ModelClass = ModelWithListOffStringType
        self.instance = ModelWithListOffStringType()
        self.instance.name = 'test'
        self.instance.listOfString = [u"a", u"b"]
        

    def test_filled_instance_xml(self):
        self._run_serialization(XMLSerializer, XMLUnserializer)   
        self.checkModelWithListOffStringType(self.instance, self.unser_instance)

    def test_filled_instance_json(self):
        self._run_serialization(JsonSerializer, JsonUnSerializer)   
        self.checkModelWithListOffStringType(self.instance, self.unser_instance)

from model_definitions_for_test import ModelWithListModelWithAllBaseFields

class ModelWithListModelWithAllBaseFieldsSetted(BaseSerializationTestCase):

    def setUp(self):
        self.ModelClass = ModelWithListModelWithAllBaseFields
        self.instance = ModelWithListModelWithAllBaseFields()
        self.instance.name = 'test'
        self.instance.listOf = []
        
        item = ModelWithAllBaseFields()
        item.date = date(1968, 9, 17)
        item.integer = 1
        item.char  = 'een'
        item.float = 12.3
        self.instance.listOf.append(item) 

        
        item2 = ModelWithAllBaseFields()
        item2.date = date(1969, 9, 17)
        item2.integer = 2
        item2.char  = 'twee'
        item2.float = 4.56
        
        self.instance.listOf.append(item2) 

    
    def check(self):
        self.assertEqual( self.instance.name, self.unser_instance.name)
        if self.instance.listOf is not None:
            for i in range(len(self.instance.listOf)):
                self.assertTrue( self.instance.listOf[i] is not None)
                self.assertTrue( self.unser_instance.listOf[i] is not None)
                self.checkModelWithAllBaseFields(self.instance.listOf[i], self.unser_instance.listOf[i])
        

    def test_filled_instance_xml(self):
        self._run_serialization(XMLSerializer, XMLUnserializer)   
        self.check()

    def test_filled_instance_json(self):
        self._run_serialization(JsonSerializer, JsonUnSerializer)   
        self.check()



from model_definitions_for_test import ModelWithMapOffStringType, ModelWithMapModelWithAllBaseFields

class ModelWithMapOffStringTypeEmpty(BaseSerializationTestCase):

    def setUp(self):
        self.ModelClass = ModelWithMapOffStringType
        self.instance = ModelWithMapOffStringType()
        self.instance.mapOf["nl"] = "Nederlands"
        self.instance.mapOf["de"] = "Deutch"
        self.instance.mapOf["en"] = "English"
        
        

    def check(self):
        self.assertTrue(self.unser_instance.mapOf is not None)
        self.assertTrue( "nl" in self.unser_instance.mapOf)
        self.assertEqual("Nederlands", self.unser_instance.mapOf["nl"])
        self.assertEqual("Deutch", self.unser_instance.mapOf["de"])
        self.assertEqual("English", self.unser_instance.mapOf["en"])
        

    def test_serialization_xml(self):
        self._run_serialization(XMLSerializer, XMLUnserializer)   
        self.check()

    def test_serialization_json(self):
        self._run_serialization(JsonSerializer, JsonUnSerializer)   
        self.check()
        
        
class ModelWithMapOffStringTypeFilled(BaseSerializationTestCase):

    def setUp(self):
        self.ModelClass = ModelWithMapOffStringType
        self.instance = ModelWithMapOffStringType()

    def check(self):
        self.assertEqual( self.instance.name, self.unser_instance.name)
        if self.instance.mapOf is not None:
            for key, value in self.instance.mapOf:
                self.assertTrue( key in self.unser_instance.mapOf)
                self.assertEqual(value, self.unser_instance.mapOf[key])

    def test_serialization_xml(self):
        self._run_serialization(XMLSerializer, XMLUnserializer)   
        self.check()

    def test_serialization_json(self):
        self._run_serialization(JsonSerializer, JsonUnSerializer)   
        self.check()        

class ModelWithModelWithMapModelWithAllBaseFieldsSetted(BaseSerializationTestCase):

    def setUp(self):
        self.ModelClass = ModelWithMapModelWithAllBaseFields
        self.instance = ModelWithMapModelWithAllBaseFields()
        self.instance.name = "test"
        self.instance.mapOf['een']  =  ModelWithAllBaseFields(date = date(1968, 9, 17), integer = 1, char  = 'een', float = 12.3)
        self.instance.mapOf['twee'] =  ModelWithAllBaseFields(date = date(1969, 9, 17), integer = 2, char  = 'twee', float = 14.3)

    def check(self):
        self.assertEqual( self.instance.name, self.unser_instance.name)
        if self.instance.mapOf is not None:
            for key, value in self.instance.mapOf.items():
                self.assertTrue( key in self.unser_instance.mapOf)
                self.checkModelWithAllBaseFields(value, self.unser_instance.mapOf[key])

    def test_serialization_xml(self):
        self._run_serialization(XMLSerializer, XMLUnserializer)   
        self.check()

    def test_serialization_json(self):
        self._run_serialization(JsonSerializer, JsonUnSerializer)   
        self.check()

from model_definitions_for_test import Party, ContactInfo

class TestSerialisationNonExistingRelation(TestCase):

    def test(self):
        file  = open('../tests/fixtures/test_with_notexisting_attribute.json')
        json = file.read()
        party = JsonUnSerializer().unserialize(json, Party)
        
        self.assertEquals("test", party.name)

        
        
if __name__ == '__main__':
    main()   