from django.core.validators import BaseValidator
from django.utils.translation import ugettext_lazy as _

class MinListLengthValidator(BaseValidator):
    compare = lambda self, a, b: a < b
    clean   = lambda self, x: len(x)
    message = _(u'Ensure this list has at least %(limit_value)d items (it has %(show_value)d).')
    code = 'min_length'
    
    
    
class MaxListLengthValidator(BaseValidator):
    compare = lambda self, a, b: a > b
    clean   = lambda self, x: len(x)
    message = _(u'Ensure this list has at most %(limit_value)d items (it has %(show_value)d).')
    code = 'max_length'    