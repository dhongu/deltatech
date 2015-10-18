"""
High Level interface to DBF files.


>>> import os
>>> import datetime
>>> from dbf import models, fields

>>> class Person(models.Model):
...
...    class Meta:
...        #dbname = 'persons.dbf'
...        lazy = True
...
...    first_name = fields.CharField(max_length=100, null=False)
...    last_name = fields.CharField(max_length=100, null=True)
...    email = fields.CharField(max_length=100, null=True)
...    birth_date = fields.DateField()
...    loves_python = fields.BooleanField()
...    height = fields.DecimalField(max_length=5, deci=2)
...
...    def __unicode__(self):
...        return self.first_name

>>> Person.objects.get(pk=0)
Traceback (most recent call last):
...
IndexError: list index out of range

>>> person = Person(first_name='Tyrion', last_name='MX', email='ty@nsa.gov')
>>> person.birth_date = datetime.date(1980, 1, 3) # random date
>>> person.save()

>>> tyrion = Person.objects.get(pk=0)
>>> tyrion
<Person: Tyrion>

>>> assert tyrion.first_name == person.first_name
>>> assert tyrion.birth_date == person.birth_date

>>> tyrion.loves_python = True
>>> tyrion.save()

Force the database to close and delete it.
>>> Person._meta.dbf.close()
>>> if os.path.exists('Person.dbf'):
...     os.remove('Person.dbf')
"""
import types
import copy

#from dbf.base import DBF
#from dbf.sorteddict import SortedDict
#from dbf import fields

from base import DBF
from sorteddict import SortedDict
import fields


class QuerySet(object):

    defaultParams = dict(
            #options=None,
            slice=None,
            get_only=None,
            one_result=False
    )


    def __init__(self, Model, params={}):
        self.Model = Model
        self.dbf = Model._meta.dbf

        include = params.pop('include', {})
        exclude = params.pop('exclude', {})

        self.params = self.defaultParams.copy()
        self.params['options'] = dict()
        self.params.update(params)

    def _match(self, fname, fdata, **params):
        if fname == 'pk':
            field = fields.IntegerField
        else:
            field = self.dbf.fields[fname]
        for type in ('include', 'exclude'):
            for (method, value) in params[type]:
                res = field.lookupMethods[method](fdata, value)
                if (type == 'include' and not res) or \
                   (type == 'exclude' and res):
                    return False
        return True       

    def __iter__(self):
        options = self.params['options']
        slice = self.params['slice']
        getonly = self.params['get_only']
        i = -1
        for record in self.dbf.select(fields=options.keys()):
            match = True
            for fname, params in options.iteritems():
                match = self._match(fname, record[fname], include=params[0],
                                    exclude=params[1])
                if not match:
                    break
            if match:
                i += 1
                if slice and (slice[0] > i or \
                   (slice[1] is not None and slice[1] < i)):
                    continue
                if getonly in (i, None):
                    m = self.Model(record['pk'])
                    vars(m).update(record)
                    yield m
                    if getonly == i:
                        return

    def prepareOptions(self, options, **params):
        for i, option in enumerate(('include', 'exclude')):
            for fname, value in params[option].iteritems():
                try:
                    fname, method = fname.split('__')
                except ValueError:
                    method = 'exact'
                try:
                    if fname == 'pk':
                        field = fields.IntegerField
                    else:
                        field = self.dbf.fields[fname]
                    if not method in field.lookupMethods:
                        raise TypeError('inexistent %s method: %s' %
                                (field.__class__.__name__, method))
                except KeyError:
                    raise TypeError('inexistent field: %s' % fname)
                field = options.setdefault(fname, (list(),list()))
                field[i].append((method, value))

    def new(self, include={}, exclude={}, **extend):
        params = copy.deepcopy(self.params)
        params.update(extend)
        self.prepareOptions(params['options'], include=include,
                            exclude=exclude)
        return QuerySet(self.Model, params)

    def filter(self, **params):
        return self.new(include=params)

    def exclude(self, **params):
        return self.new(exclude=params)

    def all(self):
        return self.new()

    def get(self, **params):
        res = list(self.new(include=params))
        if len(res) > 1:
            raise Exception('get() returned more than one result: %d' % \
                            len(res))
        return res[0]

    
    def __getitem__(self, key):
        if isinstance(key, int):
            self.params['get_only'] = key
            return list(self)[0]
        elif isinstance(key, slice):
            return self.new(slice=(key.start or 0, key.stop))
        else:
            raise KeyError(key)

    def __repr__(self):
        return repr(list(self))

class Manager(QuerySet):

    __repr__ = object.__repr__
    __iter__ = __getitem__ = None


def makeModel(name, **meta):
    meta = type('Meta', (object,), meta)
    return ModelMeta(name, (Model,), {'Meta': meta})


class ModelMeta(type):

    def __new__(cls, name, bases, dict):
        if bases != (object,):

            dict.pop('pk', None)
            meta = dict.pop('Meta', None)

            if not meta:
                meta = type('Meta', (object,), {})

            def setdefault(attr, default):
                if not hasattr(meta, attr):
                    setattr(meta, attr, default)

            setdefault('lazy', True)
            setdefault('dbname', name + '.dbf')
            
            if not hasattr(meta, 'fields'):
                meta.fields = SortedDict()
                for key, value in dict.iteritems():
                    if isinstance(value, fields.Field):
                        meta.fields[key] = dict[key]
                [dict.pop(field) for field in meta.fields]

            if hasattr(meta, 'stream'):
                meta.dbf = DBF(meta.stream, meta.fields)
            else:
                meta.dbf = DBF(meta.dbname, meta.fields)
            
            if dict.get('__unicode__'):
                repr = (lambda self: u'<%s: %s>' % (name, self.__unicode__()))
                dict['__repr__'] = repr

            Model = type.__new__(cls, name, bases, dict)
            Model._meta = meta
            Model.objects = Manager(Model)
            return Model

        else:
            return type.__new__(cls, name, bases, dict)


class Model(object):

    __metaclass__ = ModelMeta

    def __init__(self, pk=None, **kwargs):
        self.pk = pk
        if pk is None:
            for fname in self._meta.fields:
                setattr(self, fname, kwargs.pop(fname, None))

    def __hasattr__(self, attr):
        return attr in self._meta.fields

    def __getattr__(self, attr):
        if attr in self._meta.fields:
            if self.pk is not None:
                value = self._meta.dbf.select(self.pk, [attr])[attr]
                setattr(self, attr, value)
                return value
        else:
            raise AttributeError(attr)

    def getall(self):
        vars(self).update(self._meta.dbf.select(self.pk))

    def save(self):
        if self.pk != None:
            self._meta.dbf.update(vars(self))
        else:
            self._meta.dbf.insert(vars(self))

def _test():
    import doctest
    doctest.testmod()

if __name__ == '__main__':
    _test()
