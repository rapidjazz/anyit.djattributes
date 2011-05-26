from django.db.models.base import ModelBase, Model
from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from fields import PickledObjectField

class AttributeNameError(NameError):
    pass

class AttributeTypeError(TypeError):
    pass

class AttributeManager(models.Manager):
    """
    Manager class for the 'background work'
    """
    def attribute(self, o, n, v=None, create_attributetype=True,
                  create_attribute=True, klass=False, description=None,
                  as_attribute=False, tolerant=True):
        """
        set or get an (o)bject's attribut (with the name n) to value(v)

        o is the object to be "attributed"
        n the attributetype's name
        v the value which is used with the setter, if none the getter will be used
        
        create_attributetype, set to True, will create an attributetype of a given name, if it does not exist
        create_attribut, set to True, will create an attribute and attach it to the given object, if it does not exist
        klass will attach the given attribute to the model class, even if o is an instance
        description may contain a description for the attribute type eventually being created.
        """
        ct = ContentType.objects.get_for_model(o)
        # This is a classattribute
        if klass or isinstance(o, ModelBase): 
            oid = 0
        # This is an instanceattribute
        else:
            oid = o.id
        # Check if type exists
        namespaces = n.split('.')
        try:
            # allow namespaces for retreival of single subkeys
            at = AttributeType.objects.get(name=namespaces[0])

        # Try to create it, if not and set
        except:
            if not create_attributetype:
                raise AttributeTypeError("There is no attribute type %s"%n)
            else:
                # Determine Type
                if isinstance(v, int):
                    internal_type='int'
                elif isinstance(v, float):
                    internal_type='float'
                elif isinstance(v, str):
                    internal_type='text'
                elif isinstance(v, unicode): 
                    internal_type='text'
                elif isinstance(v, Model): 
                    internal_type='contenttype'
                else: 
                    # Hope it's 'pickable'
                    internal_type='class'
                if not description:
                    description = n
                at = AttributeType.objects.create(name=n, description=description, 
                                                  internal_type=internal_type)
        last = len(namespaces) - 1
        # getter
        if not v:
            try:
                a = self.get(content_type=ct, object_id=oid, attribute_type=at)
            except:
                # Try to fall back to static attribute if object has none
                try:
                    a = self.get(content_type=ct, object_id=0, attribute_type=at)
                except:
                    if not tolerant:
                        raise AttributeNameError("Neither Object %s nor it's Class has an attribute %s"%(o,n))
                    return None
            if as_attribute:
                return a
            val = a.value
            if last:
                for killmer in namespaces[1:]:
                    val = val[killmer]
            return val
        # setter
        else:
            try:
                a = self.get(content_type=ct, object_id=oid, attribute_type=at)
            except:
                if not create_attribute:
                    raise AttributeNameError("Object %s has no attribute %s"%(o,n))
                else:
                    a = self.create(content_type=ct, object_id=oid, attribute_type=at)
            if last:
                val = a.value
                if not val:
                    val = {}
                result = val
                for killmer in namespaces[1:-1]:
                    if val.get(killmer, None) is None:
                        val[killmer] = {}
                    val = val[killmer]
                val[namespaces[-1]] = v
                a.value = result
            else:
                val = a.value = v
            if as_attribute:
                return a
            else:
                return val

    def collection(self, o, recursive=False, class_only=False):
        """
        Creates a collection of attributes related to object or model o

        Since attributes may have attributes a recursive option is given.
        class_only will return the static like model attributes only
        """
        ct = ContentType.objects.get_for_model(o)
        if isinstance(o, ModelBase):
            qs = self.filter(content_type=ct)
            if class_only:
                qs.filter(object_id=0)
        else:
            qs = self.filter(content_type=ct, object_id=o.id)
        if recursive:
            for a in qs:
                if a not in qs:
                    qs = qs | self.collection(a, recursive=True, class_only=class_only)
        return qs

ATTRIBUTE_TYPES = (
    ('int','int'),
    ('float','float'),
    ('unicode','str'),
    ('string','str'),
    ('text','str'),
    ('class','class'),
    ('contenttype','contenttype'),
)
class AttributeType(models.Model):
    """
    A class for AttributeTypes containing fields for 
    name, discription and typevar, mapping the processing
    """
    name = models.CharField(max_length=255, db_index=True, unique=True, choices=ATTRIBUTE_TYPES)
    description = models.CharField(max_length=255)
    internal_type = models.CharField(max_length=45, db_index=True)
    class Meta:
        ordering = ['name', 'internal_type',]
    def __unicode__(self):
        return u','.join([self.name, self.description, self.internal_type])
    def collection(self, value=None):
        """
        An attribute collection for this type,
        limited to those set to value if given
        """
        qs = self.attribute_set.all()
        if not value:
            return qs
        else:
            ids = [a.id for a in qs if a.value==value]
            return qs.filter(id__in=ids)

class Attribute(models.Model):
    """
    A class with a generic key to an owninng object, a link to a type class and implicit links to
    specific values distributed to those classes mapped in ATTRIBUTE_TYPES to the helper classes
    defined below.
    """
    content_type = models.ForeignKey(ContentType,db_index=True)
    object_id = models.IntegerField(db_index=True)
    owner = generic.GenericForeignKey('content_type', 'object_id')
    attribute_type = models.ForeignKey(AttributeType, db_index=True)

    objects = AttributeManager()

    class Meta:
        unique_together = (("content_type", "object_id", "attribute_type",),)
        ordering = ["content_type", "object_id", "attribute_type",]

    def __unicode__(self):
        try:
            val =  u"%s"%self.value
        except:
            val = u"not printable"
        return u','.join([self.name, self.description, self.attributetype, val])

    def get_owner(self):
        try:
            ct = ContentType.objects.get(pk=self.content_type)
            return ct.get_object_for_this_type(pk=self.object_id)
        except:
            return None

    @property
    def name(self):
        return self.attribute_type.name

    @property 
    def description(self):
        return self.attribute_type.description

    @property
    def attributetype(self):
        return self.attribute_type.internal_type

    @property
    def parent(self):
        try:
            o = self.get_owner()
            if isinstance(o, Attribute):
                return o
        except:
            pass
        return None

    @property
    def children(self):
        ct = ContentType.objects.get_for_model(self)
        return Attribute.objects.filter(content_type=ct.pk, object_id=self.pk) 

    def get_value(self):
        """type dispatcher"""
        try:
            at = self.attributetype
            if at == "int":
                return self.intvalue_set.all()[0].value
            elif at == "float":
                return self.floatvalue_set.all()[0].value
            elif at in ["string", "text", "unicode"]:
                return self.textvalue_set.all()[0].value
            elif at == "class": 
                return self.classvalue_set.all()[0].value
            elif at == "contenttype":
                return self.contenttypevalue_set.all()[0].value
        except:
            pass
        return None

    def set_value(self, v):
        """storage dispatcher"""
        at = self.attributetype
        if at == "int":
            self.intvalue_set.all().delete()
            self.intvalue_set.add(IntValue.objects.create(parent=self, value=v))
        elif at == "float":
            self.floatvalue_set.all().delete()
            self.floatvalue_set.add(FloatValue.objects.create(parent=self, value=v))
        elif at in ["string", "text", "unicode"]:
            self.textvalue_set.all().delete()
            self.textvalue_set.add(TextValue.objects.create(parent=self, value=v))
        elif at == "class":
            self.classvalue_set.all().delete()
            self.classvalue_set.add(ClassValue.objects.create(parent=self, value=v))
        elif at == "contenttype":
            self.contenttypevalue_set.filter(parent=self).delete()
            self.contenttypevalue_set.add(ContentTypeValue.objects.create(parent=self, value=v))

    def delete_value(self):
        at = self.attributetype
        if at == "int":
            self.intvalue_set.all().delete()
        if at == "float":
            self.floatvalue_set.all().delete()
        if at in ["string", "text", "unicode"]:
            self.textvalue_set.all().delete()
        if at == "class":
            self.classvalue_set.all().delete()
        if at == "contenttype":
            self.contenttypevalue_set.filter(parent=self).delete()

    value = property(fget=get_value, fset=set_value, fdel=delete_value)

    def delete(self):
        ct = ContentType.objects.get_for_model(self)
        for a in Attribute.objects.filter(content_type=ct, object_id=self.pk):
            a.delete()
        self.delete_value()
        super(Attribute, self).delete()

"""
Internal Representation Models
"""

class IntValue(models.Model):
    parent = models.ForeignKey(Attribute)
    value = models.IntegerField()

class FloatValue(models.Model):
    parent = models.ForeignKey(Attribute)
    value = models.FloatField()

class TextValue(models.Model):
    parent = models.ForeignKey(Attribute)
    value = models.TextField()

# taken from http://djangosnippets.org/snippets/1694/
class ClassValue(models.Model):
    parent = models.ForeignKey(Attribute)
    value = PickledObjectField()

class ContentTypeValue(models.Model):
    parent = models.ForeignKey(Attribute)
    content_type = models.ForeignKey(ContentType,db_index=True)
    object_id = models.PositiveIntegerField(db_index=True)
    content_object = generic.GenericForeignKey('content_type', 'object_id')

    def get_value(self):
        return self.content_object

    def set_value(self, o):
        self.content_object = o

    value = property(fget=get_value, fset=set_value)

class ConvenientAttributeManager(object):
    """
    This class provides a JavaScript like interface to the
    attribute classes, mapping JQuery logic to the above
    class and manager functions
    """
    def __call__(self, o=None, n=None, v=None, create_attributetype=True, 
                 create_attribute=True, klass=False, description=None, 
                 as_attribute=False, as_dict=True):
        """
        Forwarder to Attribute.attribute as a short notation 
        
        returning 
        - a collection of all Attribute objects if no parameter is given
        - a collection of those attached to (o)wner if given exclusively 
        - an attribute's value if (o)wner and (n)ame are given
        - a dictionary of values if multiple (o)wners and (n)ames are given
        - or the one being attached to a class if klass or o of Model type
        - the containing Attribute object respectively if as_attribute

        or setting the corresponding attributes value. You can "batch" the attr
        command by passing lists as o,n,v and dicts as n and v.

        You can address dict's or list keys in a namespace like manner:
            attr(o, name.subkey.subsubkey, v) ...
        """
        ############################################
        # Permutation of o types
        # 
        # no object given so lets go for a queryset
        if not o: 
            qs = Attribute.objects.all()
            if n:
                qs = qs.filter(attribute_type__name=n)
            if v:
                keys = []
                for a in qs:
                    if a.value == v:
                        keys.append(a.pk)
                qs = qs.filter(pk__in=keys)
            return qs

        # multiple objects given so lets just iterate
        elif isinstance(o, list) or isinstance(o, set) or isinstance(o, tuple):
            for x in set(o):
                result = []
                result.append(self.__call__(x, n, v, create_attributetype, create_attribute,
                              klass, description, as_attribute))
                if v or isinstance(n, dict):
                    return
                else:
                    return result

        # check object for type
        elif not isinstance(o, Model) and not isinstance(o, ModelBase):
            raise AttributeTypeError("Object instance has to be an instance of Model or ModelBase!")

        ############################################
        # Permutation of n types
        # 
        # no key
        if not n:
            return Attribute.objects.collection(o, recursive=False)
        
        # multiple keys => "getters"
        elif isinstance(n, list) or isinstance(n, set) or isinstance(n, tuple):
            result = {}
            if v is not None:
                raise AttributeNameError("List of keys indicate the use of getters while a given value indicates using a setter!")
            for key in set(n):
                result[key] = self.__call__(o, key, None, create_attributetype, create_attribute,
                              klass, description, as_attribute)
            return result

        # multiple keys, value pairs => "setters"
        elif isinstance(n, dict):
            result = {}
            for key, value in n.iteritems():
                result[key] = self.__call__(o, key, value, create_attributetype, create_attribute, klass, description, as_attribute)
            return result

        ############################################
        # Permutation of v types
        # 
        return Attribute.objects.attribute(o, n, v, create_attributetype, create_attribute, klass, description, as_attribute)


    def create_type(self, n, d, it):
        """
        get or create an attribute type with the given
        (n)ame, (d)escription and (i)nternal (t)ype
        """
        try:
            a = AttributeType.objects.get(name=n)
            if d!=a.description or it!=a.internal_type:
                raise AttributeNameError("Attribute types cannot be changed via this manager and either %s != %s or %s != %s"%(d, a.description, it, a.internal_type))
        except:
            a = AttributeType.objects.create(name=n, description=d, internal_type=it)
        return a

    def delete_type(self, n):
        """
        delete the type of the given (n)ame
        """
        a = AttributeType.objects.get(name=n)
        a.attribute_set.all().delete()
        a.delete()

    def delete(self, o=None, n=None):
        """
        delete everything with no parameter given
        delete the every attribute of the given (n)ame, o=None
        delete the every attribute attached to (o)bject, n=None
        delete the attribute n attached to (o)bject
        """
        if not o:
            if not n: 
                return AttributeType.objects.all().delete()
            else:
                return Attribute.objects.filter(attribute_type__name=n).delete()
        elif isinstance(o, list) or isinstance(o, set) or isinstance(o, tuple):
            for x in o:
                self.delete(x, n)
        else:
            ct = ContentType.objects.get_for_model(o)
            if not n:
                qs = Attribute.objects.filter(content_type=ct, object_id=o.id)
                for a in qs:
                    a.delete()
            # multiple keys => "getters"
            elif isinstance(n, list) or isinstance(n, set) or isinstance(n, tuple):
                for value in n:
                    self.delete(o, value)
            else:
                Attribute.objects.get(content_type=ct, object_id=o.id,
                                          attribute_type__name=n).delete()
                return

    def find(self, a, value=None, recursive=False):
        """
        find (a list of) owner(s) of an attribute(type)
        """
        if isinstance(a, Attribute):
            return a.owner
        if isinstance(a, str) or isinstance(a, unicode):
            try:
                a = AttributeType.objects.get(name=unicode(a))
                return a.collection(value)
            except:
                return None
        return None

attr = ConvenientAttributeManager()

class PersistentDict(models.Model):
    '''a simple persistent dict'''

    def __init__(self, d=None):
        super(PersistentDict, self).__init__()
        self.save()
        if d:
            self.__call__(d)

    def __call__(self, k=None, v=None):
        return attr(self, k, v, create_attributetype=True,
                    create_attribute=True, klass=True, description=k,
                    as_attribute=False)

    def __getitem__(self, key):
        return self.__call__(key)

    def __setitem__(self, key, val):
        return self.__call__(key, val)


