import base64
import math
import re
from bs4 import BeautifulSoup

from odoo import _
from odoo.exceptions import except_orm


def isFloat(v):
    try:
        float(v)
        return True
    except:
        return False


def isInt(v):
    try:
        int(v)
        return True
    except:
        return False


class pars():
    _depou = {}
    _placi = {}
    _depozit = []
    _html = object
    _header = []
    _liste = {}

    def __init__(self, data):
        self._depou = {}
        self._placi = {}
        self._depozit = []
        self._header = []
        self._html = BeautifulSoup(data, "lxml")
        self.headere()

    def headere(self):
        h = self._html.find('thead').find_all('th')
        for th in h:
            self._header.append(th.text)
        return self.grupe()

    def grupe(self):
        cap = self._html.find_all('h3')
        tabel = self._html.find_all('table')
        self._depou['cap'] = [t.text for t in cap]
        return self.parse((cap, tabel))

    def lungimeProfile(self, item):
        if ')' not in item[0].split('(')[-1]:
            return None
        mm = item[0].split('(')[-1].split(')')[0]
        flNr = int(math.floor(float(mm)))
        return flNr

    def parse(self, t):
        lista = {}
        it = 0
        for cap in t[0]:
            h = re.sub('(\s|:|"+)', '', cap.text)
            lista[h] = self.tabel(t[1][it], it)
            it += 1
        materiale = {}
        for k, v in lista.iteritems():
            if re.search(r'PLACI', k):
                materiale[k] = v
            else:
                if 'Depozit' not in materiale:
                    materiale['Depozit'] = []
                for d in v.iteritems():
                    dd = []
                    for smd in d[1]:
                        sd = list(smd)
                        if len(sd[1]) == 7:
                            sd[1] = "%s_%s" % (sd[1], self.lungimeProfile(sd)) if self.lungimeProfile(sd) else sd[1]
                        dd.append(tuple(sd))
                    materiale["Depozit"] += dd
        self._placi = materiale['PLACI']
        self._depozit = materiale['Depozit']
        self._liste = lista
        # print materiale
        # print lista

    def tabel(self, tab, index):
        liste = {}
        gr = tab.find_all(class_='BrdUpDown_1px')
        com = -1
        if self._depou['cap'][index] == 'CANTURI:':
            t = 'Canturi'
            liste[t] = []
        if len(gr) > 0 or self._depou['cap'][index] == 'CANTURI:':
            for tr in tab.find_all('tr'):
                valori = ()
                iterr = 0
                for td in tr.find_all('td'):
                    if td.has_attr('colspan') and td in gr:
                        com += 1
                        t = gr[com].find('b').text
                        liste[t] = []
                    else:
                        if iterr > 2:
                            valori += (float(td.text),)
                        else:
                            valori += (td.text,)
                        iterr += 1
                if not t:
                    t = gr[com].find('b').text
                if len(valori) > 2:
                    if float(valori[3]) > 0 and float(valori[4]) > 0 and 'proba' not in valori[0].lower():
                        if len(valori[1]) > 0:
                            liste[t].append(valori)
                        else:
                            raise except_orm(_('Product Code NULL or not set'),
                                             _('Product code is [%s] for %s\nnot set') % (valori[1], valori[0]))
        return liste


class diagrama():
    _pachete = {'STAS': []}
    _rute = {}
    _placi = []
    _echivalente = {}
    _cant = {}
    _depou = {}
    _html = object
    _cumul = []

    def __init__(self):
        self._placi = []
        self._pachete = {'STAS': []}
        self._rute = {}
        self._echivalente = {}
        self._cant = {}
        self._depou = {}
        self._cumul = []

    def init(self, data):
        self._html = BeautifulSoup(data, "lxml")
        self.process()

    def border(self, s=None, tab=None):
        if s:
            r = re.compile(r'border-right', re.IGNORECASE)
            l = re.compile(r'border-left', re.IGNORECASE)
            t = re.compile(r'border-top', re.IGNORECASE)
            b = re.compile(r'border-bottom', re.IGNORECASE)

            result = (
                l.search(s) is not None,
                r.search(s) is not None,
                t.search(s) is not None,
                b.search(s) is not None,
            )
        else:
            result = (None, None, None, None,)
        m = []
        if tab is not None:
            matrice = tab.find_all('nobr')
            m1 = []
            for t in matrice:
                v1 = (t.text).replace(u'\xa0', '')
                v2 = v1.replace(' ', '')
                # print self._depou['cant'], v2
                if v2.isdigit() and 'proba' not in self._depou['cant'][int(v2)]:
                    m1.append(self._depou['cant'][int(v2)])
                else:
                    m1.append(None)
            m = [m1[0], m1[3], m1[1], m1[2]]
        return (result, m)

    def processCumul(self, t, stil, continer):

        if 'proba' in t[4].lower():
            return False

        def taiere(data):
            t = re.split('x', data)
            return [float(i) for i in t]

        def matrita(canturi):
            m = []
            cant = canturi[1] + [None] * (4 - len(canturi[1]))
            for c in cant:
                if not c or 'proba' in c[1]:
                    m.append(None)
                else:
                    m.append(self._echivalente[c[1]])
            # print "M", m
            f = [m[3], m[2], m[0], m[1]]
            # print "F", f
            return f

        def isFib(data):
            m = re.search(r'da', data)
            return [True if m else False]

        canturi = self.border(stil, continer)
        # print "canturi", canturi
        # print self._cant, stil, "================", continer, "|||||"
        # print t
        CodMat = self._echivalente[t[4]]
        self._cumul.append([CodMat, int(t[1])] + taiere(t[8]) + isFib(t[-1]) + [t[2], ''] + matrita(canturi))

    def adaugDate(self, t, stil, continer):
        ruta = t[3]
        self.processCumul(t, stil, continer)
        if t[3] not in self._pachete:
            self._pachete[ruta] = []
        if len(t) < 11 or not re.search(r'x', t[8]):
            raise except_orm(_('Format inadecvat'), _("""Diagrama de cantuire trebuie sa aiba minim 11 coloane\n
            Dupa cum urmeaza:\n
            Coloana 9 = aria piesei, 10 = laturile cantuite.\n Recomand sa exportati diagrama din nou!\n
            Cap de tabel: [Nr. | Nr., buc | Cod | Nume | Material | Culoare | Grosime, mm | Dimensiune Gabarit, mm x mm | Dimensiune taiere, mm x mm | Cantuire | Textura]"""))
        x, y = t[8].split('x')
        ap = (t[1], t[3], t[4], x, y, self.border(stil, continer))
        self._pachete[ruta].append(ap)

    def loadcoduri(self, seturi):
        for x in seturi:
            if 'proba' in x[0].lower():
                continue
            self._echivalente[x[0]] = x[1]

    def placi(self, placi):
        for k, x in placi.iteritems():
            for p in x:
                if 'proba' in p[0].lower():
                    continue

                self._placi.append(p[0])
                self._echivalente[p[0]] = p[1]

    def tabele(self):
        t = self._html.findAll('table')
        return (t[0], t[-1])

    def gencant(self, canturi):
        # print canturi
        cant = ([0, 'nume', 'culoare', 'lat', 'gros'],)
        for c in canturi.find_all('tr'):
            s = []
            m = c.find_all('td', recursive=False)
            for t in m:
                data = t.text
                if isInt(data) and t == m[0]:
                    s.append(int(data))
                elif isFloat(data):
                    s.append(float(data))
                else:
                    s.append(t.text)
            cant += (s,)
        self._depou['cant'] = cant

    def loadcanturi(self, m, s, cod, tt, t):
        if m not in self._cant:
            self._cant[m] = {}
        if s not in self._cant[m]:
            self._cant[m][s] = {}
        if cod not in self._cant[m][s]:
            self._cant[m][s][cod] = {
                'left': [0, 0, None],
                'top': [0, 0, None],
                'right': [0, 0, None],
                'bottom': [0, 0, None]
            }
        try:
            self._cant[m][s][cod][tt][0] += 1
            self._cant[m][s][cod][tt][1] += float(t[4]) / 1000
            self._cant[m][s][cod][tt][2] = self._depou['cant'][s]
        except:
            raise except_orm(_('Probleme la procesare'), _("""In timpul procesarii diagramei am intampinat un obstacol\n
            Nu gasesc cantul cu numarul %s in diagrama, pe ruta %s, material %s\n
            Daca sigur exista si il regasiti, reincarcati.\nDaca acest cant nu exista probabil avem o diagrama incorecta/incompleta""") % (
            s, m, cod))

    def process(self):
        x = self.tabele()
        self.gencant(x[1])
        # print self._depou
        load = x[0]
        tabel = []
        for tr in load.find_all('tr'):
            v = ()
            for td in tr.find_all('td'):
                v += (td.text,)
            cant = None
            cont = None
            try:
                cant = tr.find('div')['style']
                cont = tr.find('div')
            except:
                pass
            tabel.append([v, cant, cont])

        for t in tabel:
            # print t
            if len(t[0]) > 10 and 'proba' not in t[0][4].lower():
                # print t
                self.adaugDate(t[0], t[1], t[2])
        for k, v in self._pachete.iteritems():  # loop prin toate tipurile de placi, pregatite
            if re.search(r'#', k):
                m = re.sub(r'#+(.*)$', '#', k)
            else:
                m = 'STAS'
            if m not in self._rute:
                self._rute[m] = {}
                self._cant[m] = {}

            for t in v:  # loop pe grupe in interiorul unui tip de placa.
                if t[2] not in self._placi:
                    continue
                if len(self._echivalente[t[2]]) == 7:
                    cod = "%s_%s" % (self._echivalente[t[2]], t[3])
                else:
                    cod = self._echivalente[t[2]]

                if cod not in self._rute[m]:  # adaugam tipul de pal
                    self._rute[m][cod] = [0, '', 0]  # [nr placi, cod material, suprafata totala]
                self._rute[m][cod][0] += int(t[0])
                self._rute[m][cod][1] = cod
                # self._rute[m][cod][2] += 1 if len(self._echivalente[t[2]])==7 else float(t[3])*float(t[4]) #arie material
                self._rute[m][cod][2] += 1 if '_' in cod else float(t[3]) * float(t[4])  # arie material

                # print t[-1][0], t[-1][1]
                if t[-1][0][0]:
                    self.loadcanturi(m, t[-1][1][0][0], cod, 'left', t)
                if t[-1][0][1]:
                    self.loadcanturi(m, t[-1][1][1][0], cod, 'right', t)
                if t[-1][0][2]:
                    self.loadcanturi(m, t[-1][1][2][0], cod, 'top', t)
                if t[-1][0][3]:
                    self.loadcanturi(m, t[-1][1][3][0], cod, 'bottom', t)

        for k, s in self._cant.iteritems():
            for ks, ss in s.iteritems():
                for kss, sss in ss.iteritems():
                    for ksss, ssss in sss.iteritems():
                        self._cant[k][ks][kss][ksss][1] = round(ssss[1], 2)

    def calc(self):
        canturi = self._cant
        date = {'cod': {}, 'cons': {'NR': 0.0, 'SQ': 0.0, 'RP': 0.0}, 'cant': {}}

        # ===============================================
        def parseCant(cant):
            grupa = canturi[cant]
            lista = []
            # if len(grupa) < 1:
            # return lista
            for k, v in grupa.iteritems():
                s = {'Q': 0.0, 'NR': 0.0, 'LT': 0.0}
                for kun, vun in v.iteritems():
                    laturi = 0
                    piese = []
                    for st, dat in vun.iteritems():
                        piese.append(dat[0])
                        if dat[2]:
                            s['Q'] += dat[0] * dat[1]
                            laturi += 1
                            s['cant'] = dat[2]
                    s['NR'] += max(piese)
                    s['LT'] = laturi
                s['type'] = {
                    'GROS': s['cant'][4],
                    'LAT': s['cant'][3],
                    'NAME': s['cant'][1],
                }
                lista.append(s)
            return lista

        # ==================== Parse Rutare =============
        for cod, materiale in self._rute.iteritems():
            if cod not in date['cod']:
                date['cod'][cod] = {}
            for k, s in materiale.iteritems():
                realS = s[2]  # /1000000
                date['cod'][k] = {
                    'NR': s[0],
                    'SQ': realS,
                    'RP': realS / s[0],
                }
                date['cod'][cod][k] = {
                    'NR': s[0],
                    'SQ': realS,
                    'RP': realS / s[0],
                }
                date['cons']['NR'] += s[0]
                date['cons']['SQ'] += realS
                date['cons']['RP'] += date['cons']['SQ'] / date['cons']['NR']
            date['cant'][cod] = parseCant(cod)
        return date


def extract(bon, diag):
    # base64
    bc = base64.standard_b64decode(bon)
    dg = base64.standard_b64decode(diag)
    b = pars(bc)
    d = diagrama()
    d.placi(b._placi)
    d.loadcoduri(b._depozit)
    d.init(dg)
    return {
        'placi': b._placi,
        'depozit': b._depozit,
        'route': d._rute,
        'canturi': d._cant,
        'calc': d.calc(),
        'optimik': d._cumul,
    }


def loadData():
    bc = open('./bc/BC.htm', 'r').read()
    dg = open('./bc/DC.htm', "r").read()
    b = pars(bc)
    d = diagrama()
    d.placi(b._placi)
    d.loadcoduri(b._depozit)
    d.init(dg)
    return {
        'placi': b._placi,
        'depozit': b._depozit,
        'route': d._rute,
        'canturi': d._cant,
        'calc': d.calc(),
        'optimik': d._cumul,
    }



