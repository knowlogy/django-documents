from django.utils.datastructures import SortedDict
from utils import get_fqclassname_forclass

#__all__ = ('get_model', 'register_model')

class ModelCache(object):
    """
    A cache that stores  models. Used to
    provide app introspection (e.g. admin).
    """
    # Use the Borg pattern to share state between all instances. Details at
    # http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/66531.
    __shared_state = dict(
 
        app_models = SortedDict(),
        _get_models_cache = {},
    )

    def __init__(self):
        self.__dict__ = self.__shared_state
     
    
    def get_models(self, root = False):
        if not root:
            return SortedDict(self.app_models)
        else:
            model_dict = SortedDict()
            for name, clazz in self.app_models.items():
                if clazz._meta.is_root:
                    model_dict[name] = clazz
            return model_dict        
    
    def get_model(self, fq_modelclazzname):
        """
        Returns the model matching the given app_label and case-insensitive
        model_name.

        Returns None if no model is found.
        """
        return self.app_models.get(fq_modelclazzname, None)

    def register_model(self, model_clazz):
        """
        Register a model, abstract models are not registered
        """
        if not model_clazz._meta.abstract:
            clazz_name = get_fqclassname_forclass(model_clazz)
            self.app_models[clazz_name] = model_clazz
        
modelCache = ModelCache()

get_model = modelCache.get_model
register_model = modelCache.register_model
