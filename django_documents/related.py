from django.utils.encoding import smart_unicode
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import ValidationError 

from validators import MinListLengthValidator, MaxListLengthValidator
from fields import Field, FieldDoesNotExist
import types
import signals

RECURSIVE_RELATIONSHIP_CONSTANT = 'self'

pending_lookups = {}

def is_accepted_type(to):
    return to == types.StringType or to == types.IntType or to == types.LongType or to == types.UnicodeType or to == types.FloatType or to == types.BooleanType or to == types.StringTypes

def is_accepted_type_one_of(to):
    # for one of also accept a dictionary
    return is_accepted_type(to) or to == types.DictType
    
        

def add_lazy_relation(cls, field, relation, operation):
    """
    Adds a lookup on ``cls`` when a related field is defined using a string,
    i.e.::

        class MyModel(Model):
            fk = OneOf("AnotherModel")

    This string can be:

        * RECURSIVE_RELATIONSHIP_CONSTANT (i.e. "self") to indicate a recursive
          relation.

        * The name of a model (i.e "AnotherModel") to indicate another model in
          the same app.

        * An app-label and model name (i.e. "someapp.AnotherModel") to indicate
          another model in a different app.

    If the other model hasn't yet been loaded -- almost a given if you're using
    lazy relationships -- then the relation won't be set up until the
    class_prepared signal fires at the end of model initialization.

    operation is the work that must be performed once the relation can be resolved.
    """
    # Check for recursive relations
    if relation == RECURSIVE_RELATIONSHIP_CONSTANT:
        app_label = cls.__module__ 
        model_name = cls.__name__       
    else:
        # Look for an "app.Model" relation
        try:
            app_label, model_name = relation.split(".")
        except ValueError:
            # If we can't split, assume a model in current app
            app_label = cls.__module__
            model_name = relation
        


    # Try to look up the related model, and if it's already loaded resolve the
    # string right away. If get_model returns None, it means that the related
    # model isn't loaded yet, so we need to pend the relation until the class
    # is prepared.
    from register import get_model
    model = get_model(relation)
    if model:
        operation(field, model, cls)
    else:
        key = (app_label, model_name)
        value = (cls, field, operation)
        pending_lookups.setdefault(key, []).append(value)


def do_pending_lookups(sender, **kwargs):
    """
    Handle any pending relations to the sending model. Sent from class_prepared.
    """
    key = (sender.__module__, sender.__name__)
    for cls, field, operation in pending_lookups.pop(key, []):
        operation(field, sender, cls)



signals.class_prepared.connect(do_pending_lookups)

#HACK in original
class RelatedField(object):
    
    def contribute_to_class(self, cls, name):
        sup = super(RelatedField, self)

        # Store the opts for related_query_name()
        self.opts = cls._meta

        if hasattr(sup, 'contribute_to_class'):
            sup.contribute_to_class(cls, name) # calls Field.contribute_to_class

        if not cls._meta.abstract and self.rel.related_name:
            self.rel.related_name = self.rel.related_name % {
                    'class': cls.__name__.lower(),
                    'app_label': cls._meta.app_label.lower(),
                }

        other = self.rel.to
        if isinstance(other, basestring):
            def resolve_related_class(field, model, cls):
                field.rel.to = model
                #field.contribute_to_class(cls, name)
                #field.do_related_class(model, cls)
            add_lazy_relation(cls, self, other, resolve_related_class)
        #self.do_related_class(other, cls)

    def set_attributes_from_rel(self):
        self.name = self.name or (self.rel.to._meta.object_name.lower() + '_' + self.rel.to._meta.pk.name)
        if self.verbose_name is None:
            self.verbose_name = self.rel.to._meta.verbose_name
        self.rel.field_name = self.rel.field_name or self.rel.to._meta.pk.name

    def do_related_class(self, other, cls):
        if not cls._meta.abstract:
            #self.contribute_to_related_class(other, self.related)
            self.contribute_to_class(other, self.related)

class ReverseSingleRelatedObjectDescriptor(object):
    # This class provides the functionality that makes the related-object
    # managers available as attributes on a model class, for fields that have
    # a single "remote" value, on the class that defines the related field.
    # In the example "choice.poll", the poll attribute is a
    # ReverseSingleRelatedObjectDescriptor instance.
    def __init__(self, field_with_rel):
        self.field = field_with_rel

    def __get__(self, instance, instance_type=None):
        if instance is None:
            return self

        cache_name = self.field.get_cache_name()
        return getattr(instance, cache_name)
        
    def __set__(self, instance, value):
        if instance is None:
            raise AttributeError("%s must be accessed via instance" % self._field.name)

        # If null=True, we can assign null here, but otherwise the value needs
        # to be an instance of the related class.
        if value is None and self.field.null == False:
            raise ValueError('Cannot assign None: "%s.%s" does not allow null values.' %
                                (instance._meta.object_name, self.field.name))
        elif value is not None and not isinstance(value, self.field.rel.to):
            raise ValueError('Cannot assign "%r": "%s.%s" must be a "%s" instance.' %
                                (value, instance._meta.object_name,
                                 self.field.name, self.field.rel.to._meta.object_name))

        # Set the value of the related field
        try:
            val = getattr(value, self.field.rel.get_related_field().attname)
        except AttributeError:
            val = None
        setattr(instance, self.field.attname, val)

        # Since we already know what the related object is, seed the related
        # object cache now, too. This avoids another db hit if you get the
        # object you just set.
        setattr(instance, self.field.get_cache_name(), value)

   

class ReverseSingleObjectDescriptor(object):
    # This class provides the functionality that makes the related-object
    # managers available as attributes on a model class, for fields that have
    # a single "remote" value, on the class that defines the related field.
    # In the example "choice.poll", the poll attribute is a
    # ReverseSingleRelatedObjectDescriptor instance.
    def __init__(self, field_with_rel):
        self.field = field_with_rel

    def __get__(self, instance, instance_type=None):
        if instance is None:
            return self

        cache_name = self.field.get_cache_name()
        return getattr(instance, cache_name, None)
        
    def __set__(self, instance, value):
        if instance is None:
            raise AttributeError("%s must be accessed via instance" % self._field.name)

        # If null=True, we can assign null here, but otherwise the value needs
        # to be an instance of the related class.
        #if value is None and self.field.null == False:
        #    raise ValueError('Cannot assign None: "%s.%s" does not allow null values.' %
        #                        (instance._meta.object_name, self.field.name))
        if value is not None and not isinstance(value, self.field.rel.to):
            raise ValueError('Cannot assign "%r": "%s.%s" must be a "%s" instance. It s a %s' %
                                (value, instance._meta.object_name,
                                 self.field.name, self.field.rel.to._meta.object_name, self.field.rel.to))

        # Set the value of the related field
        #try:
        #    val = getattr(value, self.field.rel.get_related_field().attname)
        #except AttributeError:
        #    val = None
        #setattr(instance, self.field.attname, val)

        # Since we already know what the related object is, seed the related
        # object cache now, too. This avoids another db hit if you get the
        # object you just set.
        setattr(instance, self.field.get_cache_name(), value)
        
class ReverseListRelatedObjectDescriptor(object):      


# This class provides the functionality that makes the related-object
    # managers available as attributes on a model class, for fields that have
    # a single "remote" value, on the class that defines the related field.
    # In the example "choice.poll", the poll attribute is a
    # ReverseSingleRelatedObjectDescriptor instance.
    def __init__(self, field_with_rel):
        self.field = field_with_rel

    def __get__(self, instance, instance_type=None):
        if instance is None:
            return self

        cache_name = self.field.get_cache_name()
        return getattr(instance, cache_name)
        
    def __set__(self, instance, value):
        if instance is None:
            raise AttributeError("%s must be accessed via instance" % self._field.name)

        # If null=True, we can assign null here, but otherwise the value needs
        # to be an instance of the related class.
        
        #if value is None and self.field.null == False:
        #    raise ValueError('Cannot assign None: "%s.%s" does not allow null values.' %
        #                        (instance._meta.object_name, self.field.name))
        #elif 
        
        if value is not None and not isinstance(value, list): # and not isinstance(value, self.field.rel.to): ROHO CHECK ON LIST ITEMS?? OR REPLACE LIST WITH OWN TYPE
            raise ValueError('Cannot assign "%r": "%s.%s" must be a "%s" instance.' %
                                (value, instance._meta.object_name,
                                 self.field.name, self.field.rel.to._meta.object_name))

        # Set the value of the related field
        #try:
        #    val = getattr(value, self.field.rel.get_related_field().attname)
        #except AttributeError:
        #    val = None
        #setattr(instance, self.field.attname, val)

        # Since we already know what the related object is, seed the related
        # object cache now, too. This avoids another db hit if you get the
        # object you just set.
        setattr(instance, self.field.get_cache_name(), value)     


class MapObjectDescriptor(object):      


# This class provides the functionality that makes the related-object
    # managers available as attributes on a model class, for fields that have
    # a single "remote" value, on the class that defines the related field.
    # In the example "choice.poll", the poll attribute is a
    # ReverseSingleRelatedObjectDescriptor instance.
    def __init__(self, field_with_rel):
        self.field = field_with_rel

    def __get__(self, instance, instance_type=None):
        if instance is None:
            return self

        cache_name = self.field.get_cache_name()
        value = getattr(instance, cache_name)
        if value is None:
            value = {}
            setattr(instance, self.field.get_cache_name(), value)  
        return value    
        
    def __set__(self, instance, value):
        if instance is None:
            raise AttributeError("%s must be accessed via instance" % self._field.name)

        # If null=True, we can assign null here, but otherwise the value needs
        # to be an instance of the related class.
        
        #if value is None and self.field.null == False:
        #    raise ValueError('Cannot assign None: "%s.%s" does not allow null values.' %
        #                        (instance._meta.object_name, self.field.name))
        #elif 
        
        if value is not None and not isinstance(value, dict): # and not isinstance(value, self.field.rel.to): ROHO CHECK ON LIST ITEMS?? OR REPLACE LIST WITH OWN TYPE
            raise ValueError('Cannot assign "%r": "%s.%s" must be a "%s" instance.' %
                                (value, instance._meta.object_name,
                                 self.field.name, self.field.rel.to._meta.object_name))

        # Set the value of the related field
        #try:
        #    val = getattr(value, self.field.rel.get_related_field().attname)
        #except AttributeError:
        #    val = None
        #setattr(instance, self.field.attname, val)

        # Since we already know what the related object is, seed the related
        # object cache now, too. This avoids another db hit if you get the
        # object you just set.
        setattr(instance, self.field.get_cache_name(), value)     

class Enum(set):
    def __getattr__(self, name):
        if name in self:
            return name
        raise AttributeError


        
class RelationMeta(object):

    """
    Metadata object, contained by ModelClass._meta.fields[fieldname].rel attribute
    for 
    """

    
    def __init__(self, field, to, field_name, related_name=None, limit_choices_to=None, lookup_overrides=None, parent_link=False, part_of_parent = True, contains_built_in_type = False, xml_element_name = None):
        try:
            to._meta
        except AttributeError: # to._meta doesn't exist, so it must be RECURSIVE_RELATIONSHIP_CONSTANT
            if is_accepted_type(to):
                pass
            #assert isinstance(to, basestring), "'to' must be either a model, a model name or the string %r" % RECURSIVE_RELATIONSHIP_CONSTANT
        self.field = field    
        self.to, self.field_name = to, field_name
        self.related_name = related_name
        if limit_choices_to is None:
            limit_choices_to = {}
        self.limit_choices_to = limit_choices_to
        self.lookup_overrides = lookup_overrides or {}
        self.multiple = True
        self.parent_link = parent_link
        self.part_of_parent = part_of_parent
        self.contains_built_in_type = contains_built_in_type
        self.xml_element_name = xml_element_name # element name in case of build in types

        

    def is_hidden(self):
        "Should the related object be hidden?"
        return self.related_name and self.related_name[-1] == '+'

    def get_related_field(self):
        """
        Returns the Field in the 'to' object to which this relationship is
        tied.
        """
        data = self.to._meta.get_field_by_name(self.field_name)
        if not data[2]:
            raise FieldDoesNotExist("No related field named '%s'" %
                    self.field_name)
        return data[0]    
    
    def add_to_instance(self, instance, value_dict, unserializer):
        pass  
    
    def unserialize_from_xml(self, instance, element, unserializer):
        pass

class MapRelation(RelationMeta):

    """
    Metadata object, contained by ModelClass._meta.fields[fieldname].rel attribute
    for 
    """
    def __init__(self, field, to, field_name, related_name=None, limit_choices_to=None, lookup_overrides=None, parent_link=False, part_of_parent = True, contains_built_in_type = False, xml_element_name = None, xml_key_attr_name = None):
        self.xml_key_attr_name = xml_key_attr_name
        super(MapRelation, self). __init__(field, to, field_name, related_name, limit_choices_to, lookup_overrides, parent_link, part_of_parent, contains_built_in_type, xml_element_name)



class ListRelation(RelationMeta):

    """
    Metadata object, contained by ModelClass._meta.fields[fieldname].rel attribute
    for 
    """
    def __init__(self, field, to, field_name, related_name=None, limit_choices_to=None, lookup_overrides=None, parent_link=False, part_of_parent = True, contains_built_in_type = False, xml_element_name = None):
        super(ListRelation, self). __init__(field, to, field_name, related_name = related_name, limit_choices_to = limit_choices_to, lookup_overrides = lookup_overrides, parent_link = parent_link, part_of_parent=part_of_parent, contains_built_in_type=contains_built_in_type, xml_element_name =xml_element_name)


    def unserialize_from_xml(self, instance, element, unserializer):
                
        list_element = element.find(self.field.name)
        if list_element:
            
            new_list = []
            clazz = self.to
            for child_element in list_element.getchildren():

                if not self.contains_built_in_type:
                    list_item = unserializer._unserialize(child_element, clazz)   
                else:
                    item = child_element.text
                    list_item = clazz(item)    
                new_list.append(list_item)
            
            setattr(instance, self.field.name, new_list)


class OneOnOneRelation(RelationMeta):

    """
    Metadata object, contained by ModelClass._meta.fields[fieldname].rel attribute
    for 
    """
    def __init__(self, field, to, field_name, related_name=None, limit_choices_to=None, lookup_overrides=None, parent_link=False, part_of_parent = True, contains_built_in_type = False, xml_element_name = None):
        super(OneOnOneRelation, self). __init__(field, to, field_name, related_name, limit_choices_to, lookup_overrides, parent_link, part_of_parent, contains_built_in_type, xml_element_name)
    

    

class MapOf(RelatedField, Field):        

    empty_strings_allowed = False
    default_error_messages = {
        'invalid': _('Model %(model)s with pk %(pk)r does not exist.')
    }
    description = _("Foreign Key (type determined by related field)")
    
    def __init__(self, to, to_field=None, rel_class=MapRelation, **kwargs):
        contains_built_in_type = False
        try:
            to_name = to._meta.object_name.lower()
        except AttributeError: # to._meta doesn't exist, so it must be RECURSIVE_RELATIONSHIP_CONSTANT
            # to._meta doesn't exist is it a basic type
            if is_accepted_type(to):
                contains_built_in_type = True
                
            #assert isinstance(to, basestring), "%s(%r) is invalid. First parameter to ForeignKey must be either a model, a model name, or the string %r" % (self.__class__.__name__, to, RECURSIVE_RELATIONSHIP_CONSTANT)
        else:
            assert not to._meta.abstract, "%s cannot define a relation with abstract class %s" % (self.__class__.__name__, to._meta.object_name)
            # For backwards compatibility purposes, we need to *try* and set
            # the to_field during FK construction. It won't be guaranteed to
            # be correct until contribute_to_class is called. Refs #12190.
            to_field = to_field
        kwargs['verbose_name'] = kwargs.get('verbose_name', None)


        kwargs['rel'] = rel_class(self, to, to_field,
            related_name=kwargs.pop('related_name', None),
            limit_choices_to=kwargs.pop('limit_choices_to', None),
            lookup_overrides=kwargs.pop('lookup_overrides', None),
            parent_link = False,
            xml_element_name = kwargs.pop('xml_element_name', 'item'),
            xml_key_attr_name = kwargs.pop('xml_key_attr_name', 'key'),
            contains_built_in_type = contains_built_in_type)
        Field.__init__(self, **kwargs)

        
    def contribute_to_class(self, cls, name):
        super(MapOf, self).contribute_to_class(cls, name)
        setattr(cls, self.name, MapObjectDescriptor(self))
        #if isinstance(self.rel.to, basestring):
        #    target = self.rel.to
        #else:
        #    target = self.rel.to._meta.db_table
        #cls._meta.duplicate_targets[self.column] = (target, "o2m")

    
    def handle_visit(self, visitor, instance):
        visitor.handle_map_of(self, instance)
           
            
        
class ListOf(RelatedField, Field):        

    empty_strings_allowed = False
    default_error_messages = {
        'invalid': _('Model %(model)s ')
    }
    description = _("Foreign Key (type determined by related field)")
    
    def __init__(self, to, to_field=None, rel_class=ListRelation, **kwargs):
        contains_built_in_type = False
        try:
            to_name = to._meta.object_name.lower()
        except AttributeError: # to._meta doesn't exist, so it must be RECURSIVE_RELATIONSHIP_CONSTANT
            # to._meta doesn't exist is it a basic type
            if is_accepted_type(to):
                contains_built_in_type = True
                
            #assert isinstance(to, basestring), "%s(%r) is invalid. First parameter to ForeignKey must be either a model, a model name, or the string %r" % (self.__class__.__name__, to, RECURSIVE_RELATIONSHIP_CONSTANT)
        else:
            #assert not to._meta.abstract, "%s cannot define a relation with abstract class %s" % (self.__class__.__name__, to._meta.object_name)
            # For backwards compatibility purposes, we need to *try* and set
            # the to_field during FK construction. It won't be guaranteed to
            # be correct until contribute_to_class is called. Refs #12190.
            to_field = to_field 
        kwargs['verbose_name'] = kwargs.get('verbose_name', None)


        kwargs['rel'] = rel_class(self, to, to_field,
            related_name=kwargs.pop('related_name', None),
            limit_choices_to=kwargs.pop('limit_choices_to', None),
            lookup_overrides=kwargs.pop('lookup_overrides', None),
            parent_link = False,
            xml_element_name = kwargs.get('xml_element_name', 'item'),
            contains_built_in_type = contains_built_in_type)
        Field.__init__(self, **kwargs)
        if self.min_length is not None:
            self.validators.append(MinListLengthValidator(self.min_length))
        if self.max_length is not None:
            self.validators.append(MaxListLengthValidator(self.max_length))
        
    def contribute_to_class(self, cls, name):
        super(ListOf, self).contribute_to_class(cls, name)
        setattr(cls, self.name, ReverseListRelatedObjectDescriptor(self))
        #if isinstance(self.rel.to, basestring):
        #    target = self.rel.to
        #else:
        #    target = self.rel.to._meta.db_table
        #cls._meta.duplicate_targets[self.column] = (target, "o2m")
    
    def handle_visit(self, visitor, instance):
        visitor.handle_list_of(self, instance)  
    
    def _validate(self, value):
        
        for option_key, option_value in self._choices:
            if isinstance(option_value, (list, tuple)):
                # This is an optgroup, so look inside the group for options.
                for optgroup_key, optgroup_value in option_value:
                    if value == optgroup_key:
                        return
            elif value == option_key:
                return
        raise ValidationError(self.error_messages['invalid_choice'] % value)
            
    
    def validate_list_items(self, value):
        
        if value is not None:
            errors = {}
            for i, item_value in enumerate(value):
                try:
                    item_value.full_clean()
                except ValidationError, e:
                    # @todo: e.messages contains the flattened list of errors, message_dict is containing error per field. 
                    errors[self.name + "." + str(i)] = e.messages
            if errors:
                raise ValidationError(errors)

    def run_validators(self, value):
        #default run_validators doesn't run the validators if value is EMPTYVALUES, a [] is a empty value
        #so overwrite the default
        
        errors = []
        for v in self.validators:
            try:
                v(value)
            except ValidationError, e:
                if hasattr(e, 'code') and e.code in self.error_messages:
                    message = self.error_messages[e.code]
                    if e.params:
                        message = message % e.params
                    errors.append(message)
                else:
                    errors.extend(e.messages)
        if errors:
            raise ValidationError(errors)
    
    def validate(self, value, model_instance):
        """
        Validates value and throws ValidationError. Subclasses should override
        this to provide validation logic.
        """
        if not self.editable:
            # Skip validation for non-editable fields.
            return
    
        if self.rel.contains_built_in_type:
    
            if self._choices and value:
                for item_value in value:
                    self._validate(item_value)
        else:
            self.validate_list_items(value)
                    
        if value is None and not self.null:
            raise ValidationError(self.error_messages['null'])
    
        """
        
        if not self.blank and value in validators.EMPTY_VALUES:
            raise exceptions.ValidationError(self.error_messages['blank'])
        """
        
        
        
class OneOf(RelatedField, Field):
    empty_strings_allowed = False
    default_error_messages = {
        'invalid': _('Model %(model)s with pk %(pk)r does not exist.')
    }
    description = _("Relation (type determined by related field)")
    
    def __init__(self, to, to_field=None, rel_class=OneOnOneRelation, **kwargs):
        try:
            to_name = to._meta.object_name.lower()
        except AttributeError: # to._meta doesn't exist, so it must be RECURSIVE_RELATIONSHIP_CONSTANT
            if is_accepted_type_one_of(to):
                contains_built_in_type = True
            else:    
                assert isinstance(to, basestring), "%s(%r) is invalid. First parameter to related object must be either a model, a model name, or the string %r" % (self.__class__.__name__, to, RECURSIVE_RELATIONSHIP_CONSTANT)
        else:
            #assert not to._meta.abstract, "%s cannot define a relation with abstract class %s" % (self.__class__.__name__, to._meta.object_name)
            # For backwards compatibility purposes, we need to *try* and set
            # the to_field during FK construction. It won't be guaranteed to
            # be correct until contribute_to_class is called. Refs #12190.
            to_field = to_field
        kwargs['verbose_name'] = kwargs.get('verbose_name', None)

        kwargs['rel'] = rel_class(self,to, to_field,
            related_name=kwargs.pop('related_name', None),
            limit_choices_to=kwargs.pop('limit_choices_to', None),
            lookup_overrides=kwargs.pop('lookup_overrides', None),
            parent_link=kwargs.pop('parent_link', False))
        Field.__init__(self, **kwargs)

    def validate(self, value, model_instance):
        if self.rel.parent_link:
            return
        super(OneOf, self).validate(value, model_instance)
        if value is None:
            return

    def clean(self, value, model_instance):
        value = super(OneOf, self).clean(value, model_instance)
        if value:
            value.full_clean()
        return value    
    
        
    #def get_attname(self):
    #    return '%s' % self.name

    def get_validator_unique_lookup_type(self):
        return '%s__%s__exact' % (self.name, self.rel.get_related_field().name)

    def get_default(self):
        "Here we check if the default value is an object and return the to_field if so."
        field_default = super(OneOf, self).get_default()
        if isinstance(field_default, self.rel.to):
            return getattr(field_default, self.rel.get_related_field().attname)
        return field_default

    def value_to_string(self, obj):
        if not obj:
            # In required many-to-one fields with only one available choice,
            # select that one available choice. Note: For SelectFields
            # we have to check that the length of choices is *2*, not 1,
            # because SelectFields always have an initial "blank" value.
            if not self.blank and self.choices:
                choice_list = self.get_choices_default()
                if len(choice_list) == 2:
                    return smart_unicode(choice_list[1][0])
        return Field.value_to_string(self, obj)

    def contribute_to_class(self, cls, name):
        super(OneOf, self).contribute_to_class(cls, name)
        setattr(cls, self.name, ReverseSingleObjectDescriptor(self))
       
    
    def handle_visit(self, visitor, instance):
        related_instance = getattr(instance, self.name)
        visitor.handle_one_of(self, instance, related_instance)
        
    def contribute_to_related_class(self, cls, related):
        # Internal FK's - i.e., those with a related name ending with '+' -
        # don't get a related descriptor.
        if not self.rel.is_hidden():
            setattr(cls, related.get_accessor_name(), ReverseSingleObjectDescriptor(related))
                   
