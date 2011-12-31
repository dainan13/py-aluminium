# -*- coding: utf-8 -*-


import easyprotocol as ezp
import cStringIO
import struct
import os.path
import cPickle as pickle

import pprint


class TTFError(Exception):
    pass


def checksum( inp, le=None ):
    
    if le != None :
        inp = inp.read( length )
    
    r = 0
    for i, c in enumerate(inp) :
        i = 3 - (i % 4)
        r += c << (i*8)
        r = r & 0xFFFFFFFF
    
    return r

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
            
        #if numberOfPoints != 0 :
        #    raise  Exception, ('length check error', numberOfPoints)
        
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
        


    fname=os.path.realpath(sys.argv[0])
    fname=fname[:fname.rfind('.')]+'.pdf'

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

        
    idxsort = ['head','maxp','cmap','loca','glyf','hhea','hmtx','post','name','os_2','prep','cvt','fpgm']
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
        extent = getattr( self, 'read_' + e['tag'].replace('/','_').strip(), self.extract_default )
        
        return extent( fp, e )
    
    def read_default( self, fp, e, ae ):
        
        self.fix_entrys[e['tag']] = fp.read( e['length'] )
        
    def read_head( self, fp, e, ae ):
        
        head = self.ebp.read('head', fp)
        
        #macstryle = head.pop('macStyle')
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
        
        r = []
        
        for segc, s, e, delta, offset in zip( range(fm4['segCountX2']/2,0,-1), fm4['startCount'], fm4['endCount'], fm4['idDelta'], fm4['idRangeOffset']):
            
            if offset != 0 :
                rs = offset/2 - segc
                re = rs + e - s
                vs = [ (v+delta)%65536 for v in fm4['plyphIdArray'][rs:re+1] ]
                r.extend( zip(range(s,e+1),vs) )
            else :
                r.extend( [ (k, (k+delta)%65536) for k in range(s,e+1) ] )
        
        e['data'] = r
    
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
            char_blocks.get( (self.unicode_block[k>>8]) if k!=0 else 'null', [] ).append(k)
                
        with open( path+'char_blocks', 'w' ) as fp :
            pickle.dump( char_blocks, fp )
            
            
        return
    
    def dump_ttf( self, fname ):
        
        entrys = [ self.getattr( 'dump_'+e )() for e in self.idxsort ]
        entrys = [ (name, le, cs data) for (le, cs, data), name in zip(entrys, self.idxsort) if data != None ]
        
        dirsearchrange, direntryselector, dirrangeshift = make_ser(len(allentry),16)
        sorted_allentry = allentry[:]
        sorted_allentry.sort( key = lambda x: x['tag'] )
        
        directory = struct.pack('>HHHHHH',
            self.sfntversion['major'], self.sfntversion['sub'],
            len(allentry),
            dirsearchrange,
            direntryselector,
            dirrangeshift,
        ) + ''.join( e['entrydata'] for e in e )

        with open( fname, 'w' ) as fp :
            fp.write()
        
        return
        
    def _dump_entry( self, e ):
        
        return
        
    def dump_head( self, entrys = None ):
        
        return
        
    def dump_cmap( self ):
        
        return
        
    def subset( self, subchrs ):
        
        return
    

    