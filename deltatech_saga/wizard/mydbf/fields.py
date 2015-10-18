import datetime
import decimal

class DBFError(Exception):
    pass


class Field(object):

    type = None
    
    lookupMethods = {
        'exact': lambda f,v: f == v,
        'in': lambda f,v: f in v,
    }
    cmpMethods = dict(
        gt  = lambda f,v: f > v,
        gte = lambda f,v: f >= v,
        lt  = lambda f,v: f < v,
        lte = lambda f,v: f <= v,
    )
    otherMethods = dict(
        range = lambda f,v: f >= v[0] and f <= v[1],
    )

    def __init__(self, **kwargs):
        for k,d in (('size',None),('deci',0),('null',True),('default',None)):
            setattr(self, k, kwargs.pop(k, d))
        if self.size is None:
            try:
                self.size = kwargs.pop('max_length')
            except KeyError:
                raise TypeError('nor size or max_length supplied')

    def decode(self, value):
        value = value.replace('\0', '').strip()
        if value == '':
            if self.null:
                return None
            else:
                return self.default
        value = self.decodeField(value)
        return value

    def encode(self, value):
        if value is None:
            if not self.null:
                raise DBFError('field can not be NULL')
            else:
                return ' ' * self.size
        return self.encodeField(value)

    def as_tuple(self):
        return (self.type, self.size, self.deci)

    def __repr__(self):
        return '%s(size=%d, deci=%d)' % (self.__class__.__name__, self.size,
                                         self.deci)


class CharField(Field):

    type = 'C'

    lookupMethods = dict(
        startswith = str.startswith,
        endswith = str.endswith,
        contains = lambda f,v: v in f,
        regexp = lambda f,v: re.match(v, f),
        search = lambda f,v: re.search(v, f),
    )
    lookupMethods.update(Field.lookupMethods)
    lookupMethods.update(Field.cmpMethods)
        
    
    def __init__(self, **kwargs):
        kwargs['deci'] = 0
        Field.__init__(self, **kwargs)

    def decodeField(self, value):
        return str(value)

    def encodeField(self, value):
        return str(value)[:self.size].ljust(self.size, ' ')

class BooleanField(Field):
    
    type = 'L'

    def __init__(self, **kwargs):
        kwargs['size'] = 1
        kwargs['deci'] = 0
        Field.__init__(self, **kwargs)
    
    def decodeField(self, value):
        return (value in 'YyTt' and True) or \
               (value in 'NnFf' and False) or None

    def encodeField(self, value):
        return str(value)[0].upper()

class IntegerField(Field):

    type = 'N'

    lookupMethods = dict(
        range=Field.otherMethods['range']
    )
    lookupMethods.update(Field.lookupMethods)
    lookupMethods.update(Field.cmpMethods)

    def __init__(self, **kwargs):
        kwargs['deci'] = 0
        Field.__init__(self, **kwargs)

    def decodeField(self, value):
        return int(value)

    def encodeField(self, value):
        return str(value).rjust(self.size, ' ')

class DecimalField(IntegerField):
    
    def decodeField(self, value):
        return decimal.Decimal(value)

class DateField(Field):

    type = 'D'

    lookupMethods = dict(
        year = lambda f,v: f.year == v,
        month = lambda f,v: f.month == v,
        day = lambda f,v: f.day == v,
        range = Field.otherMethods['range'],
    ).update(IntegerField.lookupMethods)

    def __init__(self, **kwargs):
        kwargs['size'] = 8
        kwargs['deci'] = 0
        Field.__init__(self, **kwargs)

    def decodeField(self, value):
        y, m, d = map(int, (value[:4], value[4:6], value[6:8]))
        return datetime.date(y, m, d)

    def encodeField(self, value):
        return value.strftime('%Y%m%d')

AutoField = IntegerField
DateTimeField = DateField
EmailField = CharField

type_to_fields = {
        ('C', False): CharField,
        ('L', False): BooleanField,
        ('N', False): IntegerField,
        ('N', True): DecimalField,
        ('D', False): DateField,
}

def guessField(type, size, deci=0):
    return type_to_fields[type, bool(deci)](size=size, deci=deci)
