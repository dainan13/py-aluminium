


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
        
        numberOfPoints = args
        repeat = 1 << 3
        
        r = []
        le = 0
        while( numberOfPoints >= 0 ):
            flag = ord(fp.read(1))
            c = ord(fp.read(1)) if (flag & repeat) else 1
            le += ( 2 if (flag&repeat) else 1 )
            r.extends([flag]*c)
            
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
    
    def readshort( self, fp ):
        return ( ord(fp.read(1)) << 8 ) + fp.read(1)
    
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
                last = ( last + ord(fp.read(1)) ) if flag & positive else ( last - ord(fp.read(1)) )
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
        
        self.fp = open('../../../font/One Starry Night sub.ttf')
        self.directory = self.ebp.read('ttf', self.fp )['directory']
        pprint.pprint( self.directory['entry'] )
        
        #self.entrys = dict( for entry in self.directory )
        cmap = dict( ( entry['tag'], entry ) for entry in self.directory['entry'] )['cmap']
        self.fp.seek(cmap['offset'])
        self.entrys = { 'cmap': self.ebp.read('cmap', self.fp)['cmap'] }
        for cmapt in self.entrys['cmap'] :
            self.fp.seek(cmap['offset']+cmapt['offset'])
            cmapt[''] = t = self.ebp.read('cmaptable', self.fp, div=(lambda a, b : a/b) )
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
                
        name = dict( ( entry['tag'], entry ) for entry in self.directory['entry'] )['name']
        self.fp.seek(name['offset'])
        self.entrys['name'] = self.ebp.read('name', self.fp, length=name['length'], sub=(lambda a, b : a-b))
        for nm in self.entrys['name']['nameRecords'] :
            rs = nm['stringOffset']
            re = nm['stringOffset'] + nm['stringLength']
            nm['name'] = self.entrys['name']['data'][rs:re]
            if nm['encodingID'] == 1 and nm['platformID'] == 3 :
                nm['name'] = nm['name'].decode('utf-16BE')
            
    
    def make_entry( self, entry ):
        
        if entry['tag'] in (''):
            self.fp.seek(entry['offset'])
            
        return
        
    
if __name__ == '__main__' :
    
    t = TTFile( 'ttf.protocol' )
    pprint.pprint( t.directory )
    pprint.pprint( t.entrys )




















