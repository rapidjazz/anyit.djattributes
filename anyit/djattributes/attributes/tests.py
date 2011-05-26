import unittest
from django.test import TestCase
from django.db import models
from django.db.models import Model
from models import *
"""
These tests include the tests taken from http://djangosnippets.org/snippets/1694/
and those for the attributes module.
"""

class TestingModel(models.Model):
    pickle_field = PickledObjectField()
    compressed_pickle_field = PickledObjectField(compress=True)
    default_pickle_field = PickledObjectField(default=({1: 1, 2: 4, 3: 6, 4: 8, 5: 10}, 'Hello World', (1, 2, 3, 4, 5), [1, 2, 3, 4, 5]))

class TestCustomDataType(str):
    pass

class PickledObjectFieldTests(TestCase):
    def setUp(self):
        self.testing_data = (
            {1:2, 2:4, 3:6, 4:8, 5:10},
            'Hello World',
            (1, 2, 3, 4, 5),
            [1, 2, 3, 4, 5],
            TestCustomDataType('Hello World'),
        )
        return super(PickledObjectFieldTests, self).setUp()
    
    def testDataIntegriry(self):
        """
        Tests that data remains the same when saved to and fetched from
        the database, whether compression is enabled or not.
        
        """
        for value in self.testing_data:
            model_test = TestingModel(pickle_field=value, compressed_pickle_field=value)
            model_test.save()
            model_test = TestingModel.objects.get(id__exact=model_test.id)
            # Make sure that both the compressed and uncompressed fields return
            # the same data, even thought it's stored differently in the DB.
            self.assertEquals(value, model_test.pickle_field)
            self.assertEquals(value, model_test.compressed_pickle_field)
            model_test.delete()
        
        # Make sure the default value for default_pickled_field gets stored
        # correctly and that it isn't converted to a string.
        model_test = TestingModel()
        model_test.save()
        model_test = TestingModel.objects.get(id__exact=model_test.id)
        self.assertEquals(({1: 1, 2: 4, 3: 6, 4: 8, 5: 10}, 'Hello World', (1, 2, 3, 4, 5), [1, 2, 3, 4, 5]), model_test.default_pickle_field)


    def testLookups(self):
        """
        Tests that lookups can be performed on data once stored in the
        database, whether compression is enabled or not.
        
        One problem with cPickle is that it will sometimes output
        different streams for the same object, depending on how they are
        referenced. It should be noted though, that this does not happen
        for every object, but usually only with more complex ones.
                
        >>> from pickle import dumps
        >>> t = ({1: 1, 2: 4, 3: 6, 4: 8, 5: 10}, \
        ... 'Hello World', (1, 2, 3, 4, 5), [1, 2, 3, 4, 5])
        >>> dumps(({1: 1, 2: 4, 3: 6, 4: 8, 5: 10}, \
        ... 'Hello World', (1, 2, 3, 4, 5), [1, 2, 3, 4, 5]))
        "((dp0\nI1\nI1\nsI2\nI4\nsI3\nI6\nsI4\nI8\nsI5\nI10\nsS'Hello World'\np1\n(I1\nI2\nI3\nI4\nI5\ntp2\n(lp3\nI1\naI2\naI3\naI4\naI5\natp4\n."
        >>> dumps(t)
        "((dp0\nI1\nI1\nsI2\nI4\nsI3\nI6\nsI4\nI8\nsI5\nI10\nsS'Hello World'\np1\n(I1\nI2\nI3\nI4\nI5\ntp2\n(lp3\nI1\naI2\naI3\naI4\naI5\natp4\n."
        >>> # Both dumps() are the same using pickle.

        >>> from cPickle import dumps
        >>> t = ({1: 1, 2: 4, 3: 6, 4: 8, 5: 10}, 'Hello World', (1, 2, 3, 4, 5), [1, 2, 3, 4, 5])
        >>> dumps(({1: 1, 2: 4, 3: 6, 4: 8, 5: 10}, 'Hello World', (1, 2, 3, 4, 5), [1, 2, 3, 4, 5]))
        "((dp1\nI1\nI1\nsI2\nI4\nsI3\nI6\nsI4\nI8\nsI5\nI10\nsS'Hello World'\np2\n(I1\nI2\nI3\nI4\nI5\ntp3\n(lp4\nI1\naI2\naI3\naI4\naI5\nat."
        >>> dumps(t)
        "((dp1\nI1\nI1\nsI2\nI4\nsI3\nI6\nsI4\nI8\nsI5\nI10\nsS'Hello World'\n(I1\nI2\nI3\nI4\nI5\nt(lp2\nI1\naI2\naI3\naI4\naI5\natp3\n."
        >>> # But with cPickle the two dumps() are not the same!
        >>> # Both will generate the same object when loads() is called though.

        We can solve this by calling deepcopy() on the value before
        pickling it, as this copies everything to a brand new data
        structure.
        
        >>> from cPickle import dumps
        >>> from copy import deepcopy
        >>> t = ({1: 1, 2: 4, 3: 6, 4: 8, 5: 10}, 'Hello World', (1, 2, 3, 4, 5), [1, 2, 3, 4, 5])
        >>> dumps(deepcopy(({1: 1, 2: 4, 3: 6, 4: 8, 5: 10}, 'Hello World', (1, 2, 3, 4, 5), [1, 2, 3, 4, 5])))
        "((dp1\nI1\nI1\nsI2\nI4\nsI3\nI6\nsI4\nI8\nsI5\nI10\nsS'Hello World'\np2\n(I1\nI2\nI3\nI4\nI5\ntp3\n(lp4\nI1\naI2\naI3\naI4\naI5\nat."
        >>> dumps(deepcopy(t))
        "((dp1\nI1\nI1\nsI2\nI4\nsI3\nI6\nsI4\nI8\nsI5\nI10\nsS'Hello World'\np2\n(I1\nI2\nI3\nI4\nI5\ntp3\n(lp4\nI1\naI2\naI3\naI4\naI5\nat."
        >>> # Using deepcopy() beforehand means that now both dumps() are idential.
        >>> # It may not be necessary, but deepcopy() ensures that lookups will always work.
        
        Unfortunately calling copy() alone doesn't seem to fix the
        problem as it lies primarily with complex data types.
        
        >>> from cPickle import dumps
        >>> from copy import copy
        >>> t = ({1: 1, 2: 4, 3: 6, 4: 8, 5: 10}, 'Hello World', (1, 2, 3, 4, 5), [1, 2, 3, 4, 5])
        >>> dumps(copy(({1: 1, 2: 4, 3: 6, 4: 8, 5: 10}, 'Hello World', (1, 2, 3, 4, 5), [1, 2, 3, 4, 5])))
        "((dp1\nI1\nI1\nsI2\nI4\nsI3\nI6\nsI4\nI8\nsI5\nI10\nsS'Hello World'\np2\n(I1\nI2\nI3\nI4\nI5\ntp3\n(lp4\nI1\naI2\naI3\naI4\naI5\nat."
        >>> dumps(copy(t))
        "((dp1\nI1\nI1\nsI2\nI4\nsI3\nI6\nsI4\nI8\nsI5\nI10\nsS'Hello World'\n(I1\nI2\nI3\nI4\nI5\nt(lp2\nI1\naI2\naI3\naI4\naI5\natp3\n."

        """
        for value in self.testing_data:
            model_test = TestingModel(pickle_field=value, compressed_pickle_field=value)
            model_test.save()
            # Make sure that we can do an ``exact`` lookup by both the
            # pickle_field and the compressed_pickle_field.
            model_test = TestingModel.objects.get(pickle_field__exact=value, compressed_pickle_field__exact=value)
            self.assertEquals(value, model_test.pickle_field)
            self.assertEquals(value, model_test.compressed_pickle_field)
            # Make sure that ``in`` lookups also work correctly.
            model_test = TestingModel.objects.get(pickle_field__in=[value,], compressed_pickle_field__in=[value,])
            # model does not support this ... not even if trivially implemented :)
            self.assertEquals(value, model_test.pickle_field)
            self.assertEquals(value, model_test.compressed_pickle_field)
            # Make sure that ``is_null`` lookups are working.
            self.assertEquals(1, TestingModel.objects.filter(pickle_field__isnull=False).count())
            self.assertEquals(0, TestingModel.objects.filter(pickle_field__isnull=True).count())
            model_test.delete()
        
        # Make sure that lookups of the same value work, even when referenced
        # differently. See the above docstring for more info on the issue.
        value = ({1: 1, 2: 4, 3: 6, 4: 8, 5: 10}, 'Hello World', (1, 2, 3, 4, 5), [1, 2, 3, 4, 5])
        model_test = TestingModel(pickle_field=value, compressed_pickle_field=value)
        model_test.save()
        # Test lookup using an assigned variable.
        model_test = TestingModel.objects.get(pickle_field__exact=value)
        self.assertEquals(value, model_test.pickle_field)
        # Test lookup using direct input of a matching value.
        model_test = TestingModel.objects.get(
            pickle_field__exact = ({1: 1, 2: 4, 3: 6, 4: 8, 5: 10}, 'Hello World', (1, 2, 3, 4, 5), [1, 2, 3, 4, 5]),
            compressed_pickle_field__exact = ({1: 1, 2: 4, 3: 6, 4: 8, 5: 10}, 'Hello World', (1, 2, 3, 4, 5), [1, 2, 3, 4, 5]),
        )
        self.assertEquals(value, model_test.pickle_field)
        model_test.delete()

class AttributeTest(unittest.TestCase):

    def setUp(self):
        self.at = attr.create_type("test_int","test_description","int")
        self.atf = attr.create_type("test_float","test_description","float")
        self.ats = attr.create_type("test_string","test_description","string")
        self.atu = attr.create_type("test_unicode","test_description","unicode")
        self.att = attr.create_type("test_text","test_description","text")
        self.atc = attr.create_type("test_class","test_description","class")
        self.atd = attr.create_type("test_contenttype","test_description","contenttype")

        return super(AttributeTest, self).setUp()

    def test_attribute_creation(self):
        self.assertEqual( self.at.name, "test_int" )
        self.assertEqual( self.at.description , "test_description" )
        self.assertEqual( self.at.internal_type , "int" )
        self.assertEqual( isinstance(self.at.pk, long) or isinstance(self.at.pk, int), True )

        self.assertEqual( self.atf.name, "test_float" )
        self.assertEqual( self.atf.description , "test_description" )
        self.assertEqual( self.atf.internal_type , "float" )
        self.assertEqual( isinstance(self.atf.pk, long) or isinstance(self.atf.pk, int), True )

        self.assertEqual( self.ats.name, "test_string" )
        self.assertEqual( self.ats.description , "test_description" )
        self.assertEqual( self.ats.internal_type , "string" )
        self.assertEqual( isinstance(self.ats.pk, long) or isinstance(self.ats.pk, int), True )

        self.assertEqual( self.atu.name, "test_unicode" )
        self.assertEqual( self.atu.description , "test_description" )
        self.assertEqual( self.atu.internal_type , "unicode" )
        self.assertEqual( isinstance(self.atu.pk, long) or isinstance(self.atu.pk, int), True )

        self.assertEqual( self.att.name, "test_text" )
        self.assertEqual( self.att.description , "test_description" )
        self.assertEqual( self.att.internal_type , "text" )
        self.assertEqual( isinstance(self.atu.pk, long) or isinstance(self.atu.pk, int), True )

        self.assertEqual( self.atc.name, "test_class" )
        self.assertEqual( self.atc.description , "test_description" )
        self.assertEqual( self.atc.internal_type , "class" )
        self.assertEqual( isinstance(self.atu.pk, long) or isinstance(self.atu.pk, int), True )

        self.assertEqual( self.atd.name, "test_contenttype" )
        self.assertEqual( self.atd.description , "test_description" )
        self.assertEqual( self.atd.internal_type , "contenttype" )
        self.assertEqual( isinstance(self.atu.pk, long) or isinstance(self.atu.pk, int), True )

    def test_attribute_attachment(self):
        """
        Since attributes are model independent,
        we might just use an attribute type as
        carrier, at in this test case :) 
        """

        attr(self.at, "test_int", 5)
        self.assertEqual( attr(self.at, "test_int"), 5 )
        self.assertEqual( isinstance(attr(self.at, "test_int"), int), True )

        attr(self.at, "test_int", 9)
        self.assertEqual( attr(self.at, "test_int"), 9 )
        self.assertEqual( isinstance(attr(self.at, "test_int"), int), True )

        attr.delete(self.at, "test_int")
        self.assertEqual( attr(self.at, "test_int"), None )

        attr(self.at, "test_float", 5.678)
        self.assertEqual( attr(self.at, "test_float"), 5.678 )
        self.assertEqual( isinstance(attr(self.at, "test_float"), float), True)

        attr(self.at, "test_string", "hello world")
        self.assertEqual( attr(self.at, "test_string"), "hello world" )
        self.assertEqual( isinstance(attr(self.at, "test_string"), unicode), True)

        attr(self.at, "test_text", "hello world")
        self.assertEqual( attr(self.at, "test_text"), "hello world" )
        self.assertEqual( isinstance(attr(self.at, "test_text"), unicode), True)

        attr(self.at, "test_unicode", "hello world")
        self.assertEqual( attr(self.at, "test_unicode"), "hello world" )
        self.assertEqual( isinstance(attr(self.at, "test_unicode"), unicode), True)

        attr(self.at, "test_class", [2,3,4,5,6])
        self.assertEqual( attr(self.at, "test_class"), [2,3,4,5,6] )
        self.assertEqual( isinstance(attr(self.at, "test_class"), list), True)

        attr(self.at, "test_class", ({1: 1, 2: 4, 3: 6, 4: 8, 5: 10}, 'Hello World', (1, 2, 3, 4, 5), [1, 2, 3, 4, 5]))
        self.assertEqual( attr(self.at, "test_class"), ({1: 1, 2: 4, 3: 6, 4: 8, 5: 10}, 'Hello World', (1, 2, 3, 4, 5), [1, 2, 3, 4, 5]))
        self.assertEqual( isinstance(attr(self.at, "test_class"), tuple), True)

        attr(self.at, "test_class", set([1, 2, 3, 4, 5]))
        self.assertEqual( attr(self.at, "test_class"), set([1, 2, 3, 4, 5]))
        self.assertEqual( isinstance(attr(self.at, "test_class"), set), True)

        attr(self.at, "test_class", {1: 1, 2: 4, 3: 6, 4: 8, 5: 10})
        self.assertEqual( attr(self.at, "test_class"), {1: 1, 2: 4, 3: 6, 4: 8, 5: 10})
        self.assertEqual( isinstance(attr(self.at, "test_class"), dict), True)

        attr(self.at, "test_contenttype", self.at)
        self.assertEqual( attr(self.at, "test_contenttype"), self.at )
        self.assertEqual( isinstance(attr(self.at, "test_contenttype"), Model), True)

        self.assertEqual( attr(self.at).count(), 6)
        self.assertEqual( attr.find("test_float").count(), 1)
        self.assertEqual( attr.find("test_float",1).count(), 0)
        self.assertEqual( attr.find("test_float",5.678).count(), 1)
        self.assertEqual( attr.find("test_float")[0].value, 5.678)
        self.assertEqual( attr.find("test_contenttype")[0].value, self.at)


    def test_attribute_dict_attachment(self):
        """
        Since attributes are model independent,
        we might just use an attribute type as
        carrier, at in this test case :) 
        """

        test_dict = {
            'test_int':8,
            'test_float':8.5,
            'test_string':"blah",
        }
        attr(self.at, test_dict)

        self.assertEqual( attr(self.at, "test_string"), "blah" )
        self.assertEqual( attr(self.at, "test_int"), 8 )
        self.assertEqual( attr(self.at, "test_float"), 8.5 )

    def test_nested_dict_attachment(self):
        """
        Since attributes are model independent,
        we might just use an attribute type as
        carrier, at in this test case :) 
        """

        test_dict = {
            'test_int':2,
            'test_float':10.5,
            'test_string':"sucks",
            'nested_list':[1,2,3,4,5,6,7,"hello",{'it':'is stupid', 'to':'forget tests',}],
            'nested_dict':{
                'a':{'it':'is stupid', 'to':'forget tests',},
                'b':{'wise':1, 'include': 9.5},
                'c':self.ats,
            },
        }
        attr(self.at, test_dict)

        self.assertEqual( attr(self.at, "test_string"), "sucks" )
        self.assertEqual( attr(self.at, "test_int"), 2 )
        self.assertEqual( attr(self.at, "test_float"), 10.5 )
        self.assertEqual( attr(self.at, "nested_list"), [1,2,3,4,5,6,7,"hello",{'it':'is stupid', 'to':'forget tests',}])
        self.assertEqual( attr(self.at, "nested_dict"), {
                'a':{'it':'is stupid', 'to':'forget tests',},
                'b':{'wise':1, 'include': 9.5},
                'c':self.ats,
            })

    def test_nested_dict_key_retreival(self):
        test_dict = {
            'test_int':2,
            'test_float':10.5,
            'test_string':"sucks",
            'nested_list':[1,2,3,4,5,6,7,"hello",{'it':'is stupid', 'to':'forget tests',}],
            'nested_dict':{
                'a':{'it':'is stupid', 'to':'forget tests',},
                'b':{'wise':1, 'include': 9.5},
                'c':self.ats,
            },
        }
        attr(self.at, test_dict)

        self.assertEqual( attr(self.at, ["test_int", "test_float",
                                         "nested_list",]), {
                            'test_int':2, 
                            'test_float':10.5, 
                            'nested_list': [1,2,3,4,5,6,7,"hello",{'it':'is stupid',
                                                               'to':'forget tests',}],
                         })
        self.assertEqual( attr(
            self.at, 
            'nested_dict'
        ),{
                'a':{'it':'is stupid', 'to':'forget tests',},
                'b':{'wise':1, 'include': 9.5},
                'c':self.ats,
            })

        self.assertEqual( attr(
            self.at, 
            ['nested_dict','nested_list']
        ),{
            'nested_dict' : {
                'a':{'it':'is stupid', 'to':'forget tests',},
                'b':{'wise':1, 'include': 9.5},
                'c':self.ats,
            },
            'nested_list' : [1,2,3,4,5,6,7,"hello",{'it':'is stupid', 'to':'forget tests',}],
            })

        # namespace like retreival within list
        self.assertEqual( attr(
            self.at, 
            ['nested_dict.a.it','nested_list']
        ),{
            'nested_dict.a.it' : 'is stupid',
            'nested_list' : [1,2,3,4,5,6,7,"hello",{'it':'is stupid', 'to':'forget tests',}],
            })

        # namespace like storage within list
        attr(self.at, 'nested_dict.b.wise', 2)
        self.assertEqual( attr( self.at, ['nested_dict.b.wise','nested_list']),{ 'nested_dict.b.wise' : 2, 'nested_list' : [1,2,3,4,5,6,7,"hello",{'it':'is stupid', 'to':'forget tests',}], })

    def test_persistent_dict(self):
        self.persistent_dict = PersistentDict()
        self.persistent_dict.save()
        self.persistent_dict('b','a')
        self.assertEqual(self.persistent_dict['b'], 'a')
        self.persistent_dict('blah','blub')

    def tearDown(self):
        attr.delete()
        self.assertEqual(AttributeType.objects.all().count(), 0)
        self.assertEqual(Attribute.objects.all().count(), 0)

#FIXME add more tests ;)
