import prepare_settings
import types
        
from unittest import TestCase, main        
from django_documents.documents import Model, ObjectValidationError
from django_documents import related, fields

class Image(Model):
    thumbnail_url = fields.CharField(max_length = 300, null = False, blank = False)
    image_url = fields.CharField(max_length = 300, null = False, blank = False)
   

class Images(Model):
    urls = related.ListOf(Image, verbose_name = 'image', null = True, blank = True)   
    
class ToValidateChild(Model):    
    
    childname = fields.CharField(max_length = 300, null = False, blank = False)
    
class ToValidate(Model):
    name = fields.CharField( max_length = 300, null = False, blank = False)
    child = related.OneOf(ToValidateChild, null = False)
        

class ToValidateListOfChilds(Model):
    name = fields.CharField( max_length = 300, null = False, blank = False)
    childs = related.ListOf(ToValidateChild, null = False, min_length = 2, max_length = 100)
    

class Address(Model):
    street = fields.CharField( max_length = 30, null = False, blank = False)
    zipcode  = fields.CharField( max_length = 10, null = False, blank = False) 
    
class Poi(Model):
    """
    class poi presents the minimal set of the default properties for a poi
    """
    images = related.OneOf(Images, null = True, blank = True)
    address = related.OneOf(Address)




class ValidationOneOfRequiredField(TestCase):

    def test_validation_error_on_required_oneof(self):
        
        toValidate = ToValidate(name="test")
        try:
            toValidate.full_clean()
            self.fail("expected a validation error")
        except ObjectValidationError, oe:   
            self.assertTrue('child' in oe.messages)
            self.assertTrue(hasattr(toValidate, '_errors'))
            
    def test_validation_error_invalide_oneof(self):
        
        toValidate = ToValidate(name="test")
        toValidate.child = ToValidateChild()
        try:
            toValidate.full_clean()
            self.fail("expected a validation error")
        except ObjectValidationError, oe:    
            print oe.message_dict
            
    def test_novalidation_correct_oneof(self):
        
        toValidate = ToValidate(name="test")
        toValidate.child = ToValidateChild(childname = "test")
        toValidate.full_clean()
    

class ToValidateOneOfNull(Model):
    child = related.OneOf(ToValidateChild, blank = True)

class ValidationOneOfNotRequiredField(TestCase):

    def test_validation_error_on_required_oneof(self):
        
        toValidate = ToValidateOneOfNull()
        toValidate.full_clean()



class ValidationOfListOfChilds(TestCase):

    def test_correct(self):
        toValidateListOfChilds = ToValidateListOfChilds()
        toValidateListOfChilds.name = "test"
        toValidateListOfChilds.childs = [ToValidateChild(childname = "1"), ToValidateChild(childname = "1")]
        toValidateListOfChilds.full_clean()
        
    def test_incorrect_minlength(self):
        toValidateListOfChilds = ToValidateListOfChilds()
        toValidateListOfChilds.name = "test"
        toValidateListOfChilds.childs = [ToValidateChild(childname = "1")]
        try:    
            toValidateListOfChilds.full_clean()
            self.fail("expected  a object validation error")
        except ObjectValidationError:
            pass
            from persistent.serializer import JsonSerializer
            print JsonSerializer().serialize(toValidateListOfChilds)
        
    def test_incorrect_empty_list_minlength(self):
        toValidateListOfChilds = ToValidateListOfChilds()
        toValidateListOfChilds.name = "test"
        toValidateListOfChilds.childs = []
        try:    
            toValidateListOfChilds.full_clean()
            self.fail("expected  a object validation error")
        except ObjectValidationError:
            pass
            from persistent.serializer import JsonSerializer
            print JsonSerializer().serialize(toValidateListOfChilds)
        

    def test_validation_error_incorrect_listitem(self):
        toValidateListOfChilds = ToValidateListOfChilds()
        toValidateListOfChilds.name = "test"
        toValidateListOfChilds.childs = [ToValidateChild()]
        try:
            toValidateListOfChilds.full_clean()
            self.fail("expected  a object validation error")
        except ObjectValidationError:
            pass    
    

class ValidationEmptyList(TestCase):

    def test_correct_validation(self):
        
        
        poi = Poi()
        poi.images = Images()
        poi.address = Address()
        try: 
            poi.full_clean()
        except ObjectValidationError, ove:
            self.assertTrue('address' in ove.messages)
            print ove
        
        
        
        
LANGUAGECODES = (("nl", "Nederlands"),("de","Duits"),)

class ToValidateList(Model):

    language_codes = related.ListOf(types.StringType, choices = LANGUAGECODES)

class ListValidationTestCase(TestCase):
    
    def testListStringChoicesValidation(self):
        
        toValidateList = ToValidateList()
        toValidateList.language_codes = ['nl',"de"]
        
        toValidateList.full_clean()
    
    def testListStringIncorrectChoicesValidation(self):
        
        toValidateList = ToValidateList()
        toValidateList.language_codes = ['nl',"ce"]
        
        try:
            toValidateList.full_clean()
            self.fail("expected exception")
        except ObjectValidationError, ove:
            from persistent.serializer import JsonSerializer
            print "Errors: %s" % ove
            print JsonSerializer().serialize(toValidateList)
            self.assertTrue('language_codes' in toValidateList._errors)
        

class ToValidateNotRequiredOneOfChild(Model):
    child = related.OneOf(ToValidateChild, blank = True)
    
    
class ValidationNotRequiredOneOfChildTestCase(TestCase):
    
    def testValidation(self):
        
        testObject = ToValidateNotRequiredOneOfChild()
        testObject.full_clean()    
        
        
if __name__ == '__main__':
    main()   