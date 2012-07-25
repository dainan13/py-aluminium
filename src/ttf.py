# -*- coding: utf-8 -*-

if __name__ == '__main__' :
    try :
        import easyprotocol as ezp
    except :
        from Al import easyprotocol as ezp
else :
    from . import easyprotocol as ezp

import cStringIO
import struct
import types
import os.path
import cPickle as pickle


import hashlib

import pprint


__filepath__ = str(os.path.realpath(__file__).rsplit('/',1)[0])


class TTFError(Exception):
    pass


def checksum( inp, le=None ):
    
    
    if type(inp) == types.FileType and le != None :
        inp = inp.read( le )
    
    if type(inp) == types.StringType :
    
        #r = 0
        #for i, c in enumerate(inp) :
        #    i = 3 - (i % 4)
        #    r += ord(c) << (i*8)
        #    r = r & 0xFFFFFFFF
        inp = [inp]

    
    if type(inp) == types.ListType :
        
        r = 0
        i = 0
        
        for lc in inp :
            
            if type(lc) != types.StringType :
                raise TTFError, 'type error in checksum'
                
            for c in lc :
                r += ( ord(c) << ((3-(i%4))*8) )
                r = r & 0xFFFFFFFF
                i += 1
                
        return r
    
    raise TTFError, 'type error in checksum'
    #return r

def sum_checksum( checksums ):
    return sum( checksums ) & 0xFFFFFFFF

def int16b( ch ):
    return chr(ch/256) + chr(ch%256)

def int32b( ch ):
    return chr(ch/(256**3)) + chr((ch/(256**2))%256) + chr((ch/256)%256) + chr(ch%256)

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
    lns = [ (int(st,16),int(ed,16),name) for (st, ed), name in lns ]
    lns = [ (st,ed,name) for st, ed, name in lns if st < 0xFFFF ]
    
    xlns = [ (b[1]+1,a[0]-1,'nodefined '+hex(b[1]+1)+'..'+hex(a[0]-1)) 
             for b, a in zip(lns,lns[1:]) if b[1]+1 != a[0] ]
    
    lns = lns + xlns
    lns.sort( key = lambda n:n[0] )
    
    return lns

def init_unicodemap( unicodemap ):
    
    p = __filepath__ + '/protocols/Blocks-6.1.0d1.txt'
    block = load_unicode_block( p )
    #block = load_unicode_block( os.path.dirname(__file__)+'/protocols/Blocks-6.1.0d1.txt' )
    
    namesearch = dict( (name, (st,ed)) for st, ed, name in block )
    charsearch = [ name for st, ed, name in block for s in range(st>>8,(ed>>8)+1) ]
    
    unicodemap.namesearch = namesearch
    unicodemap.charsearch = charsearch
    
    return unicodemap

@init_unicodemap
class UnicodeMap(object):
    
    def __init__( self ):
        
        pass
        
    def __getitems__( self, index ):
        
        if len(index) != 1 :
            
            n = self.namesearch.get(index,None)
            
            if n is None :
                raise IndexError, 'map not found'
            
            return UnicodeMapSet(n)
            
        else :
            
            n = self.charsearch[ ord(unicode(index)) >> 8 ]
            
            return n
    
    def getname( self, c ):
        n = self.charsearch[ ord(unicode(c)) >> 8 ]
        return n
    
    def getset( self, n ):
        n = self.namesearch.get(n,None)
        if n is None :
            raise IndexError, 'map not found'
        return UnicodeMapSet(n)
        
    
unimap = UnicodeMap()

class UnicodeMapSet( object ):
    
    def __init__ ( self, seg ):
        
        self.seg = seg
        
        self.min = seg[0]
        self.max = seg[1]
        
        self.st = unichr(seg[0])
        self.ed = unichr(seg[1])
    
    def by_difference( self, other ):
        
        if type(other) != set :
            raise TypeError, 'inp type error.'
        
        st, ed = self.st, self.ed
        
        return set( s for s in other if s < st or s > ed )
    
    def by_intersection( self, other ):
        
        if type(other) != set :
            raise TypeError, 'inp type error.'
        
        st, ed = self.st, self.ed
        
        return set( s for s in other if s >= st or s <= ed )


class TTFile(object):
    
    ebp = ezp.EasyBinaryProtocol()
    ebp.buildintypes.append(FLAGSType())
    ebp.buildintypes.append(COORDSType())
    ebp.rebuild_namespaces()
    ebp.parsefile( __filepath__+'/protocols/ttf.protocol' )
    
    def __init__( self, fn=None, noglyph=False ):
        
        self.name = None
        self.nametuple = None
        
        self.sfntversion = None
        
        self.fix_entrys = {}
        self.stt_entrys = {}
        self.char_defines = {}
        self.char_kern = None
        self.char_dup = []
        
        self.bold = False
        self.italic = False
        self.indexToLocFormat = None
        self.glyphDataFormat = None
        
        self.numGlyphs = None
        
        if fn != None :
            self.load( fn, noglyph )
        
    idxsort = ['head','maxp','cmap','loca','glyf','kern','hhea','hmtx','post','name','OS/2','prep','cvt ','fpgm']
    requiredtable = set(['head','maxp','cmap','loca','glyf','hhea','hmtx','post','name','OS/2',])
    #idxsort = dict( (n,i) for i, n in enumerate(idxsort) )
    
    pdfrequired = set(['head', 'loca', 'maxp', 'glyf', 'hhea', 'hmtx'])
    # missing set(['OS/2', 'post', 'cmap', 'name'])
    
    def load( self, fname, noglyph=False ):
        
        if os.path.isdir(fname):
            self.load_packs( fname, noglyph )
        else :
            self.load_ttf( fname, noglyph )
        
    def load_packs( self, path, noglyph=False ):
        
        path += '' if path.endswith('/') else '/'
        
        if noglyph :
            with open( path+'char_blocks', 'r' ) as fp :
                ks = pickle.load( fp )['']
                self.char_defines = dict(zip(ks,[None]*len(ks)))
        else :
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
            self.nametuple = g['nametuple']
            
            self.sfntversion = g['sfntversion']
            
            self.bold = g['bold']
            self.italic = g['italic']
            self.indexToLocFormat = g['indexToLocFormat']
            self.glyphDataFormat = g['glyphDataFormat']
            
            self.numGlyphs = g['numGlyphs']
        
        return
    
    def load_ttf( self, fname, noglyph=False ):
        
        if noglyph :
            self.idxsort = self.idxsort[:]
            self.idxsort.remove('glyf')
            self.idxsort.remove('hmtx')
        
        with open(fname) as fp :
            
            directory = self.ebp.read( 'ttf', fp )['directory']
            entrys = directory.pop('entry')
            
            self.sfntversion = directory['sfntversion']
            
            entrys = [ e for e in entrys if e['tag'] in self.idxsort ]
            entrys.sort( key = lambda e : self.idxsort.index(e['tag']) )
            
            ae = dict( (e['tag'],e) for e in entrys )
            
            for e in entrys :
                self.read_entry( fp, e, ae, True )
                
        if noglyph :
            
            self.char_defines = dict( zip(ae['cmap']['data'],[None]*self.numGlyphs) )
            
        else :
            chrdef = zip( ae['post']['data'],
                          ae['glyf']['data'], 
                          ae['hmtx']['data'] )
            
            self.cmap = dict( ae['cmap']['data'] )
            self.char_defines = dict( (k, chrdef[v]) for k, v in ae['cmap']['data'] )
        

        inmap = {}
        for k, v in ae['cmap']['data'] :
            inmap.setdefault(v,[])
            inmap[v].append(k)
        self.char_dup = [ tuple(ks) for ks in inmap.values() if len(ks) > 1 ]

        if 'kern' in entrys :
            
            inmap = dict(inmap)
            
            scs, das = zip(*ae['kern']['data'])
            das = [ [(il, ir, v) for l,r,v in da for il in inmap[l] for ir in inmap(r)] for da in das ]
            self.kern = zip(scs, das)
        
        return
    
    def load_CID( self, CID ):
        
        if issubclass( type(CID), str ) :
            fp = cStringIO.StringIO( CID )
        else :
            fp = CID
        
        directory = self.ebp.read( 'ttf', fp )['directory']
        entrys = directory.pop('entry')
        
        self.sfntversion = directory['sfntversion']
        
        entrys = [ e for e in entrys if e['tag'] in self.idxsort ]
        entrys.sort( key = lambda e : self.idxsort.index(e['tag']) )
        
        ae = dict( (e['tag'],e) for e in entrys )
        
        for e in entrys :
            self.read_entry( fp, e, ae, False )
        
        self.ae = ae
        
        return
    
    def antidefines( self, another ):
        
        t = another.antidefines_table()
        
        gmd5 = [ hashlib.md5(g).hexdigest() for g in self.ae['glyf']['data'] ]
        
        r = [ t[g] for g in gmd5 ]
        
        return r, [ another.cmap[ir[0]] for ir in r ]
    
    def antidefines_table( self ):
        
        ad = [ ( hashlib.md5(g[1]).hexdigest(), c ) 
               for c, g in self.char_defines.items() ]
        
        r = {}
        for gmd5, c in ad :
            r.setdefault(gmd5,[])
            r[gmd5].append(c)
        
        return r
        
    def read_entry( self, fp, e, ae, check=True ):
        
        fp.seek(e['offset'])
        if check and e['tag'] != 'head' :
            c = fp.read( e['length'] )
            if len(c) != e['length'] :
                raise TTFError, 'length error in ' + e['tag']
            if e['checksum'] != checksum( c ) :
                raise TTFError, 'checksum error in ' + e['tag']
        fp.seek(e['offset'])
        extent = getattr( self, 'read_' + e['tag'].replace('/','_').strip().lower(), self.read_default )
        
        return extent( fp, e, ae )
    
    def read_default( self, fp, e, ae ):
        
        self.fix_entrys[e['tag']] = fp.read( e['length'] )
        
    def read_head( self, fp, e, ae ):
        
        head = self.ebp.read('head', fp)
        
        macstryle = head.pop('macStyle')
        self.bold, self.italic = ( macstryle & 0x1 ), ( macstryle & 0x2 )
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
        _cmap = dict(_cmap)
        
        cmapt = _cmap.get( (0,3), None ) or _cmap.get( (3,1), None )
        if cmapt == None :
            raise TTFError, ('cmap read error.', _cmap)
        
        fp.seek(e['offset']+cmapt['offset'])
        cmap = self.ebp.read('cmaptable', fp)
        fm4 = cmap['cmap']['format4']
        
        segnum = list(range(fm4['segCountX2']/2,0,-1))
        
        segs = zip( segnum, fm4['startCount'], fm4['endCount'], fm4['idDelta'], fm4['idRangeOffset'])
        
        r = []
        
        for segc, st, ed, delta, offset in segs:
            
            if offset != 0 :
                rs = offset/2 - segc
                re = rs + ed - st
                vs = [ (v+delta)%65536 for v in fm4['plyphIdArray'][rs:re+1] ]
                r.extend( zip(range(st,ed+1),vs) )
            else :
                r.extend( [ (k, (k+delta)%65536) for k in range(st,ed+1) ] )
        
        if r[0][0] != 0 :
            r = [(0,0)] + r
        
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
        elif 'Format10' in glyphNames :
            gnames = list(range(0,258)) + [0]*(self.numGlyphs-258)
            e['data'] = gnames[:self.numGlyphs]
        elif 'Format25' in glyphNames :
            e['data'] = glyphNames['Format25']['index']
        elif 'Format30' in glyphNames :
            e['data'] = [0]*self.numGlyphs
        else :
            raise TTFError, 'unsupported format of post table.'
            
    def read_name( self, fp, e, ae ):
        
        _name = self.ebp.read( 'name', fp, length=e['length'] )
        
        #print _name
        
        ids = [ (nr['platformID'], nr['encodingID'], nr['LanguageID']) 
                for nr in _name['nameRecords'] ]
        
        _ids = set(ids)
        ids = [ (pid, eid, lcid) 
                for pid, eid in [(3,1),(0,3),(1,0)] 
                for lcid in (1033,0) 
                if (pid,eid,lcid) in _ids ]
        
        if ids == [] :
            raise TTFError, 'get name error.'
        
        for pid, eid, lcid in ids :
            
            nrs = [ nr for nr in _name['nameRecords'] 
                    if (nr['platformID'], nr['encodingID'], nr['LanguageID']) == (pid, eid, lcid) ]
            
            if len(nrs) < 8 :
                continue
            
            nrs.sort( key = lambda n:n['NameID'] )
            if any( (i != nr['NameID']) for i, nr in enumerate(nrs[:8]) ):
                continue
            
            nrs = [ (nm['stringOffset'],nm['stringLength']) for nm in nrs ]
            nrs = [ (off,off+le) for off, le in nrs ]
            
            nrs = [ _name['data'][st:ed] for st, ed in nrs ]
            
            deco = 'mac_roman' if pid == 1 else 'utf-16BE'
            
            self.nametuple = [ n.decode(deco) for n in nrs ][:8]
            self.name = self.nametuple[4]
            return
        
        nrs = [ [ nr for nr in _name['nameRecords'] 
                  if (nr['platformID'], nr['encodingID'], nr['LanguageID']) == i ]
                for i in _ids
              ]
              
        for n in nrs :
            n.sort( key = lambda x: x['NameID'] )
        
        nids = [ [ nm['NameID'] for nm in n ] for n in nrs ]
        nrs = [ [ (nm['stringOffset'],nm['stringLength']) for nm in n ] for n in nrs ]
        nrs = [ [ _name['data'][off:off+le] for off, le in n ] for n in nrs ]
        
        raise TTFError, zip(_ids,nids,nrs)
    
    def dump_packs( self, path ):
        
        path += '' if path.endswith('/') else '/'
        
        with open( path + 'global', 'w' ) as fp :
            
            g = {}
            
            g['name'] = self.name
            g['nametuple'] = self.nametuple
            
            g['sfntversion'] = self.sfntversion
            
            g['bold'] = self.bold
            g['italic'] = self.italic
            g['indexToLocFormat'] = self.indexToLocFormat
            g['glyphDataFormat'] = self.glyphDataFormat
            
            g['numGlyphs'] = self.numGlyphs
            
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
            char_blocks.get( (unimap.getname(k)) if k!=chr(0) else 'null', [] ).append(k)
        char_blocks[''] = self.char_defines.keys()
        
        for v in char_blocks.values() :
            v.sort()
        
        with open( path+'char_blocks', 'w' ) as fp :
            pickle.dump( char_blocks, fp )
            
        return
    
    def _dump_ttf_write( self, fp, ks, charidx, entrydatas, pads, entrys ):
        
        for ed, pa, e in zip(entrydatas, pads, entrys) :
            
            st = fp.tell()
            
            if st != e[2] :
                raise TTFError, ( e[0], 'write file error.(offset)', st, e[2] )
            
            if callable(ed) :
                ed = ed( ks, charidx, entrys )[2]
            
            if type(ed) != types.StringType :
                
                for edi in ed :
                    fp.write(edi)
            else :
                fp.write(ed)
            
            ed = fp.tell()
            
            if e[3] != ed - st :
                raise TTFError, ( e[0], 'write file error.(length)', ed-st, e[3] )
            
            fp.write(chr(0)*pa)
                
        return
    
    def dump_ttf( self, fname=None, onlyrequiredtable=False ):
        
        
        ks = self.char_defines.keys()
        ks.sort()
        
        if ks == [] or ord(ks[0]) != 0 :
            raise TTFError, 'must have char 0x0000'
        
        charidx = [ (k,i) for i, k in enumerate(ks) ] 
        charidx = dict(charidx)
        
        
        ae = self.idxsort[:]
        ae.sort()
        
        if onlyrequiredtable == True :
            ae = [ e for e in ae if e in self.requiredtable ]
        
        entrys = [ getattr( self, 'dump_'+e.replace('/','_').strip().lower() ) for e in ae ]
        entrys = [ e( ks, charidx ) for e in entrys ]
        entrys = zip(entrys, ae)
        entrys = [ ( r, name ) for r, name in entrys if r != None ]
        
        le_entrys = len(entrys)
        le_dirs = 12+le_entrys*16
        le_pad = -(le_dirs%-4)
        
        entrys = [ (name, cs, le, data) for (cs, le, data), name in entrys ]
        names, csums, lens, entrydatas = zip(*entrys)
        pads = [ -(le%-4) for le in lens ]
        offsets = [ le_dirs + le_pad + sum(lens[:i]) + sum(pads[:i]) for i in range( len(lens) ) ]
        entrys = zip( names, csums, offsets, lens )
        
        #entrysort = entrys[:]
        #entrysort.sort( key = lambda x : x[0] )
        #ests = [ self._dump_entry(e) for e in entrysort ]
        ests = [ self._dump_entry(e) for e in entrys ]
        
        searchrange, entryselector, rangeshift = make_ser(le_entrys,16)
        
        directory = struct.pack('>HHHHHH',
            self.sfntversion['major'], self.sfntversion['sub'],
            le_entrys,
            searchrange, entryselector, rangeshift,
        )
        
        directory += ''.join(ests)
        
        entrys = [( '', checksum(directory), 0, le_dirs )] + entrys
        entrydatas = [directory] + list(entrydatas)
        pads = [ le_pad ] + pads
        
        
        if fname == None :
            
            fp = cStringIO.StringIO()
            self._dump_ttf_write( fp, ks, charidx, entrydatas, pads, entrys )
            
            return fp.getvalue()
        
        elif type( fname ) in types.Strings :
            
            with open( fname, 'wb' ) as fp :
                self._dump_ttf_write( fp, ks, charidx, entrydatas, pads, entrys )
            
        else :
            
            self._dump_ttf_write( fname, ks, charidx, entrydatas, pads, entrys )
            
        return
        
    @staticmethod
    def _dump_entry( e ):
        return struct.pack('>4sIII', *e)
            
    def dump_head( self, _unused_ks, _unused_charidx, entrys = None ):
        
        _head = self.stt_entrys['head']
        
        checkSumAdjustment = 0 if entrys is None else (( 0xB1B0AFBA - sum_checksum(zip(*entrys)[1]) ) % 0x100000000 )
        #checkSumAdjustment = 0
        
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
            1, #indexToLocFormat,
            self.glyphDataFormat,
        )
        
        if entrys is None :
            return checksum(head), len(head), self.dump_head
        
        return checksum(head), len(head), head
        
    def dump_maxp( self, ks, charidx ):
        
        _maxp = self.stt_entrys['maxp']
        #print self.numGlyphs, _maxp['maxPoints']
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
        
        format6 = [ chr(c+0x20).decode('mac_roman') for c in range(0,224) ]
        format6 = [ charidx.get(c,0) for c in format6 ]
        format6 = [ int16b(c) for c in format6 ]
        format6 = ''.join(format6)
        format6 = struct.pack('>HH',0x20,224)+format6
        
        f6len = len(format6)+6
        format6 = struct.pack('>HHH',6,f6len,0) + format6
        
        return format6
    
    def _dump_cmap_format4_unicode( self, ks, charidx ):
        
        ks = [ ord(k) for k in ks[1:] ]
        
        format4 = [(ks[0],ks[0])]
        for c in ks[1:] :
            if format4[-1][1] == c-1 :
                format4[-1] = (format4[-1][0],c)
                continue
            format4.append((c,c))
        
        format4.append((65535,65535))
        
        format4 = [ (st,en,(charidx.get(unichr(st),0)-st)%65536) for st, en in format4 ]
        
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
        
        format6 = self._dump_cmap_format6_roman(ks,charidx)
        format4 = self._dump_cmap_format4_unicode(ks,charidx)
        
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
        
        #loca = [ sum(loca[:i])/2 for i in range(len(loca)+1) ]
        #loca = ''.join( int16b(lo) for lo in loca )
        
        loca = [ sum(loca[:i]) for i in range(len(loca)+1) ]
        loca = ''.join( int32b(lo) for lo in loca )
        
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
        
        post = [ self.char_defines[k][0] for k in ks ]
        
        if all([ (p == 0) for p in post ]) :
            mv, sv = 3, 0
        else :
            mv, sv = 2, 0
        
        _post = self.stt_entrys['post']
        posthead = struct.pack('>HHHHhhIIIII',
            mv, sv,
            _post['atalicAngle']['major'], _post['atalicAngle']['sub'],
            _post['underlinePosition'],
            _post['underlineThickness'],
            _post['isFixedPitch'],
            _post['minMemType42'],
            _post['maxMemType42'],
            _post['minMemType1'],
            _post['maxMemType1'],
        )
        
        if ( mv, sv ) == (2, 0):
        
            idx = []
            strnames = []
            i = 0
            for p in post :
                if type(p) == types.IntType :
                    idx.append(p)
                else :
                    strnames.append(p)
                    idx.append( 257 + len(strnames) )
                    
            idx = ''.join( int16b(p) for p in idx )
            strnames = ''.join( chr(len(sn))+sn for sn in strnames )
            
            post = [ posthead, int16b(self.numGlyphs), idx, strnames ]
            
            return checksum(post), len(posthead)+2+len(idx)+len(strnames), post
            
        elif ( mv, sv ) == ( 3, 0 ):
            
            post = posthead
            return checksum(post), len(post), post
        
    def dump_name( self, ks, charidx ):
        
        le_record = len(self.nametuple)*2
        
        strings = [ s.encode('mac_roman', errors='ignore') for s in self.nametuple ] + \
                  [ s.encode('utf-16BE') for s in self.nametuple ]
        stringlens = [ len(s) for s in strings ]
        strlen = sum(stringlens)
        offsets = [ sum(stringlens[:i]) for i in range(len(stringlens)) ]
        
        nameids = list(range(len(self.nametuple)))*2
        pids = [1]*len(self.nametuple) + [3]*len(self.nametuple)
        eids = [0]*len(self.nametuple) + [1]*len(self.nametuple)
        lids = [0]*len(self.nametuple) + [1033]*len(self.nametuple)
        
        record = [ struct.pack('>HHHHHH', *arg) 
                   for arg in zip(pids,eids,lids,nameids,stringlens,offsets) ]
        
        recordlen = len(record)*struct.calcsize('>HHHHHH')
        le = struct.calcsize('>HHH') + recordlen + strlen
        
        namehead = struct.pack('>HHH', 0, le_record, le-strlen )
        
        name = [namehead,] + record + strings
        
        return checksum(name), le, name
        
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
    
    def copy( self ):
        
        another = TTFile()
        
        another.name = self.name
        another.nametuple = self.nametuple
        
        another.sfntversion = self.sfntversion
        
        another.bold, another.italic = self.bold, self.italic
        another.indexToLocFormat = self.indexToLocFormat
        another.glyphDataFormat = self.glyphDataFormat
        
        another.numGlyphs = self.numGlyphs
        
        
        another.char_defines = self.char_defines.copy()
        
        if self.char_kern != None :
            another.char_kern = [ (sc, field[:]) for sc, field in self.char_kern ]
        
        another.char_dup = self.char_dup[:]
        
        another.fix_entrys = self.fix_entrys.copy()
        another.stt_entrys = self.stt_entrys.copy()
        
        return another
        
    def rename( self, name=None, familyname=None, subfamilyname=None, postname=None,
                      version=None, identifier=None, copyright=None, trademark=None):
        
        if name == None and self.name == None :
                raise TTFError, 'name must present'
        
        name = name or self.name
        familyname = familyname or name
        subfamilyname = subfamilyname or familyname
        postname = postname or name.strip().replace(' ','')
        version = version or 'Version 1.00'
        identifier = identifier or ( name + ':' + version )
        copyright = copyright or 'Copyright (c) 2012, all rights reserved.'
        trademark = trademark or name
        
        self.name = name
        self.nametuple = ( copyright, familyname, subfamilyname, identifier,
                           name, version, postname, trademark,
                         )
        
        return
    
    @staticmethod
    def build_subchrs( subchrs ):
        
        if type(subchrs) == types.StringType :
            subchrs = unicode(subchrs)
            subchrs = set(subchrs)
        elif type(subchrs) in ( types.ListType, types.TupleType, set ) :
            if not all( ( type(c) in types.StringTypes and len(c) == 1 ) for c in subchrs ) :
                raise TTFError, 'err input for subchrs'
            subchrs = [ unicode(c) for c in subchrs ]
            subchrs = set(subchrs)
        elif type(subchrs) == types.UnicodeType :
            subchrs = set(subchrs)
        elif type(subchrs) == set :
            if all( ( type(c) == types.UnicodeType ) for c in subchrs ) :
                subchrs = subchrs.copy()
            elif all( ( type(c) in types.StringTypes and len(c) == 1 ) for c in subchrs ) :
                subchrs = set( unicode(c) for c in subchrs )
            else :
                raise TTFError, 'inp type error'
        else :
            raise TTFError, 'inp type error'        
        
        return subchrs
    
    def subset( self, subchrs, ignore=None ):
        
        subchrs = self.build_subchrs( subchrs )
        
        if ignore == None :
            #subchrs = [ c for c in subchrs if c not in '\r\n\t\b']
            subchrs = subchrs - set('\r\n\t\b')
            ignore = True
        
        subchrs = subchrs | set(unichr(0))
        
        if ignore == True :
            self.char_defines = dict( (c, self.char_defines[c]) for c in subchrs )
        else :
            cds = [ (c, self.char_defines.get(c, None)) for c in subchrs ]
            self.char_defines = dict( (k,v) for k, v in cds if v != None )
        
        if self.char_kern != None :
            charkern = [ 
                (sc, [ (l, r, v) for l, r, v in field if l in subchrs and r in subchrs ]) 
                for sc, field in self.char_kern
            ]
            charkern = [ (sc, field) for sc, field in charkern if len(field) != 0 ]
            self.char_kern = None if len(charkern) == 0 else charkern
            
        cdup = [ tuple( c for c in cs if c in subchrs ) for cs in self.char_dup ]
        cdup = [ cs for cs in cdup if len(cs) > 1 ]
        self.char_dup = cdup
        
        self.numGlyphs = len(self.char_defines)
        
        return
    
    def update( self, another, subchrs=None, covered=False ):
        
        if self.stt_entrys['head']['unitsPerEm'] != another.stt_entrys['head']['unitsPerEm'] :
            raise TTFError, 'unitsPerEm not match'
            
        #if self.stt_entrys['hhea']['ascender'] != another.stt_entrys['hhea']['ascender'] :
        #    raise TTFError, 'ascender not match'
            
        #if self.stt_entrys['hhea']['descender'] != another.stt_entrys['hhea']['descender'] :
        #    raise TTFError, 'descender not match'
        
        if type(subchrs) == UnicodeMapSet :
        
            subchrs = subchrs.by_intersection( set(another.char_defines.keys()) )
        
        else :
            
            if subchrs == None :
                subchrs = another.char_defines.keys()
        
            subchrs = self.build_subchrs( subchrs )
            subchrs = subchrs - set(unichr(0))
        
        if covered == True :
            rm_glyph = []
        else :
            rm_glyph = [ (c,self.char_defines.pop(c,None)) for c in subchrs ]
            rm_glyph = [ (c, g) for c, g in rm_glyph if g != None]
                
        rm_chars = zip(*rm_glyph)[0] if rm_glyph else []
        rm_chars = set(rm_chars)
        
        add_glyph = [ (c, another.char_defines.get(c, None) ) for c in subchrs ] 
        add_glyph = [ (c, g) for c, g in add_glyph if g != None ]
        
        add_chars = zip(*add_glyph)[0] if add_glyph else []
        add_chars = set(add_chars)
        
        if covered == True :
            #self.char_defines.update(dict(add_glyph))
            for c, g in add_glyph :
                self.char_defines[c] = g
        else :
            for c, g in add_glyph :
                self.char_defines.setdefault(c,g)
            
        self.numGlyphs = len(self.char_defines)
        
        this_kern = [ (sc, [ (l, r, v) for l, r, v in l not in rm_chars and r not in rm_chars ] ) 
                      for sc, field in self.char_kern ] if self.char_kern else []
        that_kern = [ (sc, [ (l, r, v) for l, r, v in l in add_chars and r in add_chars ] ) 
                      for sc, field in another.char_kern ] if another.char_kern else []
        
        charkern = this_kern + that_kern
        charkern = [ (sc, field) for sc, field in charkern if len(field) != 0 ]
        self.char_kern = None if len(charkern) == 0 else charkern
        
        this_dup = [ tuple( c for c in cs if c not in rm_chars ) for cs in self.char_dup ]
        this_dup = [ cs for cs in this_dup if len(cs) > 1 ]
        that_dup = [ tuple( c for c in cs if c in add_chars ) for cs in another.char_dup ]
        that_dup = [ cs for cs in that_dup if len(cs) > 1 ]
        self.char_dup = this_dup + that_dup
        
        return
        
    def showinfos( self ):
        
        print '       Name :', self.name
        print ' unitsPerEm :', self.stt_entrys['head']['unitsPerEm']
        print 'atalicAngle :', self.stt_entrys['post']['atalicAngle']['major'],\
                          '.', self.stt_entrys['post']['atalicAngle']['sub']
        print '  numGlyphs :', self.numGlyphs
        
        return


transmapdefault = '⋯…≪《≫》'.decode('utf-8')
transmapdefault = dict(zip(transmapdefault[::2],transmapdefault[1::2]))



if __name__ == '__main__' :
    
    import sys
    import getopt
    
    opts, args = getopt.gnu_getopt(
        sys.argv[1:],
        'o:s:S:c:gen:m:I:rx:X:t:y:lih',
        ['output=','extract',
         'info', 'cid=',
         'rename=',
         'subset=','subset-file=','decoding=','ignore',
         'map=','integrate=','replace',
         'text=','text-file=','text-code=','output-code=','translate=','use-symbol=','stripline',
         'help']
    )
    
    helpinfo = '''\
TTF tool. present by py-Al project. it written by python.


examples :

   ttf.py [-s subsetchrs] [-I integratefont] [-o output] <xxx.ttf|packagespath>
 or
   ttf.py [-T textfile] [-o outputfile] <xxx.ttf|packagespath>
 or 
   ttf.py <xxx.ttf|packagespath> --info

command arguments :

 common :
    --output      -o file  : output file or path
    --extract     -e       : extract the font file instead build a new ttf file
    
 for display font info :
    --info        -i       : show font file infomations
 
 for pdf embedded font :
    --cid                  : show font file infomations for pdf embedded
 
 for change font info :
    --rename      -n name  : rename the font file
 
 for subset :
    --subset      -s text  : set subset charactors
    --subset-file -S file  : set subset charactors from file
    --decoding    -c codec : set subset charactors or file coding
    --ignore      -g       : ignore if subset charactor not found
    
 for integrate :
    --map         -m block : set the integrate subset, using unicode block name
    --integrate   -I file  : integrate a font to your font
    --replace     -r       : integrate the charactor even it in your font
    
 for parse text file :
    --text        -x text  : text to parse
    --text-file   -X file  : read the text from file
    --text-code      codec : text codec
    --output-code    codec : output file's codec
    --translate   -t text  : translate map, odd is key, even is value
    --use-symbol  -y text  : replace the invisionable charactor
    --stripline   -l       : strip the invisionable charactor by line
    
 for help :
    --help        -h       : to show this help info.
'''
    
    optks = zip(opts)[0] if opts else []
    if 'help' in optks or 'h' in optks :
        print helpinfo
        sys.exit(0)

    if len(args) != 1 :
        print 'error: arguments wrong'
        print 
        print helpinfo
        sys.exit(-1)
    
    subset = ''
    output = None
    decoding = 'ascii'
    ignore = False
    extract = False
    rename = None
    intmaps = None
    intcover = False
    integrate = []
    
    info = False
    cid = None
    
    text = None
    textdecoding = 'ascii'
    outputcoding = 'utf-8'
    transmap = {}
    symbol = u''
    stripline = False
    
    for k, v in opts :
        
        k = k.strip('-')
        
        if k in ( 'output', 'o' ):
            output = v
        
        elif k in ( 'subset', 's' ):
            d = 'utf-8' if decoding == 'ascii' else decoding
            subset += v.decode(d)
        
        elif k in ( 'subset-file', 'S' ):
            
            with open( v ) as fp :
                d = decoding
                h = fp.read(2)
                if h == '\xff\xfe' :
                    d = 'utf-16'
                elif h == '\xfe\xff' :
                    d = 'utf-16BE'
                elif h == '\xef\xbb' :
                    d = 'utf-8'
                    fp.read(1)
                else :
                    fp.seek(0)
                subset += fp.read().decode(d)
        
        elif k in ( 'decoding', 'c' ):
            decoding = v
            
        elif k in ( 'ignore', 'g' ):
            ignore = True
        
        elif k in ( 'extract', 'e' ):
            extract = True
            
        elif k in ( 'rename', 'n' ):
            rename = v
            
        elif k in ( 'map', 'm' ):
            intmaps = unimap.getset(v.replace('_',' ').strip())
            
        elif k in ( 'integrate', 'I' ):
            integrate.append( (v,intmaps,intcover) )
            intmaps = None
            intcover = False
            
        elif k in ( 'replace', 'r' ):
            intcover = True
    
        elif k in ( 'text', 'x' ) :
            text = v
            
        elif k in ( 'text-file', 'X' ):
            text = open(v,'r')
            
        elif k in ( 'text-code', ):
            textdecoding = v
            
        elif k in ( 'output-code', ):
            outputcoding = v
            
        elif k in ( 'translate', 't' ):
            if v == 'auto' :
                transmap = transmapdefault
            elif v :
                d = 'utf-8' if textdecoding == 'ascii' else textdecoding
                v = v.decode(d)
                transmap = dict(zip(v[::2],v[1::2]))
        
        elif k in ( 'use-symbol', 'y' ):
            if v == 'auto' :
                symbol = u'\u2588'
            elif v :
                d = 'utf-8' if textdecoding == 'ascii' else textdecoding
                symbol = v.decode(d)
            
        elif k in ( 'stripline', 'l' ):
            stripline = True
    
        elif k in ( 'info', 'i' ):
            info = True
            
        elif k in ( 'cid', ):
            cid = v
    
    if type(text) == types.StringType :
        d = 'utf-8' if textdecoding == 'ascii' else textdecoding
        text = text.decode(d)
    elif type(text) == types.FileType :
        d = decoding
        fp = text
        h = fp.read(2)
        if h == '\xff\xfe' :
            d = 'utf-16'
        elif h == '\xfe\xff' :
            d = 'utf-16BE'
        else :
            fp.seek(0)
        text = fp.read().decode(d)
        fp.close()
    
    
    if text and (subset or integrate):
        print >> sys.stderr, 'can not both parse text and subset/integrate.'
    
    
    if cid :
        et = TTFile()
        et.load_CID( open(cid, 'r') )
        t = TTFile()
        t.load( args[0] )
        r, s = et.antidefines(t)
        for i, (chrs,snum) in enumerate(zip(r,s)) :
            #print i, ':', ' '.join( [ repr(iir)[1:-1] for iir in ir ] )
            print i, chrs, snum
            
        print '-'*20
        print et.fix_entrys['fpgm']
        print '-'*20
        print t.fix_entrys['fpgm']
    
    elif info :
    
        t = TTFile()
        t.load( args[0], noglyph=True )
        
        t.showinfos()
        
    elif text :
        
        t = TTFile()
        t.load( args[0], noglyph=True )
        
        inp_chars = set(text) - set(u'\r\n\t\b')
        lost_chars = inp_chars - set(t.char_defines.keys())
        strip_chars = lost_chars - set(transmap.keys())
        
        lost_map = dict( (c,symbol) for c in lost_chars )
        lost_map.update(transmap)
        
        text = text.splitlines()
        if stripline :
            text = [ l.strip(''.join(strip_chars)) for l in text ]
        text = [ ''.join( lost_map.get(c,c) for c in l ) for l in text ]
        
        text = '\r\n'.join(text)
        
        with open( output, 'w' ) as fp :
            fp.write( text.encode(outputcoding) )
        
    else :
    
        t = TTFile()
        t.load( args[0] )
        
        if integrate :
            gt = {}
            for ifn, imap, icover in integrate :
                it = gt.get(ifn,None)
                if not it :
                    it = TTFile()
                    it.load(ifn)
                    gt[ifn] = it
                #it = TTFile()
                #it.load(ifn)
                t.update( it, imap, icover )
        
        if subset != '' :
            t.subset( subset, ignore=ignore )
            
        if rename :
            t.rename( rename )
        
        elif output :
            
            if extract :
            
                if os.path.isdir(output) == False :
                    raise Exception, 'output arg error, it must be a path and exists.'
                    
                t.dump_packs( output )
                
            else :
                
                pth, f = os.path.split(output)
                
                if f == '' or os.path.isdir(pth or '.') == False :
                    raise Exception, 'output arg error, it must be a file, not a path, or using --extract.'
                
                t.dump_ttf( output )
            
    
    
