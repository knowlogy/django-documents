import copy

from django.core import exceptions, validators
from django.utils.functional import curry
from django.utils.translation import ugettext_lazy as _
from django.utils.encoding import smart_unicode, force_unicode, smart_str
from django.utils import datetime_safe
    
from utils import to_unicode_utf8
    
import types
import sys


import datetime
import re
import time
from itertools import tee


# The values to use for "blank" in SelectFields. Will be appended to the start of most "choices" lists.
BLANK_CHOICE_DASH = [("", "---------")]
BLANK_CHOICE_NONE = [("", "None")]


if sys.version_info < (2, 5):
    # Prior to Python 2.5, Exception was an old-style class
    def subclass_exception(name, parents, unused):
        return types.ClassType(name, parents, {})
else:
    def subclass_exception(name, parents, module):
        return type(name, parents, {'__module__': module})


 

class NOT_PROVIDED:
    pass


class FieldDoesNotExist(Exception):
    pass

class Field(object):
    """Base class for all field types"""
    
    empty_strings_allowed = False

    # These track each time a Field instance is created. Used to retain order.
    # The auto_creation_counter is used for fields that Django implicitly
    # creates, creation_counter is used for all user-specified fields.
    creation_counter = 0
    auto_creation_counter = -1
    default_validators = [] # Default set of validators
    default_error_messages = {
        'invalid_choice': _(u'Value %r is not a valid choice.'),
        'null': _(u'This field cannot be null.'),
        'blank': _(u'This field cannot be blank.'),
    }

    # Generic field type description, usually overriden by subclasses
    def _description(self):
        return _(u'Field of type: %(field_type)s') % {
            'field_type': self.__class__.__name__
        }
    description = property(_description)

    def __init__(self, 
            verbose_name=None, 
            name=None,
            min_length=None,
            max_length=None, 
            unique=False, 
            blank=False, 
            null=False,
            rel=None, 
            default=NOT_PROVIDED, 
            editable=True,
            serialize=True, 
            choices=None, 
            help_text='',
            auto_created=False, 
            validators=[],
            error_messages=None, 
            meta = None,
            indexed_field = None,   # field name in solr index 
            index_function = None,   # function called for solr indexing
            js_validate_regex = None,
            xml_element_name = None,
            js_widgetclass = None,
            js_widgetclass_meta = None,
            is_group = False,
            additional_meta = None
            ):
        self.name = name
        self.verbose_name = verbose_name
        self.max_length, self._unique = max_length, unique
        self.min_length = min_length
        self.blank, self.null = blank, null
        self.meta = meta
        self.xml_element_name = xml_element_name 
        # Oracle treats the empty string ('') as null, so coerce the null
        # option whenever '' is a possible value.
        if self.empty_strings_allowed:
            self.null = True
        self.rel = rel
        self.default = default
        self.editable = editable
        self.serialize = serialize
        self._choices = choices or []
        self.help_text = help_text
        
        self.auto_created = auto_created
        self.indexed_field = indexed_field
        self.index_function = index_function 
        self.js_validate_regex = js_validate_regex
        self.js_widgetclass = js_widgetclass
        self.js_widgetclass_meta = js_widgetclass_meta
        self.is_group = is_group
        self.additional_meta = additional_meta
        # Adjust the appropriate creation counter, and save our local copy.
        if auto_created:
            self.creation_counter = Field.auto_creation_counter
            Field.auto_creation_counter -= 1
        else:
            self.creation_counter = Field.creation_counter
            Field.creation_counter += 1

        self.validators = self.default_validators + validators

        messages = {}
        for c in reversed(self.__class__.__mro__):
            messages.update(getattr(c, 'default_error_messages', {}))
        messages.update(error_messages or {})
        self.error_messages = messages

    def __cmp__(self, other):
        # This is needed because bisect does not take a comparison function.
        return cmp(self.creation_counter, other.creation_counter)

    def __deepcopy__(self, memodict):
        # We don't have to deepcopy very much here, since most things are not
        # intended to be altered after initial creation.
        obj = copy.copy(self)
        if self.rel:
            obj.rel = copy.copy(self.rel)
        memodict[id(self)] = obj
        return obj

    def describe(self, described_classes = None, recursive = False):
        
        from utils import get_fqclassname_forinstance
        description = {}
        description['name'] = self.name
        description['meta'] = self.meta
        description['min_length'] = self.min_length
        description['max_length'] = self.max_length
        description['choices'] = self._choices
        description['verbose_name'] = self.verbose_name 
        description['blank'] = self.blank
        description['null'] = self.null
        description['type'] = get_fqclassname_forinstance(self)
        description['auto_created'] = self.auto_created
        description['is_group'] = self.is_group
        if self.default != NOT_PROVIDED:
            description['default'] = self.default
        if self.js_validate_regex:
            description['js_validate_regex'] = self.js_validate_regex
        if self.js_widgetclass:
            description['js_widgetclass'] = self.js_widgetclass
        if self.js_widgetclass_meta:
            description['js_widgetclass_meta'] = self.js_widgetclass_meta
            
        if self.additional_meta:
            description['additional_meta'] = self.additional_meta
            
        from related import is_accepted_type
        
        if self.rel:
            try:
                description['relation_clazz'] = self.rel.to._meta.describe(described_classes = described_classes, recursive = recursive)
            except AttributeError: # to._meta doesn't exist, so it must be RECURSIVE_RELATIONSHIP_CONSTANT
                # to._meta doesn't exist is it a basic type
                assert is_accepted_type(self.rel.to)
                description['relation_clazz'] = self.rel.to.__name__            
        return description
        

    def to_python(self, value):
        """
        Converts the input value into the expected Python data type, raising
        django.core.exceptions.ValidationError if the data can't be converted.
        Returns the converted value. Subclasses should override this.
        """
        return value

    def run_validators(self, value):
        if value in validators.EMPTY_VALUES:
            return

        errors = []
        for v in self.validators:
            try:
                v(value)
            except exceptions.ValidationError, e:
                if hasattr(e, 'code') and e.code in self.error_messages:
                    message = self.error_messages[e.code]
                    if e.params:
                        message = message % e.params
                    errors.append(message)
                else:
                    errors.extend(e.messages)
        if errors:
            raise exceptions.ValidationError(errors)

    def validate(self, value, model_instance):
        """
        Validates value and throws ValidationError. Subclasses should override
        this to provide validation logic.
        """
        if not self.editable:
            # Skip validation for non-editable fields.
            return
        if self._choices and value:
            if hasattr(self._choices, '__call__'):
                choices = self._choices()
            else:
                choices = self._choices
                
            for option_key, option_value in choices:
                if isinstance(option_value, (list, tuple)):
                    # This is an optgroup, so look inside the group for options.
                    for optgroup_key, _optgroup_value in option_value:
                        if value == optgroup_key:
                            return
                elif value == option_key:
                    return
            raise exceptions.ValidationError(self.error_messages['invalid_choice'] % value)

        if value is None and not self.null:
            raise exceptions.ValidationError(self.error_messages['null'])

        if not self.blank and value in validators.EMPTY_VALUES:
            raise exceptions.ValidationError(self.error_messages['blank'])

    def clean(self, value, model_instance):
        """
        Convert the value's type and run validation. Validation errors from to_python
        and validate are propagated. The correct value is returned if no error is
        raised.
        """
        value = self.to_python(value)
        self.validate(value, model_instance)
        self.run_validators(value)
        return value

   

    def unique(self):
        return self._unique or self.primary_key
    unique = property(unique)

    def set_attributes_from_name(self, name):
        self.name = name
        if self.xml_element_name is None:
            self.xml_element_name = self.name
        self.attname, self.column = self.get_attname_column()
        if self.verbose_name is None and name:
            self.verbose_name = name.replace('_', ' ')

    def contribute_to_class(self, cls, name):
        self.set_attributes_from_name(name)
        self.model = cls
        cls._meta.add_field(self)
        if self.choices:
            setattr(cls, 'get_%s_display' % self.name, curry(cls._get_FIELD_display, field=self))

    def get_attname(self):
        return self.name

    def get_attname_column(self):
        attname = self.get_attname()
        column = attname
        return attname, column

    def get_cache_name(self):
        return '_%s_cache' % self.name

    def get_internal_type(self):
        return self.__class__.__name__


    def has_default(self):
        "Returns a boolean of whether this field has a default value."
        return self.default is not NOT_PROVIDED

    def get_default(self):
        "Returns the default value for this field."
        if self.has_default():
            if callable(self.default):
                return self.default()
            return force_unicode(self.default, strings_only=True)
        #rh if not self.empty_strings_allowed or (self.null):
        #rh   return None
        #rh return ""
        return None

    def get_validator_unique_lookup_type(self):
        return '%s__exact' % self.name

    def get_choices(self, include_blank=True, blank_choice=BLANK_CHOICE_DASH):
        """Returns choices with a default blank choices included, for use
        as SelectField choices for this field."""
        first_choice = include_blank and blank_choice or []
        if self.choices:
            return first_choice + list(self.choices)
        rel_model = self.rel.to
        if hasattr(self.rel, 'get_related_field'):
            lst = [(getattr(x, self.rel.get_related_field().attname), smart_unicode(x)) for x in rel_model._default_manager.complex_filter(self.rel.limit_choices_to)]
        else:
            lst = [(x._get_pk_val(), smart_unicode(x)) for x in rel_model._default_manager.complex_filter(self.rel.limit_choices_to)]
        return first_choice + lst

    def get_choices_default(self):
        return self.get_choices()

    def get_flatchoices(self, include_blank=True, blank_choice=BLANK_CHOICE_DASH):
        "Returns flattened choices with a default blank choice included."
        first_choice = include_blank and blank_choice or []
        return first_choice + list(self.flatchoices)

    def _get_val_from_obj(self, obj):
        if obj is not None:
            return getattr(obj, self.attname)
        else:
            return self.get_default()

    def value_to_string(self, obj):
        """
        Returns a string value of this field from the passed obj.
        This is used by the serialization framework.
        """
        return smart_unicode(self._get_val_from_obj(obj))

    def bind(self, fieldmapping, original, bound_field_class):
        return bound_field_class(self, fieldmapping, original)

    def _get_choices(self):
        if hasattr(self._choices, 'next'):
            choices, self._choices = tee(self._choices)
            return choices
        else:
            return self._choices
    choices = property(_get_choices)

    def _get_flatchoices(self):
        """Flattened version of choices tuple."""
        flat = []
        for choice, value in self.choices:
            if isinstance(value, (list, tuple)):
                flat.extend(value)
            else:
                flat.append((choice,value))
        return flat
    flatchoices = property(_get_flatchoices)

    def save_form_data(self, instance, data):
        setattr(instance, self.name, data)

    

    def value_from_object(self, obj):
        "Returns the value of this field in the given model instance."
        return getattr(obj, self.attname)
    
    
    def get_verbose_name(self, language):
        
        if isinstance(self.verbose_name, dict):
            
            if language in self.verbose_name:
                return to_unicode_utf8(self.verbose_name[language])
            else:
                return to_unicode_utf8(self.verbose_name.itervalues().next())            
        else:
            return to_unicode_utf8(self.verbose_name)    

    def get_display_value(self,value, language):
        
        if self._choices:
            for item in self._choices:
                if value == item[0]:
                    display_value_dict = item[1]
                    if language in display_value_dict:
                        return display_value_dict[language]
                    else:
                        return display_value_dict.itervalues().next()
        return value    

import decimal


class DecimalField(Field):
    empty_strings_allowed = False
    default_error_messages = {
        'invalid': _(u"'%s' value must be a decimal number."),
    }
    description = _("Decimal number")

    def __init__(self, verbose_name=None, name=None, max_digits=None,
                 decimal_places=None, **kwargs):
        self.max_digits, self.decimal_places = max_digits, decimal_places
        
        
        self.quatizer = "".join("0" for i in range(self.decimal_places - 1))
        self.quatizer = "." + self.quatizer + "1"
        Field.__init__(self, verbose_name, name, **kwargs)

    def get_internal_type(self):
        return "DecimalField"

    def to_python(self, value):
        if value is None:
            return value
        try:
            if isinstance(value, float):
                value = str(value)
             
            return decimal.Decimal(value).quantize(decimal.Decimal(self.quatizer), rounding=decimal.ROUND_DOWN)
        except decimal.InvalidOperation:
            msg = self.error_messages['invalid'] % str(value)
            raise exceptions.ValidationError(msg)

    def _format(self, value):
        if isinstance(value, basestring) or value is None:
            return value
        else:
            return self.format_number(value)

    def format_number(self, value):
        """
        Formats a number into a string with the requisite number of digits and
        decimal places.
        """
        # Method moved to django.db.backends.util.
        #
        # It is preserved because it is used by the oracle backend
        # (django.db.backends.oracle.query), and also for
        # backwards-compatibility with any external code which may have used
        # this method.
        from django.db.backends import util
        return util.format_number(value, self.max_digits, self.decimal_places)

    def describe(self, described_classes = None, recursive = False):
        description = super(DecimalField, self).describe(described_classes = described_classes, recursive = recursive)
        description['decimal_places'] = self.decimal_places
        return description
    
class CharField(Field):
    description = _("String (up to %(max_length)s)")

    def __init__(self, *args, **kwargs):
        super(CharField, self).__init__(*args, **kwargs)
        if self.max_length is not None:
            self.validators.append(validators.MaxLengthValidator(self.max_length))

    def get_internal_type(self):
        return "CharField"

    def to_python(self, value):
        if isinstance(value, basestring) or value is None:
            return value
        return smart_unicode(value)


    def formfield(self, **kwargs):
        # Passing max_length to forms.CharField means that the value's length
        # will be validated twice. This is considered acceptable since we want
        # the value in the form field (to pass into widget for example).
        defaults = {'max_length': self.max_length}
        defaults.update(kwargs)
        return super(CharField, self).formfield(**defaults)




class IntegerField(Field):
    empty_strings_allowed = False
    default_error_messages = {
        'invalid': _("This value must be an integer."),
    }
    description = _("Integer")

    def get_internal_type(self):
        return "IntegerField"

    def to_python(self, value):
        if value is None:
            return value
        try:
            return int(value)
        except (TypeError, ValueError):
            raise exceptions.ValidationError(self.error_messages['invalid'])

        
        
class FloatField(Field):
    
    empty_strings_allowed = False
    default_error_messages = {
        'invalid': _("This value must be a float."),
    }
    description = _("Floating point number")

    def get_internal_type(self):
        return "FloatField"

    def to_python(self, value):
        if value is None:
            return value
        try:
            return float(value)
        except (TypeError, ValueError):       
            raise exceptions.ValidationError(self.error_messages['invalid'])
        
        

ansi_date_re = re.compile(r'^\d{4}-\d{1,2}-\d{1,2}$')

class DateField(Field):
    description = _("Date (without time)")

    empty_strings_allowed = False
    default_error_messages = {
        'invalid': _('Enter a valid date in YYYY-MM-DD format.'),
        'invalid_date': _('Invalid date: %s'),
    }
    def __init__(self, verbose_name=None, name=None, auto_now=False, auto_now_add=False, **kwargs):
        self.auto_now, self.auto_now_add = auto_now, auto_now_add
        #HACKs : auto_now_add/auto_now should be done as a default or a pre_save.
        if auto_now or auto_now_add:
            kwargs['editable'] = False
            kwargs['blank'] = True
        Field.__init__(self, verbose_name, name, **kwargs)

    def get_internal_type(self):
        return "DateField"

    def to_python(self, value):
        if value is None:
            return value
        if isinstance(value, datetime.datetime):
            return value.date()
        if isinstance(value, datetime.date):
            return value

        if not ansi_date_re.search(value):
            raise exceptions.ValidationError(self.error_messages['invalid'])
        # Now that we have the date string in YYYY-MM-DD format, check to make
        # sure it's a valid date.
        # We could use time.strptime here and catch errors, but datetime.date
        # produces much friendlier error messages.
        year, month, day = map(int, value.split('-'))
        try:
            return datetime.date(year, month, day)
        except ValueError, e:
            msg = self.error_messages['invalid_date'] % _(str(e))
            raise exceptions.ValidationError(msg)


    #def contribute_to_class(self, cls, name):
    #    super(DateField,self).contribute_to_class(cls, name)
    #    if not self.null:
    #        setattr(cls, 'get_next_by_%s' % self.name,
    #            curry(cls._get_next_or_previous_by_FIELD, field=self, is_next=True))
    #        setattr(cls, 'get_previous_by_%s' % self.name,
    #            curry(cls._get_next_or_previous_by_FIELD, field=self, is_next=False))


    def value_to_string(self, obj):
        val = self._get_val_from_obj(obj)
        if val is None:
            data = ''
        else:
            data = datetime_safe.new_date(val).strftime("%Y-%m-%d")
        return data


    def add_to_instance(self, instance, dict):   
        
        if self.name in dict:
            str_value = dict[self.name]
        
            year, month, day = map(int, str_value.split('-'))
            try:
                value = datetime.date(year, month, day)
            except ValueError:
                raise exceptions.ValidationError("Value [%s]is incorrect date format " % str_value)     
    
            
            setattr(instance, self.name, value)

    def unserialize_from_xml(self, instance, element):
        
        field_element = element.find(self.name)
        if field_element:
            str_value = field_element.text
    
            year, month, day = map(int, str_value.split('-'))
            try:
                value = datetime.date(year, month, day)
            except ValueError:
                raise exceptions.ValidationError("Value [%s]is incorrect date format " % str_value)     
    
            
            setattr(instance, self.name, value)
       
class TimeField(Field):
    description = _("Time")

    empty_strings_allowed = False
    default_error_messages = {
        'invalid': _('Enter a valid time in HH:MM[:ss[.uuuuuu]] format.'),
    }
    def __init__(self, verbose_name=None, name=None, auto_now=False, auto_now_add=False, **kwargs):
        self.auto_now, self.auto_now_add = auto_now, auto_now_add
        if auto_now or auto_now_add:
            kwargs['editable'] = False
        Field.__init__(self, verbose_name, name, **kwargs)

    def get_internal_type(self):
        return "TimeField"

    def to_python(self, value):
        if value is None:
            return None
        if isinstance(value, datetime.time):
            return value
        if isinstance(value, datetime.datetime):
            # Not usually a good idea to pass in a datetime here (it loses
            # information
            return value.time()

        # Attempt to parse a datetime:
        value = smart_str(value)
        # split usecs, because they are not recognized by strptime.
        if '.' in value:
            try:
                value, usecs = value.split('.')
                usecs = int(usecs)
            except ValueError:
                raise exceptions.ValidationError(self.error_messages['invalid'])
        else:
            usecs = 0
        kwargs = {'microsecond': usecs}

        try: # Seconds are optional, so try converting seconds first.
            return datetime.time(*time.strptime(value, '%H:%M:%S')[3:6],
                                 **kwargs)
        except ValueError:
            try: # Try without seconds.
                return datetime.time(*time.strptime(value, '%H:%M')[3:5],
                                         **kwargs)
            except ValueError:
                raise exceptions.ValidationError(self.error_messages['invalid'])


    def value_to_string(self, obj):
        val = self._get_val_from_obj(obj)
        if val is None:
            data = ''
        else:
            data = val.strftime("%H:%M:%S")
        return data

class DateTimeField(DateField):
    default_error_messages = {
        'invalid': _(u'Enter a valid date/time in YYYY-MM-DD HH:MM[:ss[.uuuuuu]] format.'),
    }
    description = _("Date (with time)")

    @classmethod
    def _conv_with_seconds_t(cls, value, usecs):
        kwargs = {'microsecond': usecs}
        return datetime.datetime(*time.strptime(value, '%Y-%m-%dT%H:%M:%S')[:6],**kwargs)

    @classmethod
    def _conv_with_seconds(cls, value, usecs):
        kwargs = {'microsecond': usecs}
        return datetime.datetime(*time.strptime(value, '%Y-%m-%d %H:%M:%S')[:6],**kwargs)

    @classmethod
    def _conv_without_seconds_t(cls, value, usecs):
        kwargs = {'microsecond': usecs}        
        return datetime.datetime(*time.strptime(value, '%Y-%m-%dT%H:%M')[:5],**kwargs)

    @classmethod
    def _conv_without_seconds(cls, value, usecs):
        kwargs = {'microsecond': usecs}        
        return datetime.datetime(*time.strptime(value, '%Y-%m-%d %H:%M')[:5],**kwargs)

    @classmethod
    def _conv_without_time(cls, value, usecs):
        kwargs = {'microsecond': usecs}        
        return datetime.datetime(*time.strptime(value, '%Y-%m-%d')[:3],**kwargs)

        
        

    def _convert(self, value, usecs):
        conversions_meth_list = [self._conv_with_seconds_t,self._conv_with_seconds, self._conv_without_seconds_t, self._conv_without_seconds, self._conv_without_time]
        
        for convert_meth in conversions_meth_list:
            try:
                return convert_meth(value, usecs)
            except ValueError:
                pass
        raise ValueError()   

    def get_internal_type(self):
        return "DateTimeField"

     
    
    def to_python(self, value):
        if value is None:
            return value
        if isinstance(value, datetime.datetime):
            return value
        if isinstance(value, datetime.date):
            return datetime.datetime(value.year, value.month, value.day)

        # Attempt to parse a datetime:
        value = smart_str(value)
        try:
            import dateutil.parser
            return dateutil.parser.parse(value)
        except ValueError:
            pass
        
        # split usecs, because they are not recognized by strptime.
        if '.' in value:
            try:
                value, usecs = value.split('.')
                usecs = int(usecs)
            except ValueError:
                raise exceptions.ValidationError(self.error_messages['invalid'])
        else:
            usecs = 0
        try:
            return self._convert(value, usecs)
        except ValueError:
            raise exceptions.ValidationError(self.error_messages['invalid'])
    
    def value_to_string(self, obj):
        val = self._get_val_from_obj(obj)
        if val is None:
            data = ''
        else:
            d = datetime_safe.new_datetime(val)
            data = d.strftime('%Y-%m-%dT%H:%M:%S')
        return data

class TextField(Field):
    description = _("Text")

    def get_internal_type(self):
        return "TextField"
    
class BooleanField(Field):
    empty_strings_allowed = False
    default_error_messages = {
        'invalid': _(u'This value must be either True or False.'),
    }
    description = _("Boolean (Either True or False)")
    def __init__(self, *args, **kwargs):
        kwargs['blank'] = True
        if 'default' not in kwargs and not kwargs.get('null'):
            kwargs['default'] = False
        Field.__init__(self, *args, **kwargs)

    def get_internal_type(self):
        return "BooleanField"

    def to_python(self, value):
        if value in (True, False):
            # if value is 1 or 0 than it's equal to True or False, but we want
            # to return a true bool for semantic reasons.
            return bool(value)
        if value in ('t', 'True', '1'):
            return True
        if value in ('f', 'False', '0'):
            return False
        raise exceptions.ValidationError(self.error_messages['invalid'])


    def value_to_string(self, obj):
        val = self._get_val_from_obj(obj)
        if val is None:
            data = ''
        else:
            data = "%s" % val
        return data

    