"""
Module for abstract serializer/unserializer base classes.
"""

from StringIO import StringIO

from django.utils.encoding import smart_unicode
from django.utils import datetime_safe
from elementtree.SimpleXMLWriter import XMLWriter
from elementtree.ElementTree import parse

from .related import OneOnOneRelation, MapRelation, ListRelation
from .utils import get_fqclassname_forclass, get_fqclassname_forinstance, get_class


CLAZZ = '_clazz'
DYNAMIC_ATTRIBUTES = '_dynamic_attributes'


def get_serialized_field_value(obj, field):
        
    value = field._get_val_from_obj(obj)        
    # Protected types (i.e., primitives like None, numbers, dates,
    # and Decimals) are passed through as is. All other values are
    # converted to string first.
    if not is_protected_type(value):
        value = field.value_to_string(obj)
    return value    

class SerializationError(Exception):
    """Something bad happened during serialization."""
    pass

class DeserializationError(Exception):
    """Something bad happened during deserialization."""
    pass



class ObjectValidationError(Exception):
    """An error while validating data."""
    def __init__(self, dict):
        """
        ValidationError can be passed any object that can be printed (usually
        a string), a list of objects or a dictionary.
        """
        self.dict = dict

class Serializer(object):
    """
    Abstract serializer base class.
    """

    # Indicates if the implemented serializer is only available for
    # internal Django use.
    internal_use_only = False

    def serialize(self, obj, **options):
        """
        Serialize a queryset.
        """
        self.options = options

        self.stream = options.get("stream", StringIO())
        
        self.start_serialization()
        self.serialize_object( obj)
        self.end_serialization()
        return self.getvalue()
    
    
    def serialize_object(self, obj):
        self.start_object(obj)
        self.handle_object(obj)
        self.end_object(obj)
    
    
    
        

    def get_string_value(self, obj, field):
        """
        Convert a field's value to a string.
        """
        return smart_unicode(field.value_to_string(obj))

    def start_serialization(self):
        """
        Called when serializing of the queryset starts.
        """
        raise NotImplementedError

    def end_serialization(self):
        """
        Called when serializing of the queryset ends.
        """
        pass



    def getvalue(self):
        """
        Return the fully  (or None if the output stream is
        not seekable).
        """
        if callable(getattr(self.stream, 'getvalue', None)):
            return self.stream.getvalue()

        
        
        
from django.utils.encoding import is_protected_type

class ModelVisitor(object):
    """
    defines the interface of a model visitor
    """
    def start_handle_object(self, instance):
        pass
            
    def end_handle_object(self, instance):
        pass
        
    
    def handle_field(self, field, instance):
        pass
  
    def handle_one_of(self, one_of_field, related_instance):
        pass   
            
    def handle_list_of(self, list_of_field, instance):
        pass
  
    def handle_map_of(self, map_of_relation, instance):
        pass

    def handle_dynamic_field(self, name, value):
        pass
    
from copy import deepcopy 
import types
        
class PythonSerializerVisitor(ModelVisitor):
    
    def __init__(self, **options):
        self.options = options
        self.object_dict = {}
        self.current_dict = self.object_dict
        self.ignoreMissingAttributes = self.options.get('ignoreMissingAttributes',False)
        
        
    def start_handle_object(self, instance):
        c = CLAZZ # when using object_dict[CLAZZ] it goes wrong !? 
        from utils import get_fqclassname_forinstance
        self.current_dict[c] = get_fqclassname_forinstance(instance)
    
        if getattr(instance, '_errors', None) is not None:
            self.current_dict['_errors'] = getattr(instance, '_errors',None)
    
    def handle_field(self, field, instance):
        try:
            value = field._get_val_from_obj(instance)
            # Protected types (i.e., primitives like None, numbers, dates,
            # and Decimals) are passed through as is. All other values are
            # converted to string first.
            if is_protected_type(value):
                self.current_dict[field.name] = value
            else:
                self.current_dict[field.name] = field.value_to_string(instance)
        except AttributeError:
            if not self.ignoreMissingAttributes:
                raise    

            
    def handle_one_of(self, one_of_field, instance, related_instance):
        if one_of_field.rel.to == types.DictType:
            self.current_dict[one_of_field.name] = related_instance
        else:
            #create new visitor to visit values
            if related_instance is not None:        
                python_serializer_visitor = PythonSerializerVisitor(**self.options)
                related_instance.visit(python_serializer_visitor)
                self.current_dict[one_of_field.name] =  python_serializer_visitor.get_dict()
            
        # or use same visitor
        """
        self.previous_dict = self.current_dict
        self.current_dict = {}                  # this 2 statements this could be the start_object 
        related_instance.visit(self)
        self.previous_dict[one_of_field.name] = self.current_dict #this 2 statements could be the end_object
        self.current_dict = self.previous_dict
        """   
            
    def handle_list_of(self, list_of_field, instance):
        related = getattr(instance, list_of_field.name)
        if related is not None:
            if list_of_field.rel.contains_built_in_type:
                related_list = deepcopy(related)
            else:    
                related_list = []
                for item in related:
                    python_serializer_visitor = PythonSerializerVisitor(**self.options)
                    item.visit(python_serializer_visitor)
                    related_list.append( python_serializer_visitor.get_dict() )
                            
            self.current_dict[list_of_field.name] = related_list
  
    def handle_map_of(self, map_of_relation, instance):
        original_dict = getattr(instance, map_of_relation.name)
        new_dict = {}
        for key, value in original_dict.items():
            if map_of_relation.rel.contains_built_in_type:
                new_dict[key] = deepcopy(value)
            else:
                python_serializer_visitor = PythonSerializerVisitor(**self.options)
                value.visit(python_serializer_visitor)
                new_dict[key] = python_serializer_visitor.get_dict()  
                
        self.current_dict[map_of_relation.name] = new_dict

    def handle_dynamic_field(self, name, value):
        python_serializer_visitor = PythonSerializerVisitor(**self.options)
        value.visit(python_serializer_visitor) 
        self.current_dict[name] = python_serializer_visitor.get_dict()        

            
    def get_dict(self):
        return self.object_dict        
            
class PythonSerializer(Serializer):


    def start_serialization(self):
        self.root_object_dict = None;
        
    
    def end_serialization(self):
        if 'root_name' in self.options and self.options['root_name'] != "":
            object_dict = self.root_object_dict
            self.root_object_dict = {}
            self.root_object_dict[self.options['root_name']] = object_dict
        
     
    def serialize_object(self, obj_or_list):

        if isinstance(obj_or_list, list):
            self.root_object_dict = []
            for obj in obj_or_list:
                obj_dict = self._serialize_object(obj)
                self.root_object_dict.append(obj_dict)
        elif isinstance(obj_or_list, dict):
            self.root_object_dict = {}
            for key, value in obj_or_list.items():
                self.root_object_dict[key] = value     
        else:
            self.root_object_dict = self._serialize_object(obj_or_list)
    
    def _serialize_object(self, instance):
        python_serializer_visitor = PythonSerializerVisitor(**self.options)
        instance.visit(python_serializer_visitor)
        return python_serializer_visitor.get_dict()
    
    
    def getvalue(self):
        return self.root_object_dict
    
from django.core import exceptions

class PythonDeserializerVisitor(ModelVisitor):
                
    def __init__(self, dict, **options):
        self.root_dict = dict
        self.current_dict = self.root_dict
        self.options = options
        self.clazz_factory = options['class_factory'] if options and  'class_factory' in options else None            
        self.one_of_handler = self.options['handle_one_of_handler'] if 'handle_one_of_handler' in self.options else None
    
    
    def _optional_convert_to_subclazz(self, clazz, obj_dict):
        if self.clazz_factory and clazz in self.clazz_factory:
            return self.clazz_factory[clazz](clazz, obj_dict)
        else:
            return clazz    
        
    
    def add_error(self, field, value_dict, e):
        field._invalid = True    
        if not '_errors' in value_dict:
            value_dict['_errors'] = {}
        if not field.name in value_dict['_errors']:
            value_dict['_errors'][field.name] = []
        value_dict['_errors'][field.name].append(e.messages) 
    
    def convert_date_field_value(self, str_value):
        year, month, day = map(int, str_value.split('-'))
        try:
            return datetime.date(year, month, day)
        except ValueError:
                raise exceptions.ValidationError("Value [%s]is incorrect date format " % str_value)
    
    def set_field_value(self, field, instance, value_dict):
        value = value_dict[field.name]
        try:
            if value is not None:
                if field.get_internal_type() == 'DateField':
                    value = self.convert_date_field_value(value)
                else:
                    value = field.to_python(value)    
            setattr(instance, field.name, value)
        except exceptions.ValidationError, e:
            self.add_error(field, value_dict, e)
            
    def start_handle_object(self, instance):
        from .fields import FieldDoesNotExist 
        from utils import get_class
        from .documents import DynamicModel
        
        # instead of using handle_field (we ignore it), iterate through values, so we can use FieldDoesNotExist for dynamic fields
        for name, value in self.current_dict.items():
            if name == CLAZZ:
                continue
            if name == '_errors':
                setattr(instance,'_errors', value)
                continue
        
            try:
                field = instance._meta.get_field(name)
                if field.serialize:
                    if field.rel is None:
                        self.set_field_value(field, instance, self.current_dict)
                    #else:
                        #field.rel.add_to_instance(instance, dict, self)
                            
                        
            except FieldDoesNotExist:
                "its could be a dynamic field"
                if issubclass( instance.__class__, DynamicModel):
                    if CLAZZ in value:
                        clazz_name = value[CLAZZ]
                        clazz = get_class(clazz_name)
                        
                        child_instance = self._create_object(clazz, value)
                        instance.add_dynamic_attribute(name, child_instance)

    def _create_object(self, clazz, value_dict):
        instance = clazz()
        python_deserializer_visitor = PythonDeserializerVisitor(value_dict, **self.options)
        instance.visit(python_deserializer_visitor)
        return instance                    
    
    def handle_one_of(self, one_of_field, instance, related_instance):
        from utils import get_class
        
        if one_of_field.name in self.current_dict:
            obj_dict = self.current_dict[one_of_field.name]
            clazz = one_of_field.rel.to
            # check for clazz info
            component_obj = None
            if obj_dict is not None: 
                if '_clazz' in obj_dict:
                    clazz_name = obj_dict["_clazz"]
                    clazz = get_class(clazz_name)
                else:
                    clazz = self._optional_convert_to_subclazz(clazz, obj_dict)
                    clazz_name = None
                skip = False
                if self.one_of_handler:
                    skip, clazz, obj_dict = self.one_of_handler.before_create_object(self, one_of_field, clazz_name, clazz, instance, related_instance, obj_dict)
                if not skip:     
                    if one_of_field.rel.to == types.DictType:
                        component_obj = obj_dict
                    else:                           
                        component_obj = self._create_object(clazz, obj_dict)
                        if self.one_of_handler:
                            self.one_of_handler.after_create_object(self, component_obj, one_of_field, clazz_name, clazz, instance, related_instance, obj_dict)
            setattr(instance, one_of_field.name, component_obj)
            
    def handle_list_of(self, list_of_field, instance):
        from utils import get_class
        if list_of_field.name in self.current_dict:
            expected_list = self.current_dict[list_of_field.name]
            
            if expected_list is not None:
            
                clazz = list_of_field.rel.to
                    
                # TODO check for list
                if list_of_field.rel.contains_built_in_type:
            
                    new_list = []
                    for item in expected_list:
                        new_list.append(clazz(item))
                    setattr(instance, list_of_field.name, new_list)
                else:
                    clazz = list_of_field.rel.to
                    new_list = []
                    for item in expected_list:
                        if "_clazz" in item:
                            clazz_name = item['_clazz']
                            clazz = get_class(clazz_name)
                        
                        new_list_instance = self._create_object(clazz, item)
                        new_list.append(new_list_instance)
                    setattr(instance, list_of_field.name, new_list)

  
    def handle_map_of(self, map_of_relation_field, instance):
        if map_of_relation_field.name in self.current_dict:
            dict = self.current_dict[map_of_relation_field.name]
            clazz = map_of_relation_field.rel.to
            
            obj_dict = {}
            if map_of_relation_field.rel.contains_built_in_type:
                for key, value in dict.items():
                    obj_dict[key] = clazz(value)
            else:
                for key, value in dict.items():
                    new_map_instance = self._create_object(clazz, value) 
                    obj_dict[key] = new_map_instance
            setattr(instance, map_of_relation_field.name, obj_dict)     
            

    
class PythonDeserializer(object):

    
    def _unserialize(self, dict, clazz = None, **options):
        from utils import get_class
 
        
        if not clazz:
            assert CLAZZ in dict, "Expected a clazz-description in dictionary"
            clazz_name = dict[CLAZZ]
            clazz = get_class(clazz_name)
        obj = clazz()
    
        python_deserializer_visitor = PythonDeserializerVisitor(dict, **options)
        obj.visit(python_deserializer_visitor)
        return obj 

        
    def unserialize(self, dict, clazz = None, **options):
        
        self._invalid = False
        obj = self._unserialize(dict, clazz, **options)
                            
        if self._invalid:                
            raise ObjectValidationError(dict)             
        return obj 
    
    def unserialize_to_instance(self, dict, instance, **options):
        
        self._invalid = False
        
        python_deserializer_visitor = PythonDeserializerVisitor(dict, **options)
        instance.visit(python_deserializer_visitor)
                            
        if self._invalid:                
            raise ObjectValidationError(dict)             
        return instance 
    
    
    def unserializeMap(self, dict, clazz = None, contains_built_in_type = False, **options):
        
        map = {}  
        for key, value in dict.items():
            if contains_built_in_type:
                obj = clazz(value)
            else:    
                obj = self.unserialize(value, clazz, **options)
            map[key] = obj
        return map            

    def unserializeList(self, provided_list, clazz = None,contains_built_in_type = False,  **options):
        
        list = []  
        for value in provided_list:
            if contains_built_in_type:
                obj = clazz(value)
            else:   
                obj = self.unserialize(value, clazz, **options)
            list.append(obj)
        return list  


import simplejson
import datetime
import decimal

class JsonSerializer(PythonSerializer):
    """
    Convert a queryset to JSON.
    """
    internal_use_only = False

    def end_serialization(self):
        super(JsonSerializer,self).end_serialization()
        self.options.pop('stream', None)
        self.options.pop('fields', None)
        self.options.pop('use_natural_keys', None)
        self.options.pop('root_name', None)
        
        simplejson.dump(self.root_object_dict, self.stream, cls=DjangoJSONEncoder, **self.options)

    def getvalue(self):
        if callable(getattr(self.stream, 'getvalue', None)):
            return self.stream.getvalue()

class XMLDeserializerVisitor(ModelVisitor):
                
    def __init__(self, element):
        self.root_element = element
        self.current_element = self.root_element            
    
    
    def add_error(self, field, element, e):
        field._invalid = True    
        #if not '_errors' in value_dict:
        #    value_dict['_errors'] = {}
        #if not field.name in value_dict['_errors']:
        #    value_dict['_errors'][field.name] = []
        #value_dict['_errors'][field.name].append(e.messages) 
    
    def convert_date_field_value(self, str_value):
        year, month, day = map(int, str_value.split('-'))
        try:
            return datetime.date(year, month, day)
        except ValueError:
                raise exceptions.ValidationError("Value [%s]is incorrect date format " % str_value)
    
    def set_field_value(self, field, instance, child_element):
        value = child_element.text
        try:
            if value is not None:
                if field.get_internal_type() == 'DateField':
                    value = self.convert_date_field_value(value)
                else:
                    value = field.to_python(value)    
            setattr(instance, field.name, value)
        except exceptions.ValidationError, e:
            self.add_error(field, child_element, e)
    
        # serialization functions
    def unserialize_from_xml(self, field, instance, element):
        element_name = field.xml_element_name if field.xml_element_name else field.name  
        field_element = element.find(element_name)
        if not field_element is None:
            value = field_element.text
            setattr(instance, field.name, field.to_python(value))
            
    def start_handle_object(self, instance):
        pass


    
    def handle_field(self, field, instance):
        if field.serialize:
            element_name = field.xml_element_name
            field_element = self.current_element.find(element_name)
            if not field_element is None:
                self.set_field_value(field, instance, field_element)

    def _create_object(self, clazz, element):
        if len( clazz.__subclasses__()) > 0:
            # has subclass, use the type attribute for getting classname
            clazz_name = element.attrib['type']
            clazz = get_class(clazz_name)

        instance = clazz()
        python_deserializer_visitor = XMLDeserializerVisitor(element)
        instance.visit(python_deserializer_visitor)
        return instance                    
    
    
    def _create_from_element(self, name, clazz):
        element = self.current_element.find(name)
        if element:
            component_obj = self._create_object(clazz, element)
            return component_obj
        else:
            return None 

    def _get_value(self, text):
        try:
            text = float(text)
        except:
            try:
                text = int(text)
            except:
                pass        
        return text

    def _create_dict(self, name):
        
        def write_key_value(result, elements):
            for child in elements:
                if child.tag == "element":
                    name = child.attrib['name']
                    child_list = list(child)
                    if len(child_list) > 0:
                        result[name] = {}
                        write_key_value(result[name], child_list)
                    else:
                        value = self._get_value(child.text)
                        result[name] = value
                elif child.tag == "list":
                    name = child.attrib['name']
                    result[name] = []
                    child_list = list(child)
                    write_key_value(result[name], child_list)
                elif child.tag == "item":
                    child_list = list(child)
                    if len(child_list) > 0:
                        value = {}
                        result.append(value)
                        self.write_key_value(value, child_list)
                    else:
                        # append values from list        
                        value = self._get_value(child.text)
                        result.append(value)
                    
                
        element = self.current_element.find(name)
        if element:
            result = {}
            write_key_value(result, list(element))
            return result
        else:
            return None
        
            
            
    def handle_one_of(self, one_of_field, instance, related_instance):
        clazz = one_of_field.rel.to
        name = one_of_field.name
        if clazz == types.DictType:
            component_obj = self._create_dict(name)
        else:    
            component_obj = self._create_from_element(name, clazz)
        if component_obj:
            setattr(instance, one_of_field.name, component_obj)
        
            
    def handle_list_of(self, list_of_field, instance):
        element_name = list_of_field.xml_element_name if list_of_field.xml_element_name else list_of_field.name
        list_elements = self.current_element.find(element_name )
        if list_elements:
            new_list = []
            clazz = list_of_field.rel.to
            if list_of_field.rel.contains_built_in_type:
                for element in list_elements.getchildren():
                    new_list.append(clazz(element.text))
            else:
                for element in list_elements.getchildren():
                    new_list_instance = self._create_object(clazz, element)
                    new_list.append(new_list_instance)
            setattr(instance, list_of_field.name, new_list)

    def handle_map_of(self, map_of_relation_field, instance):
        map_element = self.current_element.find(map_of_relation_field.name)
        if map_element:
            obj_dict = {}
            clazz = map_of_relation_field.rel.to
            for element in map_element.getchildren():
                key =  element.attrib[map_of_relation_field.rel.xml_key_attr_name]
                if map_of_relation_field.rel.contains_built_in_type:
                    obj_dict[key] = clazz(element.text)
                else:
                    new_map_instance = self._create_object(clazz, element) 
                    obj_dict[key] = new_map_instance
            setattr(instance, map_of_relation_field.name, obj_dict)


class XMLUnserializer():

    def _unserialize(self, element, clazz):
        obj = clazz()
        xml_deserializer_visitor = XMLDeserializerVisitor(element)
        obj.visit(xml_deserializer_visitor)
        return obj 

    def unserialize(self, stream_or_string, clazz = None, **options):
        if isinstance(stream_or_string, basestring):
            stream = StringIO(stream_or_string)
        else:
            stream = stream_or_string
    
        root_element = parse(stream)
        
        if not clazz:
            clazz_element  = root_element.find(CLAZZ)
            assert not clazz_element is None, "expected to find a clazz element or a supplied clazz"
            clazz_name = root_element.text
            clazz = get_class(clazz_name)
        return self._unserialize(root_element.getroot(), clazz)    
            
    
class JsonUnSerializer():
    
    def unserialize(self, stream_or_string, clazz = None, **options):
        if isinstance(stream_or_string, basestring):
            stream = StringIO(stream_or_string)
        else:
            stream = stream_or_string
        
        return PythonDeserializer().unserialize(simplejson.load(stream), clazz, **options)
       

    def unserializeMap(self, stream_or_string, clazz = None,contains_built_in_type = False,  **options):
        if isinstance(stream_or_string, basestring):
            stream = StringIO(stream_or_string)
        else:
            stream = stream_or_string
        
        return PythonDeserializer().unserializeMap(simplejson.load(stream), clazz,contains_built_in_type, **options)
       
    def unserializeList(self, stream_or_string, clazz = None,contains_built_in_type = False,  **options):
        if isinstance(stream_or_string, basestring):
            stream = StringIO(stream_or_string)
        else:
            stream = stream_or_string
        
        return PythonDeserializer().unserializeList(simplejson.load(stream), clazz,contains_built_in_type, **options)
        
def contains_related_field_subclasses(related_field):
    clazz = related_field.rel.to
    return len( clazz.__subclasses__()) > 0
    


class XMLSerializerVisitor(ModelVisitor):
    
    def __init__(self, xmlwriter):
        self.xmlwriter = xmlwriter 
        
        
    def handle_field(self, field, instance):
        if field.serialize:
            value = get_serialized_field_value(instance, field)    

            if value is not None:
                self.xmlwriter.start(field.xml_element_name, field.meta)
                self.xmlwriter.data(unicode(value))
                self.xmlwriter.end() 

    def write_value(self, value, name = None):
        if isinstance(value, types.DictType):
            self.xmlwriter.start("element", {"name": name})
            self.write_dict(value)
            self.xmlwriter.end()
        elif isinstance(value, types.ListType):
            self.xmlwriter.start("list", {"name": name})
            self.write_list(value)
            self.xmlwriter.end()
        else:           
            if name:
                self.xmlwriter.start("element", {"name": name})
            else:
                self.xmlwriter.start("item")    
            self.xmlwriter.data(unicode(value))
            self.xmlwriter.end()
                
    def write_list(self, list):
        for item in list:
            self.write_value(item)    
                       

    def write_dict(self, related_instance):
        for key, value in related_instance.iteritems():
            name = key
            self.write_value(value, name)           
            

    def handle_one_of(self, one_of_field,instance, related_instance):
        if related_instance is not None:
            #if one_of_field.rel.xml_name_use_relation_class:
            element_name = one_of_field.name
            attributes = {}
            if one_of_field.meta:
                attributes.update(one_of_field.meta)
            if contains_related_field_subclasses(one_of_field):
                attributes.update({"type": get_fqclassname_forinstance(related_instance)})
                if one_of_field.rel.to == types.DictType:
                    attributes.update({"type": "dict"})                             
            self.xmlwriter.start(element_name, attributes)
            if one_of_field.rel.to == types.DictType:
                self.write_dict(related_instance)
            else:    
                related_instance.visit(self)
            self.xmlwriter.end()  
            
    def handle_list_of(self, list_of_field, instance):
        related = getattr(instance, list_of_field.name)
        if related is not None:
            if list_of_field.rel.contains_built_in_type:
                self.xmlwriter.start(list_of_field.name)
                for item in related:
                    self.xmlwriter.start(list_of_field.rel.xml_element_name)
                    self.xmlwriter.data(unicode(item))
                    self.xmlwriter.end()
                self.xmlwriter.end()    
            else:            
                has_subclasses = contains_related_field_subclasses(list_of_field)
                element_name = list_of_field.xml_element_name if list_of_field.xml_element_name else list_of_field.name
                self.xmlwriter.start(element_name)
                for item in related:
                    element_name = item._meta.xml_element_name
                    attributes = {}
                    if has_subclasses: 
                        attributes.update({"type" :get_fqclassname_forinstance(item)}) 
                    self.xmlwriter.start(element_name, attributes)
                    item.visit(self)
                    self.xmlwriter.end()    
                self.xmlwriter.end() 
  
    def handle_map_of(self, map_of_relation, instance):
        original_dict = getattr(instance, map_of_relation.name)
        self.xmlwriter.start(map_of_relation.name)
        has_subclasses = contains_related_field_subclasses(map_of_relation)
        for key, value in original_dict.items():
            if map_of_relation.rel.contains_built_in_type:
                self.xmlwriter.start(map_of_relation.rel.xml_element_name, {map_of_relation.rel.xml_key_attr_name: key})
                self.xmlwriter.data(unicode(value))
                self.xmlwriter.end()
            else:
                attributes = {map_of_relation.rel.xml_key_attr_name: key}
                if has_subclasses: 
                    attributes.update({"type" :get_fqclassname_forinstance(value)})
                self.xmlwriter.start(map_of_relation.rel.xml_element_name, attributes)
                value.visit(self)
                self.xmlwriter.end()
        self.xmlwriter.end
                
            
    def handle_dynamic_field(self, name, value):
        pass
            
    def get_dict(self):
        return self.object_dict 
   
class XMLSerializer(Serializer):
    """
    """

    internal_use_only = True

    def serialize(self, obj, **options):
        """
        """
        self.options = options
        self.stream = options.get("stream", StringIO())
        self.xmlwriter = XMLWriter( self.stream)
        self.start_serialization(obj)
        self.serialize_object( obj)
        self.end_serialization( obj)
        return self.getvalue()

    
    def start_serialization(self, obj):
        
        if 'root_name' in self.options and self.options['root_name'] != "":
            self.xml = self.xmlwriter.start(self.options['root_name'])
        else:
            self.xml = self.xmlwriter.start(obj._meta.xml_element_name)    
        
    def end_serialization(self, obj): 
        
        self.xmlwriter.close(self.xml)
        
     
    def serialize_object(self, instance):
        xml_visitor = XMLSerializerVisitor(self.xmlwriter)
        instance.visit(xml_visitor)
   

class DjangoJSONEncoder(simplejson.JSONEncoder):
    """
    JSONEncoder subclass that knows how to encode date/time and decimal types.
    """

    DATE_FORMAT = "%Y-%m-%d"
    TIME_FORMAT = "%H:%M:%S"

    def default(self, o):
        if isinstance(o, datetime.datetime):
            d = datetime_safe.new_datetime(o)
            return d.strftime("%s %s" % (self.DATE_FORMAT, self.TIME_FORMAT))
        elif isinstance(o, datetime.date):
            d = datetime_safe.new_date(o)
            return d.strftime(self.DATE_FORMAT)
        elif isinstance(o, datetime.time):
            return o.strftime(self.TIME_FORMAT)
        elif isinstance(o, decimal.Decimal):
            return str(o)
        else:
            return super(DjangoJSONEncoder, self).default(o)

# Older, deprecated class name (for backwards compatibility purposes).
DateTimeAwareJSONEncoder = DjangoJSONEncoder



def create_key_jsonvalue_dict(obj, exclude = None):
    """
    
    
    TODO maybe make this method a method from the model
    """    
    from .documents import DynamicModel

    
    key_jsonvalue_dict = {}      
    for field in  obj._meta.local_fields:
        
        if exclude and field.name in exclude:
            continue
        
        aspect_name = field.name
        if field.rel:
            #assert  isinstance(field.rel, OneOnOneRelation), "only OneOf relations allowed here, field %s is'nt " % field.name
        
            
            related = getattr(obj, field.name)
            if related is not None:
                aspect_json_value = JsonSerializer().serialize(related)
                key_jsonvalue_dict[aspect_name] = aspect_json_value
        else:
            key_jsonvalue_dict[aspect_name] = field.value_to_string(obj)
    
    dynamic_attr_list = []
    if issubclass(obj.__class__, DynamicModel):
        dynamic_attributes = obj._get_dynamic_attributes()
        for aspect_name, value in dynamic_attributes.items():
            aspect_json_value = JsonSerializer().serialize(value)
            key_jsonvalue_dict[aspect_name] = aspect_json_value
            dynamic_attr_list.append( get_fqclassname_forinstance(value))
    da = DYNAMIC_ATTRIBUTES        
    key_jsonvalue_dict[da] = simplejson.dumps(dynamic_attr_list)
    #key_jsonvalue_dict['clazz'] = get_fqclassname_forinstance(obj)
    
            
    return key_jsonvalue_dict         



def object_from_key_jsonvalue_dict(clazz, json_value_dict):
    """
    Creates a object of clazz and initializes it values from the json_value_dict
    """
    from .documents import DynamicModel
    from .fields import FieldDoesNotExist
    
    obj = clazz()
    for name, value in json_value_dict.items():
        if name in [CLAZZ,DYNAMIC_ATTRIBUTES]:
                continue
        try:
            field = obj._meta.get_field(name)    
    
            if field.rel:
                #assert isinstance(field.rel, OneOnOneRelation), "only OneOf relations allowed here"
           
                if isinstance( field.rel, OneOnOneRelation):
                    attr_value = JsonUnSerializer().unserialize(value, field.rel.to)
                    setattr(obj, name, attr_value)
                elif isinstance( field.rel, MapRelation):
                    attr_value = JsonUnSerializer().unserializeMap(value, field.rel.to, field.rel.contains_built_in_type)
                    setattr(obj, name, attr_value)
                elif isinstance( field.rel, ListRelation):
                    attr_value = JsonUnSerializer().unserializeList(value, field.rel.to, field.rel.contains_built_in_type)
                    setattr(obj, name, attr_value)    
                        
            else:
                setattr(obj, name, value)
        except FieldDoesNotExist:
            "add it as a dynamic field"
            if issubclass( clazz, DynamicModel):
                    child = JsonUnSerializer().unserialize(value)
                    obj.add_dynamic_attribute(name, child)

    return obj
