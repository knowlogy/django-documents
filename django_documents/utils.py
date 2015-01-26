import sys
from classfactory import classFactoryCache

from django.utils.encoding import force_unicode

import time, random, md5, socket


def uuid(*args):
    """
    Generates a universally unique ID.
    Any arguments only create more randomness.
    """
    t = long(time.time() * 1000)
    r = long(random.random()*100000000000000000L)
    try:
        a = socket.gethostbyname(socket.gethostname())
    except:
    # if we can't get a network address, just imagine one
        a = random.random()*100000000000000000L
    data = str(t)+' '+str(r)+' '+str(a)+' '+str(args)
    data = md5.md5(data).hexdigest()
    return data

def fix_uso_db_space(fqcn):
    """
    NOTE, THIS IS A TEMP FIX. TO REPAIR WRONG IMPORTS FROM THE PAST
    """
    if fqcn[0:3] == 'db.':
        return 'uso.' + fqcn
    else:
        return fqcn


def get_class(fqcn):
    try:
        fqcn = fix_uso_db_space(fqcn)
        paths = fqcn.split('.')
        modulename = '.'.join(paths[:-1])
        classname = paths[-1]
        __import__(modulename)
        return getattr(sys.modules[modulename], classname)
    except:
        clazz = classFactoryCache.create_class(fqcn)
        if clazz is None:
            raise RuntimeError("Clazz with name [%s] not found " % fqcn)
        return clazz

def get_fqclassname_forclass(aclass):
    return "%s.%s" % ( aclass.__module__ ,  aclass.__name__)

def get_fqclassname_forinstance(instance):
    
    return get_fqclassname_forclass(instance.__class__)



def get_dynamic_classes_list(obj):
    from .documents import DynamicModel
    
    dynamic_classes_list = []
    if issubclass(obj.__class__, DynamicModel):
        dynamic_attributes = obj._get_dynamic_attributes()
        for aspect_name, value in dynamic_attributes.items():
            dynamic_classes_list.append( get_fqclassname_forinstance(value))
    return dynamic_classes_list
    



def to_unicode_utf8(str):
        if str:
            str = force_unicode(str)
        return str 