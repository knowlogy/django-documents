




class ClassFactoryCache(object):
    """
    A cache for class factories
    
    class ClassFactory(object):
    
        def get_class(fully_qualified_classname):
            return clazz
    
    """
    # Use the Borg pattern see http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/66531.
    __shared_state = dict(
        _class_factory_cache = [],
    )

    def __init__(self):
        self.__dict__ = self.__shared_state

    def create_class(self, fq_clazzname):
        """
        Returns the model matching the given app_label and case-insensitive
        model_name.

        Returns None if no model is found.
        """
        for class_factory in self._class_factory_cache:
            clazz = class_factory.get_class(fq_clazzname)
            if clazz is not None:
                return clazz
        return None

    def register_class_factory(self, class_factory):
        """
        Register a model, abstract models are not registered
        """
        self._class_factory_cache.append(class_factory) 
        
classFactoryCache = ClassFactoryCache()