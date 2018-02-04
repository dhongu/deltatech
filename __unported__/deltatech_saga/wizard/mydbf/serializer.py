"""
>>> from dbf import serializer
>>> from mydjangoapp import models

>>> s = serializer.Serializer()
>>> queryset = models.MyModel.objects.all()
>>> s.serialize(queryset)

>>> for record in s.Model.objects.all():
...     print record
"""
import datetime
import decimal
import warnings

from django.core.serializers import base
from django.utils.encoding import smart_unicode

from dbf import fields, models


class Serializer(base.Serializer):

    internal_use_only = False

    def start_serialization(self):
        self._current = None
        self.Model = None
        self.objects = []

    def end_serialization(self):
        pass

    def start_object(self, obj):
        if self.Model is None:
            fieldspecs = {}
            for field in obj._meta.fields:
                name = field.name
                size = field.max_length or 10
                type = field.get_internal_type()
                try:
                    field = getattr(fields, type)(size=size)
                    fieldspecs[name] = field
                except AttributeError:
                    warnings.warn("cannot encode %r field (%s)" % (name, type))
            name = obj.__class__.__name__
            dbname = smart_unicode(obj._meta) + '.dbf'
            self.Model = models.makeModel(name, dbname=dbname,
                    stream=self.stream, fields=fieldspecs)
        elif smart_unicode(obj._meta) != self.Model._meta.dbname[:-4]:
            raise base.SerializationError('different models')
        self._current = {}

    def end_object(self, obj):
        self._current[obj._meta.pk.attname] = obj._get_pk_val()
        print self._current
        self.Model._meta.dbf.insert(self._current)
        self._current = None

    def handle_field(self, obj, field):
        self._current[field.name] = getattr(obj, field.name)
    
    def handle_fk_field(self, obj, field):
        warnings.warn('cannot encode fk field: %s' % field.name)

    def handle_m2m_field(self, obj, field):
        warnings.warn('cannot encode m2m field: %s' % field.name)
