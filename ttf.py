


import easyprotocol as ezp
import pprint
import cStringIO
import struct

class TTFError(Exception):
    pass


def string_checksum( inp ):
    if len(inp) % 4 != 0 :
        inp = inp + chr(0)*(4-(len(inp) % 4))
    return reduce( (lambda a,b: (a+b) & 0xFFFFFFFF ), TTFile.ebp.read('checksum', cStringIO.StringIO(inp), length=len(inp))['data'] )

def searchrange( inp ):
    a = 1
    b = 1
    while( a < inp ):
        a = a*2
        b += 1
    return a, b

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
        
        
class TTFile(object):
    
    ebp = ezp.EasyBinaryProtocol()
    ebp.buildintypes.append(FLAGSType())
    ebp.buildintypes.append(COORDSType())
    #ebp.namespaces = dict( (bt.name, bt) for bt in ebp.buildintypes )
    ebp.rebuild_namespaces()
    ebp.parsefile( 'ttf.protocol' )
    
    def __init__( self, filename ):
        
        self.fp = open(filename)
        self.directory = self.ebp.read('ttf', self.fp )['directory']
        self.dirs = dict([ (e['tag'], e) for e in self.directory['entry'] ])
        self.make_entrys()
    
    idxsort = ['head','maxp','cmap','loca','glyf','hhea','hmtx','post']
    
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
        
        self.fp.seek(0)
        le = 12 + 16*len(self.directory['entry'])
        le = (le+3) & (0xFFFFFFFC)
        chks = self.ebp.read('checksum', self.fp, length=le )['data']
        chks = reduce( (lambda a,b: (a+b) & 0xFFFFFFFF ), chks )
        chks = reduce( (lambda a,b: (a+b) & 0xFFFFFFFF ), [ e['checksum'] for e in self.directory['entry'] ], chks )
        if 0xB1B0AFBA - chks != d2 :
            raise Exception, ( head, d2 )
        
        self.fp.seek(head['offset'])
        return self.ebp.read('head', self.fp)
    
    def entry_post( self, post ):
        #if post['length'] != 32 :
        #    raise Exception, post
        #if reduce( (lambda a,b: (a+b) & 0xFFFFFFFF ), self.ebp.read('checksum', self.fp, length=32)['data'] ) != post['checksum'] :
        #    raise Exception, post
            
        self.fp.seek(post['offset'])
        return self.ebp.read('post', self.fp, numGlyphs=self.entrys['maxp']['numGlyphs'], length=post['length'])
    
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
        _g = []
        
        for offset, end in zip(self.entrys['loca'][:-1],self.entrys['loca'][1:]) :
            
            le = end - offset
            if le % 4 != 0 :
                raise Exception, 'glyf 1ength error'
            if le == 0 :
                _glyf.append( {} )
                _g.append( {'checksum':0, 'length':0, 'data':''} )
                continue
            
            self.fp.seek(glyf['offset']+offset)
            chks = reduce( (lambda a,b: (a+b) & 0xFFFFFFFF ), self.ebp.read('checksum', self.fp, length=le)['data'] )
            
            self.fp.seek(glyf['offset']+offset)
            g = self.ebp.read('glyf', self.fp)
            #print g['numberOfContours']
            g['glyphDescription'] = self.ebp.read( 'glyphDescription', self.fp, numberOfContours=g['numberOfContours'] )['glyphdesc']
            _glyf.append( g )
            
            self.fp.seek( glyf['offset'] + offset )
            _g.append(
                { 'checksum' : chks,
                  'length' : le,
                  'data' : self.fp.read(le),
                }
            )
            
        self.glyf_raw = _g
        
        return _glyf
    
    def entry_cmap( self, cmap ):
        
        _cmap = self.ebp.read('cmap', self.fp)
        _idx = _cmap['_index'] = {}
        
        for cmapt in _cmap['cmap'] :
            
            self.fp.seek(cmap['offset']+cmapt['offset'])
            cmapt[''] = t = self.ebp.read('cmaptable', self.fp)
            
            if 'format6' in t['cmap'] :
                
                fm6 = t['cmap']['format6']
                _idx[(cmapt['platformID'],cmapt['encodingID'])] = dict((i+fm6['firstCode'],v) for i, v in enumerate(fm6['plyphIdArray']))
                    
                if len(fm6['plyphIdArray']) != fm6['entryCount'] :
                    raise TTFError, 'read error.'
                    
            elif 'format4' in t['cmap'] :
                
                fm4 = t['cmap']['format4']
                r = []
                
                for segc, s, e, delta, offset in zip( range(fm4['segCountX2']/2,0,-1), fm4['startCount'], fm4['endCount'], fm4['idDelta'], fm4['idRangeOffset']):
                    #print '>', s, e, delta, offset
                    if offset != 0 :
                        rs = offset/2 - segc
                        re = rs + e - s
                        vs = [ (v+delta)%65536 for v in fm4['plyphIdArray'][rs:re+1] ]
                        r.extend( zip(range(s,e+1),vs) )
                    else :
                        r.extend( [ (k, (k+delta)%65536) for k in range(s,e+1) ] )
                    
                _idx[(cmapt['platformID'],cmapt['encodingID'])] = dict( r )
        
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
        
    def make_subset( self, fname, subset ):
        
        subset = list(unicode(subset))
        subset = [ ord(char) for char in subset ]
        subset.sort()
        
        cmapidx = self.entrys['cmap']['_index'][(0,3)]
        cmapidx = [ cmapidx[char] for char in subset ]
        cmapidx = [0] + cmapidx

        charidx = dict([ (char, i+1) for i,char in enumerate(subset) ])

        numGlyphs = len(cmapidx)
        
        glyf = [ self.glyf_raw[c] for c in cmapidx ]
        glyflen = [ g['length'] for g in glyf ]
        glyf = {
            'data' : ''.join( g['data'] for g in glyf ),
            'length' : sum( g['length'] for g in glyf ),
            'checksum' : ( sum( g['checksum'] for g in glyf ) & 0xFFFFFFFF ),
            'tag' : 'glyf',
        }
        
        loca = [ sum(glyflen[:i+1]) for i in range(len(cmapidx)) ]
        loca = [0] + loca
        loca = [ loc/2 for loc in loca ]
        loca = [ chr(loc/256) + chr(loc%256) for loc in loca ]
        loca = ''.join(loca)
        loca = {
            'data' : loca,
            'length' : len(loca),
            'checksum' : string_checksum(loca),
            'tag' : 'loca',
        }
        
        
        _maxp = self.entrys['maxp']
        maxp = struct.pack( '>'+'H'*16,
            _maxp['version']['major'], _maxp['version']['sub'],
            numGlyphs,
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
        maxp = {
            'data' : maxp,
            'length' : len(maxp),
            'checksum' : string_checksum(maxp),
            'tag' : 'maxp',
        }
        
        _hhea = self.entrys['hhea']
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
            _hhea['reversed1'],
            _hhea['reversed2'],
            _hhea['reversed3'],
            _hhea['reversed4'],
            _hhea['reversed5'],
            _hhea['metricDataFormat'],
            numGlyphs, #_hhea['numberOfHMetrics'],
        )
        hhea = {
            'data' : hhea,
            'length' : len(hhea),
            'checksum' : string_checksum(hhea),
            'tag' : 'hhea',
        }
        
        hmtx = ''.join( struct.pack('>Hh', v['advanceWidth'], v['leftSideBearing'] ) for v in self.entrys['hmtx']['hMetrics'] )
        hmtx = {
            'data' : hmtx,
            'length' : len(hmtx),
            'checksum' : string_checksum(hmtx),
            'tag' : 'hmtx',
        }
        
        self.fp.seek( self.dirs['OS/2']['offset'] )
        os_2 = {
            'data' : self.fp.read( self.dirs['OS/2']['length'] ),
            'length' : self.dirs['OS/2']['length'],
            'checksum' : self.dirs['OS/2']['checksum'],
            'tag' : 'OS/2',
        }
        
        self.fp.seek( self.dirs['name']['offset'] )
        name = {
            'data' : self.fp.read( self.dirs['name']['length'] ),
            'length' : self.dirs['name']['length'],
            'checksum' : self.dirs['name']['checksum'],
            'tag' : 'name',
        }
        
        format6 = [ ord(chr(c+0x20).decode('mac_roman')) for c in range(0,224) ]
        format6 = [ charidx.get(c+0x20,0) for c in format6 ]
        format6 = [ chr(c/256) + chr(c%256) for c in format6 ]
        format6 = ''.join(format6)
        format6 = struct.pack('>HH',0x20,224)+format6
        
        f6len = len(format6)+6
        format6 = struct.pack('>HHH',6,f6len,0) + format6
        
        format4 = [(None,None)]
        for c in subset :
            if format4[-1][0] == None :
                format4[-1] = (c,c)
                continue
            if format4[-1][1] == c-1 :
                format4[-1] = (format4[-1][0],c)
                continue
            format4.append((None,None))
        
        if format4[-1][0] == None :
            format4[-1] = (65535,65535)
        elif format4[-1][1] == None :
            format4[-1] = (format4[-1][0],format4[-1][0])
            format4.append((65535,65535))
        else :
            format4.append((65535,65535))
            
        format4 = [ (st,en,(charidx.get(st,0)-st+65536)%65536) for st, en in format4 ]
        format4st = ''.join([ chr(st/256) + chr(st%256) for st in zip(*format4)[0] ])
        format4en = ''.join([ chr(en/256) + chr(en%256) for en in zip(*format4)[1] ])
        format4dt = ''.join([ chr(dt/256) + chr(dt%256) for dt in zip(*format4)[2] ])
        f4len = len(format4)
        f4sch, f4sel = searchrange(f4len)
        format4 = struct.pack('>HHHH',
            f4len*2,
            f4sch,
            f4sel,
            f4len*2 - f4sch,
        ) + format4en + chr(0) + chr(0) + format4st + format4dt + chr(0)*(f4len*2)
        
        f4len = len(format4)+6
        format4 = struct.pack('>HHH',4,f4len,0) + format4
        
        cmap = struct.pack('>HHHHIHHIHHI',
            0, 3,
            0, 3, 28,
            3, 1, 28,
            1, 0, f4len+28,
        )
        
        cmap = cmap + format4 + format6
        cmap = cmap + chr(0) * (( 4 - len(cmap) % 4 ) % 4)
        cmap = {
            'data' : cmap,
            'length' : len(cmap),
            'checksum' : string_checksum(cmap),
            'tag' : 'cmap',
        }
        
        _post = self.entrys['post']
        post = struct.pack('>HHHHhhIIIII',
            3, 0,
            _post['atalicAngle']['major'], _post['atalicAngle']['sub'],
            _post['underlinePosition'],
            _post['underlineThickness'],
            _post['isFixedPitch'],
            _post['minMemType42'],
            _post['maxMemType42'],
            _post['minMemType1'],
            _post['maxMemType1'],
        )
        post = {
            'data' : post,
            'length' : len(post),
            'checksum' : string_checksum(post),
            'tag' : 'post',
        }
        
        _head = self.entrys['head']
        head = struct.pack('>HHHHIIHH8s8shhhhHHhhhH',
            _head['version']['major'], _head['version']['sub'],
            _head['reversion']['major'],_head['reversion']['sub'],
            0,
            _head['magicNumber'],
            _head['flags'],
            _head['unitsPerEm'],
            ''.join( chr(c) for c in _head['created']),
            ''.join( chr(c) for c in _head['modified']),
            _head['xMin'],
            _head['yMin'],
            _head['xMax'],
            _head['yMax'],
            _head['macStyle'],
            _head['lowestRecPPEM'],
            _head['fontDirectionHint'],
            0, #_head['indexToLocFormat'],
            _head['glyphDataFromat'],
            0,
        )
        head = {
            'data' : head,
            'length' : len(head),
            'checksum' : string_checksum(head),
            'tag' : 'head',
        }
        
        
        allentry = [cmap,glyf,head,hhea,hmtx,loca,maxp,name,post,os_2]
        offset = 12+len(allentry)*16
        for e in allentry :
            e['offset'] = offset
            e['entrydata'] = struct.pack('>4sIII',
                e['tag'],
                e['checksum'],
                e['offset'],
                e['length'],
            )
            pad = e['length'] % 4
            pad = ( 4 - pad ) if pad!=0 else 0
            e['pad'] = pad
            offset += ( e['length'] + pad )
        
        dirsch, dirsel = searchrange(10)
        dirs = struct.pack('>HHHHHH',
            self.directory['sfntversion']['major'], self.directory['sfntversion']['sub'],
            10,
            dirsch*8,
            dirsel/2,
            10*16 - dirsch*8,
        ) + ''.join( e['entrydata'] for e in allentry )
            
        dirs = {
            'data' : dirs,
            'length' : len(dirs),
            'checksum' : string_checksum(dirs),
        }
        
        allchecksum = sum([ e['checksum'] for e in allentry ], dirs['checksum'])
        allchecksum = allchecksum & 0xFFFFFFFF
        
        head = struct.pack('>HHHHIIHH8s8shhhhHHhhhH',
            _head['version']['major'], _head['version']['sub'],
            _head['reversion']['major'],_head['reversion']['sub'],
            0xB1B0AFBA - allchecksum,
            _head['magicNumber'],
            _head['flags'],
            _head['unitsPerEm'],
            ''.join( chr(c) for c in _head['created']),
            ''.join( chr(c) for c in _head['modified']),
            _head['xMin'],
            _head['yMin'],
            _head['xMax'],
            _head['yMax'],
            _head['macStyle'],
            _head['lowestRecPPEM'],
            _head['fontDirectionHint'],
            _head['indexToLocFormat'],
            _head['glyphDataFromat'],
            0,
        )
        head = {
            'data' : head,
            'length' : len(head),
            'checksum' : string_checksum(head),
            'tag' : 'head',
        }
        
        fp = open(fname,'wb')
        fp.write(dirs['data'])
        for e in allentry :
            fp.write(e['data'])
            fp.write(chr(0)*e['pad'])
        fp.close()
    
if __name__ == '__main__' :
    
    t = TTFile( '../../../font/One Starry Night sub.ttf' )
    #t = TTFile( '../../../font/simhei.ttf' )
    #pprint.pprint( t.directory )
    #pprint.pprint( t.entrys )
    #print len(t.entrys['loca'])
    #print t.entrys['post']
    
    t.make_subset('osnsub.ttf','abcd')

    # from fontTools import ttLib
    # x = ttLib.TTFont('/home/dainan/workspace/font/One Starry Night sub.ttf')


















