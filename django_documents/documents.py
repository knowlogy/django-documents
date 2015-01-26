import copy
import weakref
import re


from django.core import validators
from django.utils.translation import ugettext_lazy as _
from django.utils.encoding import force_unicode
from django.core.exceptions import FieldError, ValidationError
from django.utils.translation import get_language

from itertools import izip

from django.utils.translation import string_concat
from django.utils.datastructures import SortedDict
from bisect import bisect
import signals as persistent_signals
from fields import FieldDoesNotExist
from .utils import get_fqclassname_forclass, to_unicode_utf8
import django_documents.managers  # @UnusedImport needed for triggering connecting to signals, DO NOT REMOVE 


    


# The values to use for "blank" in SelectFields. Will be appended to the start of most "choices" lists.
BLANK_CHOICE_DASH = [("", "---------")]
BLANK_CHOICE_NONE = [("", "None")]


def subclass_exception(name, parents, module):
    return type(name, parents, {'__module__': module})

# Calculate the verbose_name by converting from InitialCaps to "lowercase with spaces".
get_verbose_name = lambda class_name: re.sub('(((?<=[a-z])[A-Z])|([A-Z](?![A-Z]|$)))', ' \\1', class_name).lower().strip()

DEFAULT_NAMES = ('verbose_name', 'permissions', 
                 'app_label',
                 'abstract', 'managed', 'proxy', 'auto_created')




class ObjectValidationError(ValidationError):
    
    def __init__(self, messages, code=None, params=None, obj = None):
        assert isinstance(messages, dict) 
        self.message_dict = messages
        self.messages = messages
        self.obj = obj
        self.message = self.messages
    
    

class Meta(object):
    def __init__(self, meta, app_label=None):
        self.local_fields = []
        self.virtual_fields = []
        self.module_name, self.verbose_name = None, None
        self.verbose_name_plural = None
        self.object_name, self.app_label = None, app_label
        self.meta = meta
        self.has_auto_field, self.auto_field = False, None
        self.abstract = False
        self.managed = True
        self.proxy = False
        self.proxy_for_model = None
        self.parents = SortedDict()
        self.duplicate_targets = {}
        self.auto_created = False
        self.xml_element_name = None
        self.is_root = False
        
        self.key_space_name = None
        self.column_family_name = None

        self.js_widgetclass = None
        self.js_widgetclass_meta = None
        self.index_function = None
        self.is_group = False
        
        self.abstract_managers = []
        self.concrete_managers = []

    def contribute_to_class(self, cls, name):
        
        cls._meta = self
        # First, construct the default values for these options.
        self.object_name = cls.__name__
        self.module_name = self.object_name.lower()
        #self.verbose_name = get_verbose_name(self.object_name)
        self.clazz_name = get_fqclassname_forclass(cls)
        self.xml_element_name = cls.__name__
        # Next, apply any overridden values from 'class Meta'.
        if self.meta:
            meta_attrs = self.meta.__dict__.copy()
            for name in self.meta.__dict__:
                # Ignore any private attributes that Django doesn't care about.
                # NOTE: We can't modify a dictionary's contents while looping
                # over it, so we loop over the *original* dictionary instead.
                if name.startswith('_'):
                    del meta_attrs[name]
            for attr_name in DEFAULT_NAMES:
                if attr_name in meta_attrs:
                    setattr(self, attr_name, meta_attrs.pop(attr_name))
                elif hasattr(self.meta, attr_name):
                    setattr(self, attr_name, getattr(self.meta, attr_name))


            # verbose_name_plural is a special case because it uses a 's'
            # by default.
            setattr(self, 'verbose_name_plural', meta_attrs.pop('verbose_name_plural', string_concat(self.verbose_name, 's')))
            setattr(self, 'xml_element_name', meta_attrs.pop('xml_element_name', cls.__name__))
            setattr(self, 'is_root', meta_attrs.pop('is_root', self.is_root))
            setattr(self, 'column_family_name', meta_attrs.pop('column_family_name', self.column_family_name))
            setattr(self, 'key_space_name', meta_attrs.pop('key_space_name', self.key_space_name))
            setattr(self, 'js_widgetclass', meta_attrs.pop('js_widgetclass', None))
            setattr(self, 'js_widgetclass_meta', meta_attrs.pop('js_widgetclass_meta', None))
            setattr(self, 'index_function', meta_attrs.pop('index_function', None))

            setattr(self, "is_group", meta_attrs.pop('is_group', None))
            setattr(self, "display_order", meta_attrs.pop('display_order', None))
            # Any leftover attributes must be invalid.
            if meta_attrs != {}:
                raise TypeError("'class Meta' got invalid attribute(s): %s" % ','.join(meta_attrs.keys()))
        else:
            self.verbose_name_plural = string_concat(self.verbose_name, 's')
        del self.meta
        
        
    def _prepare(self, model):
        pass
                

    def add_field(self, field):
        # Insert the given field in the order in which it was created, using
        # the "creation_counter" attribute of the field.
        # Move many-to-many related fields from self.fields into
        # self.many_to_many.
       
        self.local_fields.insert(bisect(self.local_fields, field), field)
        if hasattr(self, '_field_cache'):
                del self._field_cache
                del self._field_name_cache

        if hasattr(self, '_name_map'):
            del self._name_map      

    
    def _fields(self):
        """
        The getter for self.fields. This returns the list of field objects
        available to this model (including through parent models).

        Callers are not permitted to modify this list, since it's a reference
        to this instance (not a copy).
        """
        try:
            self._field_name_cache
        except AttributeError:
            self._fill_fields_cache()
        return self._field_name_cache
    fields = property(_fields)        
     
     
    def _fill_fields_cache(self):
        cache = []
        for parent in self.parents:
            for field, model in parent._meta.get_fields_with_model():
                if model:
                    cache.append((field, model))
                else:
                    cache.append((field, parent))
        cache.extend([(f, None) for f in self.local_fields])
        self._field_cache = tuple(cache)
        self._field_name_cache = [x for x, _ in cache] 
     

    def get_field(self, name, many_to_many=True):
        """
        Returns the requested field by name. Raises FieldDoesNotExist on error.
        """
        to_search = self.fields
        for f in to_search:
            if f.name == name:
                return f
        raise FieldDoesNotExist('%s has no field named %r' % (self.object_name, name))
    
    
    def get_field_by_xml_element_name(self, xml_element_name):
        to_search = self.fields
        for f in to_search:
            if f.xml_element_name == xml_element_name:
                return f
        raise FieldDoesNotExist('%s has no field with xml_element_name %r' % (self.object_name, xml_element_name))
    
    
    def describe(self, described_classes = None, recursive = False):
        
        if not described_classes:
            described_classes = []
        
        if self.clazz_name not in described_classes:
            if recursive:
                described_classes.append(self.clazz_name)
            description = {}
            fields_desc_list = []
            for field in self.local_fields:
                fields_desc_list.append(field.describe(described_classes = described_classes, recursive = recursive)) 
                
            description['clazz'] = self.clazz_name    
            description['fields'] = fields_desc_list
            description['verbose_name'] = self.verbose_name
            description['is_group'] = self.is_group
            
            if self.js_widgetclass is not None:
                description['js_widgetclass'] = self.js_widgetclass
            if self.js_widgetclass_meta is not None:
                description['js_widgetclass_meta'] = self.js_widgetclass_meta
            return description
        else:
            description = {"clazz": self.clazz_name, "already_described" : True}
            return description
    
    
    def get_verbose_name(self, locale):
        
        if isinstance(self.verbose_name, dict):
            if locale in self.verbose_name:
                return to_unicode_utf8( self.verbose_name[locale])
            else:
                return to_unicode_utf8( self.verbose_name.itervalues().next())            
        else:
            return to_unicode_utf8(self.verbose_name)


from register import register_model
            
class ModelBase(type):
    """
    Metaclass for all models.
    """
    def __new__(cls, name, bases, attrs):
        super_new = super(ModelBase, cls).__new__
        parents = [b for b in bases if isinstance(b, ModelBase)]
        if not parents:
            # If this isn't a subclass of Model, don't do anything special.
            return super_new(cls, name, bases, attrs)

        # Create the class.
        module = attrs.pop('__module__')
        new_class = super_new(cls, name, bases, {'__module__': module})
        attr_meta = attrs.pop('Meta', None)
        abstract = getattr(attr_meta, 'abstract', False)
        if not attr_meta:
            meta = getattr(new_class, 'Meta', None)
        else:
            meta = attr_meta
        base_meta = getattr(new_class, '_meta', None)

        kwargs = {}

        new_class.add_to_class('_meta', Meta(meta, **kwargs))
                
        # Bail out early if we have already created this class.
        #m = get_model(new_class._meta.app_label, name, False)
        #if m is not None:
        #    return m

        # Add all attributes to the class.
        for obj_name, obj in attrs.items():
            new_class.add_to_class(obj_name, obj)

        # All the fields of any type declared on this model
        new_fields = new_class._meta.local_fields + new_class._meta.virtual_fields
        field_names = set([f.name for f in new_fields])

        for base in parents:
            original_base = base
            if not hasattr(base, '_meta'):
                # Things without _meta aren't functional models, so they're
                # uninteresting parents.
                continue

            parent_fields = base._meta.local_fields
            # Check for clashes between locally declared fields and those
            # on the base classes (we cannot handle shadowed fields at the
            # moment).
            for field in parent_fields:
                if field.name in field_names:
                    raise FieldError('Local field %r in class %r clashes '
                                     'with field of similar name from '
                                     'base class %r' %
                                        (field.name, name, base.__name__))
            
            for field in parent_fields:
                new_class.add_to_class(field.name, copy.deepcopy(field))

            # Inherited some meta functions from parents   
            if new_class._meta.index_function is None and base._meta.index_function is not None:
                new_class._meta.index_function = base._meta.index_function

            # Pass any non-abstract parent classes onto child.
            new_class._meta.parents.update(base._meta.parents)

            # Inherit managers from the abstract base classes.
            new_class.copy_managers(base._meta.abstract_managers)

            # Proxy models inherit the non-abstract managers from their base,
            # unless they have redefined any of them.

            # Inherit virtual fields (like GenericForeignKey) from the parent
            # class
            for field in base._meta.virtual_fields:
                if base._meta.abstract and field.name in field_names:
                    raise FieldError('Local field %r in class %r clashes '\
                                     'with field of similar name from '\
                                     'abstract base class %r' % \
                                        (field.name, name, base.__name__))
                new_class.add_to_class(field.name, copy.deepcopy(field))


        new_class._prepare()
        register_model(new_class)
#        register_models(new_class._meta.app_label, new_class)

        # Because of the way imports happen (recursively), we may or may not be
        # the first time this model tries to register with the framework. There
        # should only be one class for each model, so we always return the
        # registered version.
        return new_class #get_model(new_class._meta.app_label, name, False)

    def copy_managers(cls, base_managers):#@NoSelf
        # This is in-place sorting of an Options attribute, but that's fine.
        base_managers.sort()
        for _, mgr_name, manager in base_managers:
            val = getattr(cls, mgr_name, None)
            if not val or val is manager:
                new_manager = manager._copy_to_model(cls)
                cls.add_to_class(mgr_name, new_manager)

    def add_to_class(cls, name, value):#@NoSelf
        if hasattr(value, 'contribute_to_class'):
            value.contribute_to_class(cls, name)
        else:
            setattr(cls, name, value)

    def _prepare(cls):#@NoSelf
        """
        Creates some methods once self._meta has been populated.
        """
        opts = cls._meta
        opts._prepare(cls)

        
        # Give the class a docstring -- its definition.
        if cls.__doc__ is None:
            cls.__doc__ = "%s(%s)" % (cls.__name__, ", ".join([f.attname for f in opts.fields]))

        #if hasattr(cls, 'get_absolute_url'):
        #    cls.get_absolute_url = update_wrapper(curry(get_absolute_url, opts, cls.get_absolute_url),
        #                                          cls.get_absolute_url)

        persistent_signals.class_prepared.send(sender=cls)

class DeferredAttribute(object):
    """
    A wrapper for a deferred-loading field. When the value is read from this
    object the first time, the query is executed.
    """
    def __init__(self, field_name, model):
        self.field_name = field_name
        self.model_ref = weakref.ref(model)
        self.loaded = False

    def __get__(self, instance, owner):
        """
        Retrieves and caches the value from the datastore on the first lookup.
        Returns the cached value.
        """
        
        assert instance is not None
        cls = self.model_ref()
        data = instance.__dict__
        if data.get(self.field_name, self) is self:
            # self.field_name is the attname of the field, but only() takes the
            # actual name, so we need to translate it here.
            try:
                cls._meta.get_field_by_name(self.field_name)
                name = self.field_name
            except FieldDoesNotExist:
                name = [f.name for f in cls._meta.fields
                    if f.attname == self.field_name][0]
            # We use only() instead of values() here because we want the
            # various data coersion methods (to_python(), etc.) to be called
            # here.
            val = getattr(
                cls._base_manager.filter(pk=instance.pk).only(name).using(
                    instance._state.db).get(),
                self.field_name
            )
            data[self.field_name] = val
        return data[self.field_name]

    def __set__(self, instance, value):
        """
        Deferred loading attributes can be set normally (which means there will
        never be a database lookup involved.
        """
        instance.__dict__[self.field_name] = value

        

class ModelState(object):
    """
    A class for storing instance state
    """
    def __init__(self, db=None):
        self.db = db        
        
        
class Model(object):
    __metaclass__ = ModelBase
    _deferred = False

    def __init__(self, *args, **kwargs):
        #signals.pre_init.send(sender=self.__class__, args=args, kwargs=kwargs)
        self.key = None

        # Set up the storage for instance state
        self._state = ModelState()

        # There is a rather weird disparity here; if kwargs, it's set, then args
        # overrides it. It should be one or the other; don't duplicate the work
        # The reason for the kwargs check is that standard iterator passes in by
        # args, and instantiation for iteration is 33% faster.
        args_len = len(args)
        if args_len > len(self._meta.fields):
            # Daft, but matches old exception sans the err msg.
            raise IndexError("Number of args exceeds number of fields")

        fields_iter = iter(self._meta.fields)
        if not kwargs:
            # The ordering of the izip calls matter - izip throws StopIteration
            # when an iter throws it. So if the first iter throws it, the second
            # is *not* consumed. We rely on this, so don't change the order
            # without changing the logic.
            for val, field in izip(args, fields_iter):
                setattr(self, field.attname, val)
        else:
            # Slower, kwargs-ready version.
            for val, field in izip(args, fields_iter):
                setattr(self, field.attname, val)
                kwargs.pop(field.name, None)
                from related import RelationMeta
                # Maintain compatibility with existing calls.
                if isinstance(field.rel, RelationMeta):
                    kwargs.pop(field.attname, None)

        # Now we're left with the unprocessed fields that *must* come from
        # keywords, or default.

        for field in fields_iter:
            is_related_object = False
            # This slightly odd construct is so that we can access any
            # data-descriptor object (DeferredAttribute) without triggering its
            # __get__ method.
            if (field.attname not in kwargs and
                    isinstance(self.__class__.__dict__.get(field.attname), DeferredAttribute)):
                # This field will be populated on request.
                continue
            if kwargs:
                try:
                    val = kwargs.pop(field.attname)
                except KeyError:
                        # This is done with an exception rather than the
                        # default argument on pop because we don't want
                        # get_default() to be evaluated, and then not used.
                        # Refs #12057.
                    val = field.get_default()
            else:
                val = field.get_default()
            if is_related_object:
                # ROHO todo solve this
                rel_obj = None
                # If we are passed a related instance, set it using the
                # field.name instead of field.attname (e.g. "user" instead of
                # "user_id") so that the object gets properly cached (and type
                # checked) by the RelatedObjectDescriptor.
                setattr(self, field.name, rel_obj)
            else:
                #if val: # don't attemp to set a None
                setattr(self, field.attname, val)

        if kwargs:
            for prop in kwargs.keys():
                try:
                    if isinstance(getattr(self.__class__, prop), property):
                        setattr(self, prop, kwargs.pop(prop))
                except AttributeError:
                    pass
            if kwargs:
                raise TypeError("'%s' is an invalid keyword argument for this function" % kwargs.keys()[0])
        #signals.post_init.send(sender=self.__class__, instance=self)
        
        
    def _get_FIELD_display(self, field):
        value = getattr(self, field.attname)
        flat_choices_dict = dict(field.flatchoices)
        display_values = flat_choices_dict.get(value, value)
        if isinstance( display_values, dict):
            language =  get_language()
            lang_code = language.split('-')[0]
            display_value = display_values.get(lang_code, None)
            if display_value is None:
                display_value = display_values.itervalues().next()
        else:
            display_value = display_values
        
        return force_unicode( display_value, strings_only=True)
        
    
    def save(self):
        """
        Saves the current instance. Override this in a subclass if you want to
        control the saving process.
       
        """
        cls = self.__class__
        meta = cls._meta
        assert meta.is_root, "expecting save only on root objects"
        #signals.pre_save.send(sender=origin, instance=self, raw=raw)
        cls.objects.save(self)
        
    def delete(self):
            
        cls = self.__class__
        meta = cls._meta
        assert meta.is_root, "expecting delete only on root objects"
        cls.objects.delete(self.id)
        
        
    def clean(self):
        """
        Hook for doing any extra model-wide validation after clean() has been
        called on every field by self.clean_fields. Any ValidationError raised
        by this method will not be associated with a particular field; it will
        have a special-case association with the field defined by NON_FIELD_ERRORS.
        """
        pass    
    
    def _add_error(self, attname, error_messages):
        
        obj_errors = getattr(self, '_errors', None)
        if obj_errors is None:
            obj_errors = {}
            setattr(self, '_errors', obj_errors)
        if not attname in obj_errors:
            obj_errors[attname] = []
        obj_errors[attname].append(error_messages)    
    
    def clean_fields(self, exclude=None):
        """
        Cleans all fields and raises a ValidationError containing message_dict
        of all validation errors if any occur.
        """
        if exclude is None:
            exclude = []

        errors = {}
        for f in self._meta.fields:
            if f.name in exclude:
                continue
            # Skip validation for empty fields with blank=True. The developer
            # is responsible for making sure they have a valid value.
            raw_value = getattr(self, f.attname)
            if f.blank and raw_value in validators.EMPTY_VALUES:
                continue
            try:
                setattr(self, f.attname, f.clean(raw_value, self))
            except ValidationError, e:
                errors[f.name] = e.messages
                self._add_error(f.attname, e.messages)

        if errors:
            raise ObjectValidationError(errors)
    
    def full_clean(self, exclude=None):
        """
        Calls clean_fields, clean, and validate_unique, on the model,
        and raises a ``ObjectValidationError`` for any errors that occured.
        """
        errors = {}
        if exclude is None:
            exclude = []

        try:
            self.clean_fields(exclude=exclude)
        except ValidationError, e:
            errors = e.update_error_dict(errors)

        # Form.clean() is run even if other validation fails, so do the
        # same with Model.clean() for consistency.
        try:
            self.clean()
        except ValidationError, e:
            errors = e.update_error_dict(errors)

        if errors:
            raise ObjectValidationError(errors, obj = self)
        
       
    def visit(self, visitor):

        try:
            visitor.start_handle_object(self)        
            for field in self._meta.local_fields:
                if field.rel is None:
                    visitor.handle_field(field, self)
                else:
                    # relation handle visitors themself
                    field.handle_visit(visitor, self)
        except StopIteration:
            pass        
        visitor.end_handle_object(self)
        
class DataAspect(Model):
    
    
    class Meta:
        abstract = True
        
class DynamicModel(Model):       
    
    class Meta:
        abstract = True

        
    def __init__(self,  *args, **kwargs):
        self.__dynamicdict__ = {}
        super(DynamicModel, self).__init__( *args, **kwargs)
        
    def add_dynamic_attribute(self, name, value):
        assert not name in self.__dict__
        
        if not issubclass(value.__class__, DataAspect):
            raise Exception()
        
        self.__dynamicdict__[name] = value
    
    def delete_dynamic_attribute(self, name):
        assert name in self.__dynamicdict__
        del self.__dynamicdict__[name]
        
    
    def __getattr__(self, name):
        """
        Note that when __setattr__ is called by setting 
        a attribute __getattr__ isn't called
        """
        
        try:
            return self.__dynamicdict__[name]    
        except KeyError:
            raise AttributeError()
    
#    def  __getattribute__(self, name):
#        try:
#            return super(DynamicModel, self).__getattribute__(name)
#        except AttributeError:
#            return self.__dynamicdict__[name]
#    
    def _get_dynamic_attributes(self):
        return self.__dynamicdict__.copy()         
    
    
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