import prepare_settings
        
from unittest import TestCase, main  

from django_documents import fields
from django_documents import documents as persistentmodels


class Person(persistentmodels.Model):
    """
    this is the definition of a simple model
    """
    first_name = fields.CharField()
    last_name = fields.CharField()     

            
class PystacheTest(TestCase):
    
    """
    These tests check if compatibility with mustache templates
    """

    def test_mustache_rendering_simple(self):
        import pystache
        
        person = Person(first_name = "baruch", last_name="Spinoza")
        result =  pystache.render('Hi {{person.first_name}} {{ person.last_name}}!', {'person': person})
        
        self.assertEqual("Hi baruch Spinoza!", result)
        

    def test_mustache_rendering_list(self):
        import pystache
        from model_definitions_for_test import ModelWithListOffStringType
        
        model = ModelWithListOffStringType(name = "test", listOfString= ["aap","noot","mies"])
        model.c = "yes"
        
        def count():
            return "10"
        
        #partial = "<h1></h1>";
        
        result =  pystache.render('Hi {{ count }} {{model.name}} {{#model.listOfString}}{{.}} {{count}} {{/model.listOfString}}', {'model': model,'count': count})
        print result
    
    
    def test_mustache_rendering_list3(self):
        import pystache
        from model_definitions_for_test import ModelWithListOffStringType
        
        model = ModelWithListOffStringType(name = "test", listOfString= ["aap","noot","mies"])
        model.c = "yes"
        
        def count():
            return "10"
        
        hello = "<h1>{{.}} {{count}}</h1>";
        result =  pystache.render('Hi {{ count }} {{model.name}} {{#model.listOfString}} {{>hello}} {{/model.listOfString}}', {'model': model,'count': count}, partials = {"hello": hello})
        print "partial " + result
    
    
    def test_mustache_rendering_list2(self):
        import pystache
        from model_definitions_for_test import ModelWithListOffStringType
        
        model = ModelWithListOffStringType(name = "test", listOfString= ["aap","noot","mies"])
        model.c = "yes"
        
        def count():
            return "10"

                
        result =  pystache.render('test', {'model': model,'count': count})
        print result
        
        
        
if __name__ == '__main__':
    main()    