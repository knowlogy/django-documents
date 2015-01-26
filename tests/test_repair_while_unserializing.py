import prepare_settings #@UnusedImport
        
from unittest import TestCase, main       
from django_documents.documents import Model      
from django_documents import fields, related
from django_documents.serializer import  JsonUnSerializer

       

class ModelA(Model):
    
    char = fields.CharField()
    integer = fields.IntegerField()
    
class ModelB(Model):
    char = fields.CharField()
    integer = fields.IntegerField()


class ModelContainer(Model):
    """
    This model has changed in definition
    """
    oneOf = related.OneOf(ModelB)  # changed from related.OneOf(ModelA)



class ChangeClazzHandler(object):
    """
    This handler changes the clazz from ModelA to ModelB
    """
    
    def __init__(self):
        self.has_changed = False
    
    
    def after_create_object(self, serializer, component_obj, one_of_field, clazz_name, clazz, instance, related_instance, obj_dict):
        pass
    
    def before_create_object(self, serializer, one_of_field, clazz_name, clazz, instance, related_instance, obj_dict):
        if isinstance(instance, ModelContainer) and issubclass(clazz, ModelA):
            clazz = ModelB
            obj_dict = obj_dict
            self.has_changed = True
            
            skip_this_field = False
            new_clazz = ModelB
            not_changed_data = obj_dict
            return skip_this_field, new_clazz, not_changed_data
        else:
            return False, None, None
           

       
class TestJsonWithClazzNameToRepair(TestCase):
        
    def testSerializationJson(self):

        # defini
        from django_documents.utils import get_fqclassname_forclass
        print get_fqclassname_forclass(ModelA)
                        
        json = '{"oneOf": {"char": "aa", "integer": 2, "_clazz": "test_repair_while_unserializing.ModelA"}, "_clazz": "test_repair_while_unserializing.ModelContainer"}'

        
        handler = ChangeClazzHandler()
        
        model_container = JsonUnSerializer().unserialize(json, handle_one_of_handler = handler)
        self.assertTrue( isinstance(model_container.oneOf, ModelB))
        self.assertTrue(handler.has_changed)
        
           

        
if __name__ == '__main__':
    main()  