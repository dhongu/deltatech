"""
This is a doc test for the lowlevel API.
You should use the dbf.models module instead of this, it's simpler, more
object-oriented and tries to be similar to the django's model api.

Here's the documentation/testsuite.

First, import the needed modules:

  >>> from StringIO import StringIO
  >>> from dbf import base, fields

Then, let's define our fields.

  >>> myfields = dict(
  ...     username = fields.CharField(max_length=100),
  ...     is_admin = fields.BooleanField(),
  ...     last_login = fields.DateField(),
  ... )

Now, we can instanciate the DBF class of this module. The first argument can be
either a file name or a stream (an object that must behave like a file object).
For this example we use the StringIO module that we imported above, so we have
not to create a real file.

  >>> usersfile = StringIO() # a fake dbf file
  >>> db = base.DBF(usersfile, myfields)

When trying to select the first record in our db, we get ... a KeyError since
the db is empty.

  >>> db.select(0)
  Traceback (most recent call last):
  ...
  KeyError: 0

To solve this "big" problem, we can add a record. A record object is a simple
dict. The keys of our dict have to be the same of the fields we already defined.

  >>> user = dict(username='tyrion', is_admin=True, last_login=None)
  >>> db.insert(user)

The pk key has been added to our record, this is a virtual field, and it is not
written to the database.

  >>> user['pk']
  0

Now let's try to select our first record again:

  >>> tyrion = db.select(0)
  >>> tyrion['username'] == user['username']
  True
  >>> tyrion['is_admin']
  True

Hooray, it worked and returned a dict that is equal to our "user" one.

  >>> tyrion == user
  True

We left our "last_login" field empty, we got no errors because we not specified
"null=False" in our fieldspecs dict. Let's fill this field with a random data.

  >>> import datetime
  >>> tyrion['last_login'] = datetime.date(2008, 1, 30) # a random date
  >>> db.update(tyrion)

Now we select only the "last_login" field of the first record.

  >>> db.select(0, ['last_login'])
  {'pk': 0, 'last_login': datetime.date(2008, 1, 30)}

Then, just to not leave our first user alone, we create a new one.

  >>> newuser = dict(username='dummy', is_admin=False, last_login=None)
  >>> db.insert(newuser)

Our DBF instance supports the "in" keyword and the len builtin function.
  >>> newuser['pk'] in db
  True
  >>> len(db)
  2

As well as iteration over the records:

  >>> for record in db:
  ...     print record['username']
  tyrion
  dummy

We can also iterate only over the required fields:

  >>> for record in db.select(fields=['username']):
  ...     print record['username']
  tyrion
  dummy
"""

import os
import datetime
import struct

#from dbf import fields
#from dbf.sorteddict import SortedDict
import fields
from sorteddict import SortedDict

class DBF(object):

    version = 3
    header_fmt = '<BBBBLHH20x'
    fields_fmt = '<11sc4xBB14x'
    
    def __init__(self, db, fieldspecs=None):
        if isinstance(db, basestring):
            db = open(db, 'w+b')
        self.db = db
        self.fields = fieldspecs

        # try to read the header infos from the db
        header = db.read(32)
        if header:
            header = struct.unpack(self.header_fmt, header)

        # if the user passed fieldspecs
        if self.fields:
            # obtain dbf meta data from them
            self.numfields = len(self.fields)
            self.lenheader = self.numfields * 32 + 33
            
            self.lenrecord = 1
            self.record_fmt = '1s'
            for field in self.fields.itervalues():
                self.lenrecord += field.size
                self.record_fmt += '%ds' % field.size

            # if we have an header
            if header:
                # check the header's infos with the ones we have obtained from
                # our fieldspecs
                self.numrec, lenheader, lenrecord = header[-3:]
                assert (lenheader == self.lenheader and
                        lenrecord == self.lenrecord), \
                        "database's fields doesn't match provided fields"
            # if no header is present, write it
            else:
                self.numrec = 0

                # header
                now = datetime.datetime.now()
                y, m, d = now.year-1900, now.month, now.day
                header = struct.pack(self.header_fmt, self.version, y, m, d,
                                     self.numrec, self.lenheader, self.lenrecord)
                self.db.write(header)

                # field specs
                for fname, field in self.fields.iteritems():
                    fname = fname.ljust(11, '\0')
                    field = struct.pack(self.fields_fmt, fname, field.type,
                                        field.size, field.deci)
                    self.db.write(field)
                self.db.write('\r\x1A')
        else:
            # if we have no fieldspecs, but we have an header in our dbf,
            # obtain the fieldspecs from it.
            if header:
                self.numrec, self.lenheader, self.lenrecord = header[-3:]
                self.numfields = (self.lenheader - 33) // 32
                self.fields = SortedDict()
                self.record_fmt = '1s'
                for fieldno in xrange(self.numfields):
                    fieldinfo = struct.unpack(self.fields_fmt, db.read(32))
                    name, type, size, deci = fieldinfo
                    name = name.partition('\0')[0]
                    if type in ['C','L','N','D']:
                        self.fields[name] = fields.guessField(type, size, deci)
                        self.record_fmt += '%ds' % size

            else:
                # if we have no header and no fieldspecs, we can't help it ...
                raise TypeError("nor fields or header present")

        i = 0
        self._fieldpos = []
        for field in self.fields.itervalues():
            self._fieldpos.append(i)
            i += field.size

    def gotoField(self, fname):
        i = self.fields.keyOrder.index(fname)
        self.db.seek(self._currec + 1 + self._fieldpos[i])

    def newID(self):
        """
        return a new record ID.
        """
        self.db.seek(4)
        self.numrec = struct.unpack('<L', self.db.read(4))[0]
        return self.numrec

    def increase_numrec(self):
        self.numrec += 1
        self.db.seek(4)
        self.db.write(struct.pack('<L', self.numrec))

    def gotoRecord(self, recIndex):
        """
        move before the record specified by the index recIndex
        """
        if recIndex > self.numrec:
            raise KeyError(recIndex)
        self._currec = self.lenheader + self.lenrecord * (recIndex)
        self.db.seek(self._currec)

    def update(self, record):
        recId = record['pk']
        self.gotoRecord(recId)

        dflag = self.db.read(1)

        for fname, field in self.fields.iteritems():
            if fname in record:
                self.db.write(field.encode(record[fname]))
                self.db.flush()
            else:
                self.db.seek(field.size, 1)
        self.db.flush()

    def insert(self, record):
        recId = self.newID()
        self.gotoRecord(recId)
        record['pk'] = recId

        self.db.write(' ')
        data = ''
        for fname, field in self.fields.iteritems():
            data += field.encode(record[fname])
        self.db.write(data)
        
        self.db.write('\x1A')
        self.increase_numrec()

        self.db.flush()

    def _iterselect(self, fields=None):
        for recId in xrange(self.numrec):
            yield self.select(recId, fields)
 
    def select(self, recId=None, fields=None):
        if recId is None:
            return self._iterselect(fields)

        if not recId in self:
            raise KeyError(recId)
        
        if not fields:
            fields = self.fields.keys()

        self.gotoRecord(recId)
        res = {'pk': recId}

        self.db.read(1)
        for fname, field in self.fields.iteritems():
            if fname in fields:
                res[fname] = field.decode(self.db.read(field.size))
            else:
                self.db.seek(field.size, 1)
        return res

    def close(self):
        self.db.close()

    def __contains__(self, recId):
        if isinstance(recId, int) and recId < self.numrec:
            return True
        return False

    def __iter__(self):
        for i in xrange(self.numrec):
            yield self.select(i)

    def __len__(self):
        return self.numrec

    def __getitem__(self, recordID):
        return self.select(recordID)

    def __setitem__(self, recordID, dict):
        self.select(recordID, dict)

def _test():
    import doctest
    doctest.testmod()

if __name__ == '__main__':
    _test()
