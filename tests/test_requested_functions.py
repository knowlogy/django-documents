import prepare_settings
        
from unittest import TestCase, main   

from django_documents.documents import Model
from django_documents import fields, related
from types import StringType



charField = fields.CharField(max_length = 3)

class ListOfCharFields(Model):
    names = related.ListOf(StringType )




class ChoicesTest(TestCase):


    def testLanguagedChoices(self):
        loc = ListOfCharFields()
        loc.names = ["hello"]
        
        
if __name__ == '__main__':
    main()    