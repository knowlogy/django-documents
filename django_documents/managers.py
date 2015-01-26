import signals as persistent_signals
from fields import FieldDoesNotExist
import copy


def ensure_default_manager(sender, **kwargs):
    """
    """
    cls = sender
    if not cls._meta.is_root:
        return
    if not getattr(cls, '_default_manager', None):
        # Create the default manager, if needed.
        try:
            cls._meta.get_field('objects')
            raise ValueError("Model %s must specify a custom Manager, because it has a field named 'objects'" % cls.__name__)
        except FieldDoesNotExist:
            pass
        cls.add_to_class('objects', Manager())
        cls._base_manager = cls.objects
    elif not getattr(cls, '_base_manager', None):
        default_mgr = cls._default_manager.__class__
        if (default_mgr is Manager or
                getattr(default_mgr, "use_for_related_fields", False)):
            cls._base_manager = cls._default_manager
        else:
            # Default manager isn't a plain Manager class, or a suitable
            # replacement, so we walk up the base class hierarchy until we hit
            # something appropriate.
            for base_class in default_mgr.mro()[1:]:
                if (base_class is Manager or
                        getattr(base_class, "use_for_related_fields", False)):
                    cls.add_to_class('_base_manager', base_class())
                    return
            raise AssertionError("Should never get here. Please report a bug, including your model and model manager setup.")

#persistent_signals.aspect_class_prepared.connect(ensure_default_manager)

#import pycassa
from serializer import create_key_jsonvalue_dict, object_from_key_jsonvalue_dict
from utils import  get_fqclassname_forinstance, get_class
from django.conf import settings
    


class Manager(object):
    # Tracks each time a Manager instance is created. Used to retain order.
    creation_counter = 0

    def __init__(self):
        super(Manager, self).__init__()
        self._set_creation_counter()
        self.model = None
        self._inherited = False
        self._key_space_name = None
        self._column_family_name = None
        self._pool = None
        self._column_family = None
 
        
#    def _get_column_family(self):
#        if self._pool is None:
#            assert not self._key_space_name is None, "key space must have been set in meta of class"
#            assert not self._column_family_name is None, "column family name must have been set in meta of class"
            
#            key_space_name = self._key_space_name
#            if hasattr(settings, 'ISINTEST'):
#                key_space_name = 'TEST_' + self._key_space_name
#            #self._pool = pycassa.connect(key_space_name, settings.CASSANDRA_SERVER_LIST)
#            self._pool = pycassa.ConnectionPool(key_space_name, server_list= settings.CASSANDRA_SERVER_LIST)
#            self._column_family = pycassa.ColumnFamily(self._pool, self._column_family_name)
#        return self._column_family    

    def contribute_to_class(self, model, name):
        # TODO: Use weakref because of possible memory leak / circular reference.
        self.model = model
        setattr(model, name, ManagerDescriptor(self))
        if not getattr(model, '_default_manager', None) or self.creation_counter < model._default_manager.creation_counter:
            model._default_manager = self
        if model._meta.abstract or (self._inherited and not self.model._meta.proxy):
            model._meta.abstract_managers.append((self.creation_counter, name, self))
        else:
            model._meta.concrete_managers.append((self.creation_counter, name, self))
        if model._meta.is_root:
        
            self._key_space_name = model._meta.key_space_name
            self._column_family_name = model._meta.column_family_name
        
            

    def _set_creation_counter(self):
        """
        Sets the creation counter value for this instance and increments the
        class-level copy.
        """
        self.creation_counter = Manager.creation_counter
        Manager.creation_counter += 1

    def _copy_to_model(self, model):
        """
        Makes a copy of the manager and assigns it to 'model', which should be
        a child of the existing model (used when inheriting a manager from an
        abstract base class).
        """
        assert issubclass(model, self.model)
        mgr = copy.copy(self)
        mgr._set_creation_counter()
        mgr.model = model
        mgr._inherited = True
        return mgr

    
    def delete(self, id):
        
        instance = self.get(id)
        
        self._get_column_family().remove(id)
        cls = self.model.__class__
        persistent_signals.data_post_delete.send(sender=cls, instance=instance)

    def save(self, obj):
        
        obj.full_clean()
        id = obj.id
        assert not id is None, "key must have a value"
        key_jsonvalue_dict = create_key_jsonvalue_dict(obj)
        # save special values
        key_jsonvalue_dict['_clazz'] = get_fqclassname_forinstance(obj)
        self._get_column_family().insert(id, key_jsonvalue_dict)
        cls = self.model.__class__
        persistent_signals.data_post_save.send(sender=cls, instance=obj)

    
    def get(self, id, props = None):    
        if props:
            props.append('_clazz')
            props.append('id')
        retrieved_dict = self._get_column_family().get(id, props)
        clazz_name = retrieved_dict['_clazz']
        clazz = get_class(clazz_name)
        return object_from_key_jsonvalue_dict(clazz, retrieved_dict)
    
        
    
class ManagerDescriptor(object):
    # This class ensures managers aren't accessible via model instances.
    # For example, Poll.objects works, but poll_obj.objects raises AttributeError.
    def __init__(self, manager):
        self.manager = manager

    def __get__(self, instance, type=None):
        if instance != None:
            raise AttributeError("Manager isn't accessible via %s instances" % type.__name__)
        return self.manager

class EmptyManager(Manager):
    def get_query_set(self):
        return self.get_empty_query_set()