


import easyprotocol as ezp
import pprint


class TTFError(Exception):
    pass


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
        
        #print '-', namespace, args
        
        numberOfPoints = args
        repeat = 1 << 3
        zerocheck = ( 1 << 6 ) | ( 1 << 7 )
        
        r = []
        le = 0
        while( numberOfPoints > 0 ):
            
            flag = ord(fp.read(1))
            #if flag & zerocheck :
            #    raise Exception, ('zero check error', hex(flag))
            
            c = ord(fp.read(1)) if (flag & repeat) else 1
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
        
        
class TTFile(object):
    
    ebp = ezp.EasyBinaryProtocol()
    ebp.buildintypes.append(FLAGSType())
    ebp.buildintypes.append(COORDSType())
    #ebp.namespaces = dict( (bt.name, bt) for bt in ebp.buildintypes )
    ebp.rebuild_namespaces()
    ebp.parsefile( 'ttf.protocol' )
    
    def __init__( self, filename ):
        
        self.fp = open('../../../font/One Starry Night.ttf')
        #self.fp = open('../../../font/arial.ttf')
        self.directory = self.ebp.read('ttf', self.fp )['directory']
        self.make_entrys()
    
    idxsort = ['head','maxp','cmap','loca','glyf','hhea','hmtx']
    
    @classmethod
    def entry_index( cls, e ):
        try :
            return cls.idxsort.index(e['tag'])
        except :
            return 100
    
    def make_entrys( self ):
        
        entrys = list(self.directory['entry'])
        entrys.sort( key = lambda e : self.entry_index(e))
        self.entrys = {}
        
        for entry in entrys :
            
            ef = getattr( self, 'entry_'+entry['tag'].replace('/','_'), None )
            if ef :
                self.fp.seek(entry['offset'])
                self.entrys[entry['tag']] = ef(entry)
        
        return
        
    def entry_head( self, head ):
        le = (head['length'] + 3) & (0xFFFFFFFC)
        d = list(self.ebp.read('checksum', self.fp, length=le)['data'])
        d2, d[2] = d[2], 0
        if reduce( (lambda a,b: (a+b) & 0xFFFFFFFF ), d ) != head['checksum'] :
            raise Exception, head
        if 0xB1B0AFBA - head['checksum'] != d2 :
            raise Exception, ( head, d2 )
        
        self.fp.seek(head['offset'])
        return self.ebp.read('head', self.fp)
    
    def entry_post( self, post ):
        return self.ebp.read('post', self.fp)
    
    def entry_os_2( self, os_2 ):
        return self.ebp.read('os_2', self.fp)
    
    def entry_maxp( self, maxp ):
        le = (maxp['length'] + 3) & (0xFFFFFFFC)
        if reduce( (lambda a,b: (a+b) & 0xFFFFFFFF ), self.ebp.read('checksum', self.fp, length=le)['data'] ) != maxp['checksum'] :
            raise Exception, maxp
        
        self.fp.seek(maxp['offset'])
        return self.ebp.read('maxp', self.fp)
    
    def entry_loca( self, loca ):
        
        _loca = self.ebp.read('loca', self.fp, numGlyphs=self.entrys['maxp']['numGlyphs'], indexToLocFormat=self.entrys['head']['indexToLocFormat'])['loca']
        
        if 'loca_short' in _loca :
            _loca = tuple( l*2 for l in _loca['loca_short'] )
        else :
            _loca = _loca['loca_long']
            
        return _loca
        
    def entry_hhea( self, hhea ):
        if hhea['length'] != 36 :
            raise Exception, hhea
        if reduce( (lambda a,b: (a+b) & 0xFFFFFFFF ), self.ebp.read('checksum', self.fp, length=36)['data'] ) != hhea['checksum'] :
            raise Exception, hhea
        
        self.fp.seek(hhea['offset'])
        return self.ebp.read('hhea', self.fp)
    
    def entry_hmtx( self, hmtx ):
        return self.ebp.read('hmtx', self.fp, numGlyphs=self.entrys['maxp']['numGlyphs'], numberOfHMetrics=self.entrys['hhea']['numberOfHMetrics'])
    
    def entry_glyf( self, glyf ):
        
        _glyf = []
        
        for offset in self.entrys['loca'][:-1] :
            
            self.fp.seek(glyf['offset']+offset)
            g = self.ebp.read('glyf', self.fp)
            #print g['numberOfContours']
            g['glyphDescription'] = self.ebp.read( 'glyphDescription', self.fp, numberOfContours=g['numberOfContours'] )['glyphdesc']
            _glyf.append( g )
            
        return _glyf
    
    def entry_cmap( self, cmap ):
        
        _cmap = self.ebp.read('cmap', self.fp)['cmap']
        
        for cmapt in _cmap :
            
            self.fp.seek(cmap['offset']+cmapt['offset'])
            cmapt[''] = t = self.ebp.read('cmaptable', self.fp)
            
            if 'format6' in t['cmap'] :
                
                fm6 = t['cmap']['format6']
                cmapt['_index'] = dict((i+fm6['firstCode'],v) for i, v in enumerate(fm6['plyphIdArray']))
                    
                if len(fm6['plyphIdArray']) != fm6['entryCount'] :
                    raise TTFError, 'read error.'
                    
            elif 'format4' in t['cmap'] :
                
                fm4 = t['cmap']['format4']
                r = []
                
                for segc, s, e, delta, offset in zip( range(fm4['segCountX2']/2,0,-1), fm4['startCount'], fm4['endCount'], fm4['idDelta'], fm4['idRangeOffset']):
                    #print '>', s, e, delta, offset
                    rs = offset/2 - segc if offset != 0 else s
                    re = rs + e - s
                    vs = [ (v+delta)%65536 for v in fm4['plyphIdArray'][rs:re] ]
                    r.extend( zip(range(s,e),vs) )
                    
                cmapt['_index'] = dict( r )
                
        return _cmap
        
    def entry_name( self, name ):
        
        _name = self.ebp.read('name', self.fp, length=name['length'])
        
        for nm in _name['nameRecords'] :
            
            rs = nm['stringOffset']
            re = nm['stringOffset'] + nm['stringLength']
            nm['name'] = _name['data'][rs:re]
            
            if nm['encodingID'] == 1 and nm['platformID'] == 3 :
                nm['name'] = nm['name'].decode('utf-16BE')
                
        return _name
        
    
if __name__ == '__main__' :
    
    t = TTFile( 'ttf.protocol' )
    pprint.pprint( t.directory )
    pprint.pprint( t.entrys['loca'] )
    print len(t.entrys['loca'])

    # from fontTools import ttLib
    # x = ttLib.TTFont('/home/dainan/workspace/font/One Starry Night sub.ttf')


















