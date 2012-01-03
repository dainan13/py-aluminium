# -*- coding: utf-8 -*-


import easyprotocol as ezp
import cStringIO
import struct
import types
import os.path
import cPickle as pickle

import pprint


class TTFError(Exception):
    pass


def checksum( inp, le=None ):
    
    if le != None :
        inp = inp.read( length )
    
    if type(inp) == types.ListType :
        r = 0
        i = 0
        for lc, in inp :
            for c in lc :
                r = ( c << ((3-(i%4))*8) ) & 0xFFFFFFFF
                i += 1
        return r
    
    r = 0
    for i, c in enumerate(inp) :
        i = 3 - (i % 4)
        r += c << (i*8)
        r = r & 0xFFFFFFFF
    
    return r

def sum_checksum( checksums ):
    return sum( checksums ) & 0xFFFFFFFF

def int16b( ch ):
    return chr(ch/256) + chr(ch%256)


def make_ser( inp, nbyte ):
    
    if inp < 1 :
        raise TTFError, 'make ser error.'
    
    searchrange = 1
    entryselector = 0
    
    while( searchrange*2 < inp ):
        searchrange = searchrange*2
        entryselector += 1
        
    return nbyte*searchrange, entryselector, nbyte*(inp-searchrange)
    

class FLAGSType( ezp.ProtocolType ):
    
    def __init__( self ):
        
        self.name = 'flags'
        self.cname = 'flags'
        
        self.identifiable = True
        self.stretch = True
        
        self.variables = []
        
    def length( self, lens, array ):
        return None
    
    def read( self, namespace, fp, lens, args ):
        
        numberOfPoints = args
        repeat = 1 << 3
        zerocheck = ( 1 << 6 ) | ( 1 << 7 )
        
        r = []
        le = 0
        while( numberOfPoints > 0 ):
            
            flag = ord(fp.read(1))
            if flag & zerocheck :
                raise Exception, ('zero check error', hex(flag))
            
            c = ord(fp.read(1))+1 if (flag & repeat) else 1
            if c == 0 :
                raise Exception, ('repeat 0', hex(flag))
            le += ( 2 if (flag&repeat) else 1 )
            r.extend([flag]*min(c,numberOfPoints))
            numberOfPoints -= c
        
        return r, le
        
    def read_multi( self, namespace, fp, lens, mlens, args ):
        
        raise TTFError, 'flags can\'t read 1+.'
        

class COORDSType( ezp.ProtocolType ):
    
    def __init__( self ):
        
        self.name = 'coords'
        self.cname = 'coords'
        
        self.identifiable = True
        self.stretch = True
        
        self.variables = []
        
    def length( self, lens, array ):
        return None
    
    def readbyte( self, fp ):
        return ord(fp.read(1))
    
    def readshort( self, fp ):
        return ( ord(fp.read(1)) << 8 ) + ord(fp.read(1))
    
    def read( self, namespace, fp, lens, args ):
        
        flags, isX = args
        
        if isX :
            short = 1 << 1
            positive = 1 << 4
            same = 1 << 4
        else :
            short = 1 << 2
            positive = 1 << 5
            same = 1 << 5
            
        last = 0
        r = []
        le = 0
        
        for flag in flags :
            if flag & short :
                last = ( last + self.readbyte(fp) ) if flag & positive else ( last - self.readbyte(fp) )
                r.append( last )
                le += 1
            else :
                last = last if flag & same else ( last + self.readshort(fp) )
                r.append( last )
                le += 2
        
        return r, le
        
    def read_multi( self, namespace, fp, lens, mlens, args ):
        
        raise TTFError, 'coords can\'t read 1+.'
        

def load_unicode_block( fname ):
    
    with open( fname, 'r' ) as fp :
        lns = fp.read().splitlines()
    
    lns = [ l.strip() for l in lns ]
    lns = [ l for l in lns if l != '' and not l.startswith('#') ]
    lns = [ l.split(';') for l in lns ]
    
    lns = [ ( seg.split('..'), name.strip() ) for seg, name in lns ]
    if not all( st.endswith('0') and ed.endswith('F') for (st,ed), name in lns ) :
        raise TTFError, 'unicode block error'
    lns = [ (int(st),int(ed),name) for (st, ed), name in lns ]
    lns = [ (st,ed,name) for st, ed, name in lns if st < 0xFFFF ]
    
    xlns = [ (b[1]+1,a[0]-1,'nodefined '+hex(b[1]+1)+'..'+hex(a[0]-1)) 
             for b, a in zip(lns,lns[1:]) if b[1]+1 != a[0] ]
    
    lns = lns + xlns
    lns.sort( key = lambda n:n[0] )
    lns = [ name for st, ed, name in lns for s in range(st>>8,(ed>>8)+1) ]
    
    return lns

class TTFile(object):
    
    ebp = ezp.EasyBinaryProtocol()
    ebp.buildintypes.append(FLAGSType())
    ebp.buildintypes.append(COORDSType())
    ebp.rebuild_namespaces()
    ebp.parsefile( 'ttf.protocol' )
    
    unicode_block = load_unicode_block( os.path.realpath(__file__)+'Blocks-6.1.0d1.txt' )
    
    def __init__( self ):
        
        self.name = None
        self.nametuple = None
        self.fix_entrys = {}
        self.stt_entrys = {}
        self.char_defines = {}
        self.char_kern = None
        self.char_dup = []
        
        self.bold = False
        self.italic = False
        self.indexToLocFormat = None
        self.glyphDataFormat = None

        
    idxsort = ['head','maxp','cmap','loca','glyf','hhea','hmtx','post','name','OS/2','prep','cvt ','fpgm']
    #idxsort = dict( (n,i) for i, n in enumerate(idxsort) )
    
    def load( self, fname ):
        
        if os.path.isdir('./workspace'):
            self.load_packs( fname )
        
        self.load_ttf( fname )
        
    def load_packs( self, path ):
        
        path += '' if path.endswith('/') else '/'
        
        with open( path+'char_defines', 'r' ) as fp :
            self.char_defines = pickle.load( fp )
        
        with open( path+'char_kern', 'r' ) as fp :
            self.char_kern = pickle.load( fp )
        
        with open( path+'char_dup', 'r' ) as fp :
            self.char_dup = pickle.load( fp )
            
        with open( path+'fix_entrys', 'r' ) as fp :
            self.fix_entrys = pickle.load( fp )

        with open( path+'stt_entrys', 'r' ) as fp :
            self.stt_entrys = pickle.load( fp )
        
        with open( path+'global', 'r' ) as fp :
            
            g = pickle.load( fp )
            self.name = g['name']
            self.tuplename = g['tuplename']
            
            self.sfntversion = g['sfntversion']
            
            self.bold = g['bold']
            self.italic = g['italic']
            self.indexToLocFormat = g['indexToLocFormat']
            self.glyphDataFormat = g['glyphDataFormat']
        
        return
    
    def load_ttf( self, fname ):
        
        with open(filename) as fp :
            
            directory = self.ebp.read( 'ttf', fp )['directory']
            entrys = directory.pop('entry')
            
            self.sfntversion = directory['sfntversion']
            
            entrys = [ e for e in entrys if e['tag'] in idxsort ]
            entrys.sort( key = lambda e : self.idxsort.index(e['tag']) )
            
            for e in entrys :
                read_entry( fp, e, entrys )
                
        chrdef = zip( entrys['post']['data'],
                      entrys['glyf']['data'], 
                      entrys['hmtx']['data'] )
        self.char_defines = dict( (k, chrdef[v]) for k, v in entrys['hmtx']['cmap'] )
        

        setv = [ v for k, v in entrys['hmtx']['cmap'] ]
        inmap = [ (v, [ k for k, v in entrys['hmtx']['cmap'] if v == sv ]) for sv in setv ]
        self.char_dup = [ tuple(ks) for g, ks in inmap ]

        if 'kern' in entrys :
            
            inmap = dict(inmap)
            
            scs, das = zip(*entrys['kern']['data'])
            das = [ [(il, ir, v) for l,r,v in da for il in inmap[l] for ir in inmap(r)] for da in das ]
            self.kern = zip(scs, das)
        
        return
    
    def read_entry( self, fp, e, ae ):
        
        fp.seek(entry['offset'])
        if e['tag'] != 'head' and e['checksum'] != checksum( fp.read( e['length'] ) ) :
            raise TTFError, 'checksum error in ' + e['tag']
        fp.seek(entry['offset'])
        extent = getattr( self, 'read_' + e['tag'].replace('/','_').strip().lower(), self.extract_default )
        
        return extent( fp, e )
    
    def read_default( self, fp, e, ae ):
        
        self.fix_entrys[e['tag']] = fp.read( e['length'] )
        
    def read_head( self, fp, e, ae ):
        
        head = self.ebp.read('head', fp)
        
        macstryle = head.pop('macStyle')
        self.bold, self.italic = ( macstryle & 0x1 == 0 ), ( macstryle & 0x2 == 0 )
        self.indexToLocFormat = head.pop('indexToLocFormat')
        self.glyphDataFormat = head.pop('glyphDataFormat')

        head.pop('checkSumAdjustment')
        head.pop('magicNumber')
        
        self.stt_entrys['head'] = head
        
    def read_maxp( self, fp, e, ae ):
        
        maxp = self.ebp.read('maxp', fp)
        
        self.numGlyphs = maxp.pop('numGlyphs')
        
        self.stt_entrys['maxp'] = maxp
        
    def read_cmap( self, fp, e, ae ):
        
        _cmap = self.ebp.read( 'cmap', fp )
        _cmap = [ ( (cmapt['platformID'],cmapt['encodingID']), cmapt ) 
                  for cmapt in _cmap['cmap'] ]
        
        cmapt = _cmap.get( (0,3), None ) or _cmap.get( (0,3), None )
        if cmapt == None :
            raise TTFError, 'cmap read error.'
        
        fp.seek(e['offset']+cmapt['offset'])
        cmap = self.ebp.read('cmaptable', fp)
        fm4 = cmap['cmap']['format4']
        
        segnum = list(range(fm4['segCountX2']/2,0,-1))
        
        segs = zip( segnum, fm4['startCount'], fm4['endCount'], fm4['idDelta'], fm4['idRangeOffset'])
        
        r = []
        
        for segc, s, e, delta, offset in segs:
            
            if offset != 0 :
                rs = offset/2 - segc
                re = rs + e - s
                vs = [ (v+delta)%65536 for v in fm4['plyphIdArray'][rs:re+1] ]
                r.extend( zip(range(s,e+1),vs) )
            else :
                r.extend( [ (k, (k+delta)%65536) for k in range(s,e+1) ] )
        
        e['data'] = [ (unichr(k), v) for k, v in r ]
    
    def read_kern( self, fp, e, ae ):
        
        kern = self.ebp.read('kern', fp)
        
        r = []
        for k in kern['subTables'] :
            sc = k['subcoverage']
            da = [ (d['left'],d['right'],d['value'])
                   for d in k['field']['format0']['values'] ]
            r.append((sc,da))
        
        e['data'] = r

    def read_loca( self, fp, e, ae ):
        
        _loca = self.ebp.read( 'loca', fp,
                               numGlyphs = self.numGlyphs, 
                               indexToLocFormat = self.indexToLocFormat )
        _loca = _loca['loca']
        
        if 'loca_short' in _loca :
            e['data'] = tuple( l*2 for l in _loca['loca_short'] )
        else :
            e['data'] = _loca['loca_long']

    def read_glyf( self, fp, e, ae ):
        
        loca = ae['loca']['data']

        g = []
        
        for offset, end in zip( loca[:-1], loca[1:] ) :
            le = end - offset
            fp.seek( e['offset'] + offset )
            g.append( fp.read(le) )

        e['data'] =  g
        
    def read_hhea( self, fp, e, ae ):
        
        hhea = self.ebp.read('hhea', fp)
        
        hhea.pop('reversed1')
        hhea.pop('reversed2')
        hhea.pop('reversed3')
        hhea.pop('reversed4')
        hhea.pop('reversed5')
        
        self.numberOfHMetrics = hhea.pop('numberOfHMetrics')
        
        self.stt_entrys['hhea'] = hhea
    
    def read_hmtx( self, fp, e, ae ):
        
        r = self.ebp.read( 'hmtx', fp, 
                            numGlyphs=self.numGlyphs, 
                            numberOfHMetrics=self.numberOfHMetrics )
                            
        hms = r['hMetrics']
        nhlsbs = r['nonHorizontalLeftSideBearing']
        lastwith = r['hMetrics'][-1]['advanceWidth']
        
        hmtxmetrix  = [ ( hm['advanceWidth'], hm['leftSideBearing'] ) 
                        for hm in hms ]
        hmtxmetrix += [ ( lastwith, nhlsb ) for nhlsb in nhlsbs ]
        
        e['data'] = hmtxmetrix
        
    def read_post( self, fp, e, ae ):
        
        r = self.ebp.read( 'post', fp, 
                           numGlyphs = self.numGlyphs, length=e['length'] )
                           
        glyphNames = r.pop('glyphNames')
        
        self.stt_entrys['post'] = r
        
        if 'Format20' in glyphNames :
            gnames = glyphNames['Format20']
            ns = [ n['name'] for n in gnames['stt_names'] ]
            ns = range(0,258) + ns
            e['data'] = [ ns[i] for i in gnames['index'] ]
        else :
            e['data'] = [0]*self.numGlyphs
            
    def read_name( self, fp, e, ae ):
        
        _name = self.ebp.read( 'name', fp, length=e['length'] )
        
        ids = [ (nr['PlatformID'], nr['encodingID'], nr['LanguageID']) 
                for nr in _name['nameRecords'] ]
        
        ids = set(ids)
        ids = [ (pid, eid, lcid) 
                for pid, eid in [(3,1),(0,3),(1,0)] 
                for lcid in (1033,0) 
                if (pid,eid,lcid) in ids ]
        
        if ids == [] :
            raise TTFError, 'get name error.'
        
        for pid, eid, lcid in ids :
            
            nrs = [ nr for nr in r['nameRecords'] 
                    if (nr['PlatformID'], nr['encodingID'], nr['LanguageID']) == (pid, eid, lcid) ]
            
            if len(nrs) < 8 :
                continue
            
            nrs.sort( key = lambda n:n['NameID'] )
            if any( (i != nr['NameID']) for i, nr in enumerate(nrs) ):
                continue
            
            nrs = [ (nm['stringOffset'],nm['stringLength']) for nr in nrs ]
            nrs = [ (off,off+le) for off, le in nrs ]
            
            nrs = [ _name['data'][st:ed] for st, ed in nrs ]
            
            deco = 'mac_roman' if pid == 1 else 'utf-16BE'
            
            self.nametuple = [ n.decode(deco) for n in nrs ][:8]
            self.name = self.nametuple[4]
            return
            
        raise TTFError, 'error'
    
    def dump_packs( self, path ):
        
        path += '' if path.endswith('/') else '/'
        
        with open( path + 'global', 'w' ) as fp :
            
            g = {}
            
            g['name'] = self.name
            g['tuplename'] = self.tuplename 
            
            g['sfntversion'] = self.sfntversion
            
            g['bold'] = self.bold
            g['italic'] = self.italic
            g['indexToLocFormat'] = self.indexToLocFormat
            g['glyphDataFormat'] = self.glyphDataFormat
            
            pickle.dump( g, fp )
            
        with open( path+'char_defines', 'w' ) as fp :
            pickle.dump( self.char_defines, fp )
        
        with open( path+'char_kern', 'w' ) as fp :
            pickle.dump( self.char_kern, fp )
        
        with open( path+'char_dup', 'w' ) as fp :
            pickle.dump( self.char_dup, fp )
            
        with open( path+'fix_entrys', 'w' ) as fp :
            pickle.dump( self.fix_entrys, fp )

        with open( path+'stt_entrys', 'w' ) as fp :
            pickle.dump( self.stt_entrys, fp )
            
        char_blocks = {}
        for k in self.char_defines :
            char_blocks.get( (self.unicode_block[ord(k)>>8]) if k!=0 else 'null', [] ).append(k)
        char_blocks[''] = self.char_defines.keys()
        
        for v in char_blocks.values() :
            v.sort()
        
        with open( path+'char_blocks', 'w' ) as fp :
            pickle.dump( char_blocks, fp )
            
            
        return
    
    def dump_ttf( self, fname ):
        
        
        ks = self.char_defines.keys()
        ks.sort()
        
        if ks == [] or ks[0] != 0 :
            raise TTFError, 'must have char 0x0000'
        
        charidx = [ (k,i) for i in k enumerate(ks) ] 
        charidx = dict(charidx)
        
        
        entrys = self.idxsort[:]
        entrys.sort()
        
        entrys = [ self.getattr( 'dump_'+e.replace('/','_').strip().lower() ) for e in self.idxsort ]
        entrys = [ e( ks, charidx ) for e in self.idxsrot ]
        entrys = zip(entrys, self.idxsort)
        entrys = [ ( r, name ) for r, name in entrys if r != None ]
            
        le_entrys = len(entrys)
        le_dirs = 12+le_entrys*16
        
        entrys = [ (name, cs, le, data) for (cs, le, data), name in entrys ]
        names, csums, lens, entrydatas = zip(*entrys)
        pads = [ -(le%-4) for le in lens ]
        offsets = [ 12 + sum(lens[:i+1]) + sum(pads[:i+1]) for i in range( len(lens) ) ]
        entrys = zip( name, csums, offsets, lens )
        
        ests = [ self._dump_entry(e) for e in entrys ]
        
        searchrange, entryselector, rangeshift = make_ser(le_entrys,16)
        
        directory = struct.pack('>HHHHHH',
            self.sfntversion['major'], self.sfntversion['sub'],
            le_entrys,
            searchrange, entryselector, rangeshift,
        )
        
        directory += ''.join(ests)
        
        entrys = [( '', checksum(directory), 0, le_dirs )] + entrys
        entrysdata = [direcotry] + entrysdata
        pads = [ -(le_dirs%-4) ] + pads

        with open( fname, 'w' ) as fp :
            
            for ed, pa in zip(entrysdata, pads) :
                
                if callable(ed) :
                    ed = ed( entrys )
                
                if type(ed) != types.StirngType :
                    for edi in ed :
                        fp.write(edi)
                else :
                    fp.write(ed)
                
                fp.write(pads)
        
        return
        
    @staticmethod
    def _dump_entry( e ):
        return struct.pack('>4sIII', *e)
            
    def dump_head( self, _unused_ks, _unused_charidx, entrys = None ):
        
        _head = self.stt_entrys['head']
        
        checkSumAdjustment = 0 if entrys == None else (( 0xB1B0AFBA - sum_checksum(zip(*entrys)[1]) ) % 0x100000000)
        
        head = struct.pack('>HHHHIIHH8s8shhhhHHhhh',
            _head['version']['major'], _head['version']['sub'],
            _head['reversion']['major'],_head['reversion']['sub'],
            checkSumAdjustment,
            0x5F0F3CF5, #magicNumber
            _head['flags'],
            _head['unitsPerEm'],
            ''.join( chr(c) for c in _head['created']),
            ''.join( chr(c) for c in _head['modified']),
            _head['xMin'],
            _head['yMin'],
            _head['xMax'],
            _head['yMax'],
            self.bold*1 + self.italic*2, #macStyle
            _head['lowestRecPPEM'],
            _head['fontDirectionHint'],
            0, #indexToLocFormat,
            self.glyphDataFromat,
        )
        
        if entrys is None :
            return checksum(head), len(head), self.dump_head
        
        return checksum(head), len(head), head
        
    def dump_maxp( self, ks, charidx ):
        
        _maxp = self.entrys['maxp']
        maxp = struct.pack( '>'+'H'*16,
            _maxp['version']['major'], _maxp['version']['sub'],
            self.numGlyphs,
            _maxp['maxPoints'],
            _maxp['maxContours'],
            _maxp['maxCompositePoints'],
            _maxp['maxCompositeContours'],
            _maxp['maxZones'],
            _maxp['maxTwilightPoints'],
            _maxp['maxStorage'],
            _maxp['maxFunctionDefs'],
            _maxp['maxInstructionDefs'],
            _maxp['maxStackElements'],
            _maxp['maxSizeOfInstructions'],
            _maxp['maxComponentElements'],
            _maxp['maxComponentDepth'],
        )
        
        return checksum(maxp), len(maxp), maxp
        
    def _dump_cmap_format6_roman( self, _unused_ks, charidx ):
        
        format6 = [ ord(chr(c+0x20).decode('mac_roman')) for c in range(0,224) ]
        format6 = [ charidx.get(c+0x20,0) for c in format6 ]
        format6 = [ int16b(c) for c in format6 ]
        format6 = ''.join(format6)
        format6 = struct.pack('>HH',0x20,224)+format6
        
        f6len = len(format6)+6
        format6 = struct.pack('>HHH',6,f6len,0) + format6
        
        return format6
    
    def _dump_cmap_format4_unicode( self, ks, charidx ):
        
        format4 = [(ks[0],ks[0])]
        for c in ks[1:] :
            if format4[-1][1] == c-1 :
                format4[-1] = (format4[-1][0],c)
                continue
            format4.append((c,c))
        
        format4.append((65535,65535))
        
        format4 = [ (st,en,(charidx.get(st,0)-st)%65536) for st, en in format4 ]
        
        f4st = ''.join([ int16b(st) for st in zip(*format4)[0] ])
        f4en = ''.join([ int16b(en) for en in zip(*format4)[1] ])
        f4dt = ''.join([ int16b(dt) for dt in zip(*format4)[2] ])
        
        f4len = len(format4)
        searchrange, entryselector, rangeshift = make_ser(f4len,2)
        format4 = struct.pack('>HHHH',
            f4len*2, #segCountX2
            searchrange,
            entryselector,
            rangeshift,
        ) + f4en + chr(0) + chr(0) + f4st + f4dt + chr(0)*(f4len*2)
        
        f4len = len(format4)+6
        format4 = struct.pack('>HHH',4,f4len,0) + format4
        
        return format4
    
    def dump_cmap( self, ks, charidx ):
        
        format6 = _dump_cmap_format6_roman(ks,charidx)
        format4 = _dump_cmap_format4_unicode(ks,charidx)
        
        cmap = struct.pack('>HHHHIHHIHHI',
            0, 3,
            0, 3, 28,
            1, 0, len(format4)+28,
            3, 1, 28,
        )
        
        cmap = cmap + format4 + format6
        
        return checksum(cmap), len(cmap), cmap
    
    def dump_loca( self, ks, charidx ):
        
        glyf = [ self.char_defines[k][1] for k in ks ]
        
        loca = [ len(g) for g in glyf ]
        loca = [ sum(loca[0:i])/2 for i in range(loca+1) ]
        
        loca = ''.join( int16b(lo) for lo in loca )
        
        return checksum(loca), len(loca), loca
    
    def dump_glyf( self, ks, charidx ):
        
        glyf = [ self.char_defines[k][1] for k in ks ]
        
        glyflen = sum( len(g) for g in glyf )
        
        return checksum(glyf), glyflen, glyf
    
    def _dump_kern_table( self, subcoverage, da ):
        
        field = [ struct.pack('>HHh',*d) for d in da ]
        
        fieldlen = len(field)*len(field[0])
        
        searchrange, entryselector, rangeshift = make_ser(fele,6)
        fieldhead = struct.pack('>HHHH', filedlen,
                                        searchrange, entryselector, rangeshift,
                               )
        
        tablelen = struct.calcsize('>HHBB') + len(fieldhead) + fieldlen
        
        tablehead = struct.pack('>HHBB',
            0, #version
            tablelen,
            0, #format
            subcoverage,
        )
        
        return tablelen, [tablehead,fieldhead,]+fieldlen
    
    def dump_kern( self, ks, charidx ):
        
        if self.char_kern is None :
            return
        
        scs, das = zip(*self.kern)
        
        das = [ [ (charidx[l], charidx[r], v) for l, r, v in da 
                  if l in charidx and r in charidx ] 
               for da in das ]
        
        tables = [ self._dump_kern_table(sc,da) for sc, da in zip(scs,das)]
        tablelens, tables = zip(*tables)
        
        kernhead = struct.pack('>HH',0,len(tables))
        
        kern = [kernhead]+tables
        
        return checksum(kern), len(kernhead)+sum(tablelens), kern
    
    def dump_hhea( self, ks, charidx ):
        
        _hhea = self.stt_entrys['hhea']
        hhea = struct.pack( '>HHhhhHhhhhhhhhhhhH',
            _hhea['version']['major'], _hhea['version']['sub'],
            _hhea['ascender'],
            _hhea['descender'],
            _hhea['lineGap'],
            _hhea['advanceWidthMax'],
            _hhea['minLeftSideBearing'],
            _hhea['minRightSideBearing'],
            _hhea['xMaxExtent'],
            _hhea['caretSlopeRise'],
            _hhea['caretSlopeRun'],
            0,0,0,0,0, #reversed
            _hhea['metricDataFormat'],
            self.numGlyphs, #numberOfHMetrics,
        )
        
        return checksum(hhea), len(hhea), hhea
        
    def dump_hmtx( self, ks, charidx ):
        
        hmtx = [ self.char_defines[k][2] for k in ks ]
        hmtx = [ struct.pack('>Hh', a, lsb) for a, lsb in hmtx ]
        
        return checksum(hmtx), len(hmtx)*len(hmtx[0]), hmtx
        
    def dump_post( self, ks, charidx ):
        
        _post = self.stt_entrys['post']
        posthead = struct.pack('>HHHHhhIIIII',
            2, 0,
            _post['atalicAngle']['major'], _post['atalicAngle']['sub'],
            _post['underlinePosition'],
            _post['underlineThickness'],
            _post['isFixedPitch'],
            _post['minMemType42'],
            _post['maxMemType42'],
            _post['minMemType1'],
            _post['maxMemType1'],
        )
        
        post = [ self.char_defines[k][0] for k in ks ]
        idx = []
        strnames = []
        i = 0
        for p in post :
            if type(p) == types.IntType :
                idx.append(p)
            else :
                strnames.append(p)
                idx.append( 257 + len(strname) )
                
        idx = ''.join( int16b(p) for p in idx )
        strnames = ''.join( chr(len(sn))+sn for sn in strnames )
        
        post = [ posthead, int16b(self.numGlyphs), idx, strnames ]
        
        return checksum(post), len(posthead)+2+len(idx)+len(strnames), post
        
    def dump_os_2( self, ks, charidx ):
        os = self.fix_entrys['OS/2']
        return checksum(os), len(os), os
        
    def dump_prep( self, ks, charidx ):
        prep = self.fix_entrys['prep']
        return checksum(prep), len(prep), prep
        
    def dump_cvt( self, ks, charidx ):
        cvt = self.fix_entrys['cvt ']
        return checksum(cvt), len(cvt), cvt

    def dump_fpgm( self, ks, charidx ):
        fpgm = self.fix_entrys['fpgm']
        return checksum(fpgm), len(fpgm), fpgm

    def subset( self, subchrs ):
        
        return
    

    