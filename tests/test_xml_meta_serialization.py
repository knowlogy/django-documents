import prepare_settings
        
from unittest import TestCase, main        
from django_documents.documents import Model
from django_documents import fields, related
from django_documents.serializer import XMLSerializer, XMLUnserializer
from elementtree import ElementTree

import types

class Location(Model):
    
    lat = fields.FloatField( xml_element_name = 'latitude')
    lng = fields.FloatField( xml_element_name = 'longitude')

#    class Meta:
#        xml_attr = {'projection': 'WGS84'}
#        xml_element_name = 'mylocation'     


# what are the rules of element names
# property_name, class meta xml_element_name,   fields xml_element_name

class Poi(Model):
    
    length = fields.IntegerField(meta = {'dimension':"dm"})
    location = related.OneOf(Location, meta = {'projection': 'WGS84'}) # should overwrite default location xml_element_name
    descriptions = related.MapOf(types.StringType, xml_key_attr_name = "language")
    
    class Meta:
        xml_element_name = "poi"   


class Restaurant(Model):
    
    name = fields.CharField(max_length = 20, blank = False, null= False, verbose_name = {"nl": "Naam","de":"Name","en": "Name"})

class XMLMetaSerializationTestCase(TestCase):

    def test_correct_serialization_meta_attributes(self):
        poi = Poi()
        poi.length = 10
        poi.location = Location( lat= '6.8989', lng = '5.344')
        poi.descriptions = {"nl": "Nederlands", "de": "Duits"}
        
        xml_repr = XMLSerializer().serialize(poi)
        
        print xml_repr
        
        poi_xml_tree = ElementTree.XML(xml_repr.encode('utf-8'))
        self.assertEqual(poi_xml_tree.tag, 'poi')
        length_element = poi_xml_tree.find('length')
        self.assertTrue( length_element is not None)
        self.assertTrue( 'dimension' in length_element.attrib)
        self.assertEqual(length_element.attrib['dimension'], 'dm')
        
        location_element = poi_xml_tree.find('location')
        self.assertTrue( location_element is not None)
        self.assertTrue( 'projection' in location_element.attrib)
        self.assertEqual(location_element.attrib['projection'], 'WGS84')
        

        unser_poi = XMLUnserializer().unserialize(xml_repr, Poi)
        self.assertEqual(poi.length, unser_poi.length)
        
        
if __name__ == '__main__':
    main()   