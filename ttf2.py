# -*- coding: utf-8 -*-


import easyprotocol as ezp
import cStringIO
import struct
import cPickle as pickle

import pprint


class TTFError(Exception):
    pass


def checksum( inp, le=None ):
    
    if le != None :
        return reduce( (lambda a,b: (a+b) & 0xFFFFFFFF ), TTF.ebp.read('checksum', inp, length=le)['data'] )
    
    if len(inp) % 4 != 0 :
        inp = inp + chr(0)*(4-(len(inp) % 4))
    return reduce( (lambda a,b: (a+b) & 0xFFFFFFFF ), TTF.ebp.read('checksum', cStringIO.StringIO(inp), length=len(inp))['data'] )

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
        raise TTFError, 'flags can\'t read .'
        
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
    
    def read( self, namespace, fp, lens, args ):
        raise TTFError, 'coords can\'t read .'
        
    def read_multi( self, namespace, fp, lens, mlens, args ):
        raise TTFError, 'coords can\'t read 1+.'
        

class TTF(object):
    
    ebp = ezp.EasyBinaryProtocol()
    ebp.buildintypes.append(FLAGSType())
    ebp.buildintypes.append(COORDSType())
    ebp.rebuild_namespaces()
    ebp.parsefile( 'ttf.protocol' )
    
    def __init__( self, filename ):
        
        self.filename = filename
        self.entrys = {}
        
    idxsort = ['head','maxp','cmap','loca','glyf','hhea','hmtx','post']
    idxsort = dict( (n,i) for i, n in enumerate(idxsort) )
    
    def extract( self, path ):
        
        path += '' if path.endswith('/') else '/'
        
        with open(filename) as fp :
            
            directory = self.ebp.read('ttf', self.fp )['directory']
            entrys = directory.pop('entry')
        
            entrys.sort( key = lambda e : self.idxsort.get(e['tag'],100) )
            
            for e in entrys :
                self.entrys[e['tag']] = read_entry( fp, e )

        with open( path + 'directory' ) as dirfp :
            dirfp.write( pickle.dumps(directory) )


        return
    
    def read_entry( self, fp, e ):
        
        fp.seek(entry['offset'])
        if e['tag'] != 'head' and e['checksum'] != checksum( fp.read( e['length'] ) ) :
            raise TTFError, 'checksum error in ' + e['tag']
        fp.seek(entry['offset'])
        extent = getattr( self, 'read_' + e['tag'].replace('/','_').strip(), self.extract_default )
        
        return extent( fp, e )
    
    def read_default( self, fp, e ):
        return fp.read( e['length'] )
        
    def read_head( self, fp, e ):
        head = self.ebp.read('head', fp)
        return head
        
    def read_maxp( self, fp, e ):
        maxp = self.ebp.read('maxp', fp)
        return maxp
        
    def read_kern( self, fp, e ):
        kern = self.ebp.read('kern', fp)
        return kern['subTables']
        
    def read_cmap( self, fp, e ):
        
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
        
        return dict(r)
    
    def read_hhea( self, fp, e ):
        hhea = self.ebp.read('hhea', fp)
        return hhea
    
    def read_hmtx( self, fp, e ):
        
        numGlyphs = self.entrys['maxp']['numGlyphs']
        numberOfHMetrics = self.entrys['hhea']['numberOfHMetrics']
        
        r = self.ebp.read( 'hmtx', fp, 
                            numGlyphs=numGlyphs, 
                            numberOfHMetrics=numberOfHMetrics )
                            
        hmtxmetrix = [ ( hm['advanceWidth'], hm['leftSideBearing'] ) for hm in r['hMetrics'] ] + \
                     [ ( r['hMetrics'][-1]['advanceWidth'], nhlsb ) for nhlsb in r['nonHorizontalLeftSideBearing']]
                         
        return hmtxmetrix
    
    def entry_loca( self, fp, e ):
        
        numGlyphs = self.entrys['maxp']['numGlyphs']
        indexToLocFormat = self.entrys['head']['indexToLocFormat']
        
        _loca = self.ebp.read( 'loca', fp,
                               numGlyphs = numGlyphs, 
                               indexToLocFormat = indexToLocFormat )
        _loca = _loca['loca']
        
        if 'loca_short' in _loca :
            return tuple( l*2 for l in _loca['loca_short'] )
        
        return _loca['loca_long']
        
    def read_glyf( self, fp, e ):

        g = []
        
        for offset, end in zip(self.entrys['loca'][:-1],self.entrys['loca'][1:]) :
            le = end - offset
            fp.seek( e['offset'] + offset )
            g.append( fp.read(le) )

        return g
        
    def read_post( self, fp, e ):
        
        numGlyphs = self.entrys['maxp']['numGlyphs']

        r = self.ebp.read( 'post', fp, 
                           numGlyphs = numGlyphs, length=e['length'] )
                           
        glyphNames = r.pop('glyphNames')
            
        return r
    
class TTFMaker(object):
    pass
    
    
    