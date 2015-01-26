import prepare_settings
        
import simplejson as json
        
from unittest import TestCase, main        
from django_documents.serializer import PythonSerializer, PythonDeserializer,XMLSerializer, XMLUnserializer, JsonSerializer,  JsonUnSerializer
from django_documents import documents, fields, related

class Address(documents.Model):
    street = fields.CharField()
    localityName = fields.CharField()

class Image(documents.Model):
    url = fields.CharField()

class Organisation(documents.Model):
    postAddress = related.OneOf(Address, verbose_name ={"nl": "Post adres"}, is_group = True)
    images = related.ListOf(Image, is_group = True, verbose_name ={"nl": "Afbeeldingen"})


class TestGroupMeta(TestCase):

    def testMeta(self):
        
        meta_description = Organisation._meta.describe()
        print meta_description
        print json.dumps(meta_description)

if __name__ == '__main__':
    main()   