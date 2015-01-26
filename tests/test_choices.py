import prepare_settings
        
from django.utils.translation import activate, deactivate        
        
from unittest import TestCase, main   

from django_documents.documents import Model
from django_documents import fields

PARKING_FACILITIES_CHOICES_TR = [('OPS', { 'nl':'Eigen parkeerplaats beschikbaar', "de":"Eigene parkplatz", "en": "Private Parkplace"}),
                                 ('FPW', { 'nl': 'Gratis parkeren openbare weg', "de":"Eigene parkplatz", "en": "Private Parkplace"}), 
                                 ('PP',  { 'nl': 'Betaald parkeren', 'de': 'Zahled parkieren',"en": "Paid parking"})] 



class ModelWithChoices(Model):
    name = fields.CharField(choices = PARKING_FACILITIES_CHOICES_TR)




class ChoicesTest(TestCase):


    def testLanguagedChoices(self):
        activate('nl')
        try:
            modelWithChoices =  ModelWithChoices()
            modelWithChoices.name = 'OPS'
            display_name = modelWithChoices.get_name_display()
            self.assertEqual(display_name, 'Eigen parkeerplaats beschikbaar')
            modelWithChoices.full_clean()
        
            describe = ModelWithChoices._meta.describe()
            import simplejson
            
            print simplejson.dumps(describe)
            
        finally:
            deactivate

if __name__ == '__main__':
    main()    