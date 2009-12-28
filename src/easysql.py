
import types
import threading

import MySQLdb

'''
CR = MySQLdb.constants.CR
CR = dict( [ ( getattr(CR, e), e )
             for e in vars(CR)
             if not e.startswith('__')
           ]
         )
'''

class This( object ):
    
    def __init__( self, colname ):
        
        self.str = '`'+colname+'`'
        
    def __add__ ( self, another ):
        
        self.str = '(' + self.str + '+' + \
        ( another._tosql if hasattr( another, '_tosql' ) else str(another) ) + \
        ')'
        
        return self
    
    def __sub__( self, another ):
        
        self.str = '(' + self.str + '-' + \
        ( another._tosql if hasattr( another, '_tosql' ) else str(another) ) + \
        ')'
        
        return self
    
    def __mul__( self, another ) :
        
        self.str = '(' + self.str + '*' + \
        ( another._tosql if hasattr( another, '_tosql' ) else str(another) ) + \
        ')'
        
        return self
    
    def __div__( self, another ) :
        
        self.str = '(' + self.str + '/' + \
        ( another._tosql if hasattr( another, '_tosql' ) else str(another) ) + \
        ')'
        
        return self
    
    def _tosql( self ):
        
        return self.str

def this( colname ):
    return This( colname )
    
    
    
    
class Default( object ):
    
    def __init__( self ):
        pass
        
    def _tosql( self ):
        return 'DEFAULT'
    
def default( ):
    return Default()
    
    
    
class Null( object ):
    
    def __init__( self ):
        pass
        
    def _tosql( self ):
        return 'NULL'
    
def null( ):
    return Null()
    
    
    
    
    
    
class NoArg( object ):
    pass
    
    
    
    
class EasySqlException( Exception ):
    """
    Default WorkFlow Exception
    """
    pass

class DuplicateError(EasySqlException):
    pass

class PrimaryKeyError(EasySqlException):
    pass

class NotFoundError(EasySqlException):
    pass

class TypeError(EasySqlException, TypeError ):
    pass




class Tablet( object ) :
    '''
    tablet of table
    '''
    
    def __init__ ( self, name, cols=[] ):
        
        self.name = name
        
        self.cols = ['a','b','c','d','e']
        
        pass
        
    def _insert( self, rows, dup = None, ignore = True ):
        '''
        INSERT [LOW_PRIORITY | DELAYED | HIGH_PRIORITY] [IGNORE]
            [INTO] tbl_name [(col_name,...)]
            {VALUES | VALUE} ({expr | DEFAULT},...),(...),...
            [ ON DUPLICATE KEY UPDATE
              col_name=expr
                [, col_name=expr] ... ]
        '''
        
        cols = set( sum( [ r.keys() for r in rows ] , [] ) )
        
        rows = [ [ r.get( c, 'DEFAULT' ) for c in cols ]
                 for r in rows ]
        
        sql = ' '.join( [
            
            'INSERT',
            # LOW_PRIORITY or DELAYED or ''
            'IGNORE' if ignore else '',
            'INTO',
            '`'+self.name+'`',
            '(%s)' % ( ','.join( [ '`%s`' % (c,) for c in cols ] ) ),
            'VALUES',
            ','.join( [ '(%s)' % ( ','.join(r), ) for r in rows ] ),
            ('ON DUPLICATE KEY UPDATE %s' %
                ( ','.join( [ '`%s`=%s' % i for i in dup.items() ] ), )
            ) if dup else '',
        ] )
        
        print sql
        
        return 1, 1
    
    def _select( self,
                 cond=None, cols=None, limit=None, offset=None, vset=None ):
        '''
        SELECT
            [ALL | DISTINCT | DISTINCTROW ]
              [HIGH_PRIORITY]
              [STRAIGHT_JOIN]
              [SQL_SMALL_RESULT] [SQL_BIG_RESULT] [SQL_BUFFER_RESULT]
              [SQL_CACHE | SQL_NO_CACHE] [SQL_CALC_FOUND_ROWS]
            select_expr [, select_expr ...]
            [FROM table_references
            [WHERE where_condition]
            [GROUP BY {col_name | expr | position}
              [ASC | DESC], ... [WITH ROLLUP]]
            [HAVING where_condition]
            [ORDER BY {col_name | expr | position}
              [ASC | DESC], ...]
            [LIMIT {[offset,] row_count | row_count OFFSET offset}]
            [PROCEDURE procedure_name(argument_list)]
            [INTO OUTFILE 'file_name'
                [CHARACTER SET charset_name]
                export_options
              | INTO DUMPFILE 'file_name'
              | INTO var_name [, var_name]]
            [FOR UPDATE | LOCK IN SHARE MODE]]
        '''
        
        cols = cols or self.cols
        
        
        sql = ' '.join( [
            
            'SELECT',
            'DISTINCT' if vset else '',
            ','.join([ '`%s`' % (c,) for c in cols ]),
            'FROM `%s`' % self.name ,
            ('WHERE %s' % ( ','.join( [ '`%s`=%s' % i
                                        for i in cond.items() ] ), )
            ) if cond else '',
            ('LIMIT %d' % (limit,) ) if limit else '',
            ('OFFSET %d' % (offset,) ) if limit and offset else '',
            
        ] )
        
        print sql
        
        return 1, [{'a':1,'b':2,'c':3,'d':4,'e':5}]
        
    def _delete( self, cond=None, limit=None, ignore = True ):
        '''
        DELETE [LOW_PRIORITY] [QUICK] [IGNORE] FROM tbl_name
            [WHERE where_condition]
            [ORDER BY ...]
            [LIMIT row_count]
        '''
        
        sql = ' '.join( [
            
            'UPDATE',
            'IGNORE' if ignore else '',
            'FROM `%s`' % self.name ,
            ('WHERE %s' % ( ','.join( [ '`%s`=%s' % i
                                        for i in cond.items() ] ), )
            ) if cond else '',
            ('LIMIT %d' % (limit,) ) if limit else '',
            
        ] )
        
        print sql
        
        return 1, None
        
    def _replace( self, rows ):
        '''
        REPLACE [LOW_PRIORITY | DELAYED]
            [INTO] tbl_name [(col_name,...)]
            {VALUES | VALUE} ({expr | DEFAULT},...),(...),...
        '''
        
        cols = set( sum( [ r.keys() for r in rows ] , [] ) )
        
        rows = [ [ r.get( c, 'DEFAULT' ) for c in cols ]
                 for r in rows ]
        
        sql = ' '.join( [
            
            'REPLACE',
            # LOW_PRIORITY or DELAYED or ''
            'INTO',
            '`'+self.name+'`',
            '(%s)' % ( ','.join( [ '`%s`' % (c,) for c in cols ] ) ),
            'VALUES',
            ','.join( [ '(%s)' % ( ','.join(r), ) for r in rows ] ),
            
        ] )
        
        print sql
        
        return 1, 1
        
    def _update( self, row, cond=None, limit=None, ignore = True ):
        '''
        UPDATE [LOW_PRIORITY] [IGNORE] table_reference
            SET col_name1={expr1|DEFAULT} [, col_name2={expr2|DEFAULT}] ...
            [WHERE where_condition]
            [ORDER BY ...]
            [LIMIT row_count]
        '''
        
        sql = ' '.join( [
            
            'UPDATE',
            'IGNORE' if ignore else '',
            '`%s`' % self.name ,
            'SET %s' % ( ','.join( [ '`%s`=%s' % i
                                        for i in row.items() ] ) ),
            ('WHERE %s' % ( ','.join( [ '`%s`=%s' % i
                                        for i in cond.items() ] ), )
            ) if cond else '',
            ('LIMIT %d' % (limit,) ) if limit else '',
            
        ] )
        
        print sql
        
        return 1, None


class Table ( object ) :
    '''
    table class of easysql
    '''
    
    @staticmethod
    def getresult( conn ):
        
        rst = conn.store_result()
        
        return rst.fetch_row( rst.num_rows() )
        
    
    def __init__ ( self, name, cols = [] ):
        
        self.name = name
        
        self.cols = cols
        
        self.colconv = []
        
        self.tablets = [ Tablet('testtable') ]
        
        return
        
    def _splitter( self, row ):
        
        return [0,]
        
    def _buildrow( self, row ):
        
        return dict( [ ( k, v._tosql() if hasattr(v, '_tosql')
                            else "'"+str(v)+"'"
                       ) for k, v in row.items() ] )
    
    def _gettablets( self, tbl ):
        
        return self.tablets[0]
        
    def _write( self, rows, ondup = None ):
        
        rows = [ self._buildrow(row) for row in rows ]
        
        tbls = [ self._splitter(row) for row in rows ]
        tblc = [ r for r, t in zip(rows, tbls) if len(t) != 1 ]
        if tblc != [] :
            raise PrimaryKeyError, \
                           ( 'Can not find the tablet on write', tblc )
        tbls = [ t[0] for t in tbls ]
        
        tblrows = [ ( tbl, [ r for r, t in zip(rows,tbls) if t == tbl ] )
                    for tbl in set(tbls) ]
        
        rsts = [ self._gettablets(tbl)._insert( rows, ondup )
                 for tbl, rows in tblrows ]
        
        n, lastids = zip(*rsts)
        n = sum(n)
        
        return n, lastids
    
    def _replace( self, rows ):
        
        rows = [ self._buildrow(row) for row in rows ]
        tbls = [ self._splitter(row) for row in rows ]
        if tblc != [] :
            raise PrimaryKeyError, \
                           ( 'Can not find the tablet on replace', tblc )
        tbls = [ t[0] for t in tbls ]
        
        tblrows = [ ( tbl, [ r for r, t in zip(rows,tbls) if t == tbl ] )
                    for tbl in set(tbls) ]
        
        rsts = [ self._gettablets(tbl)._replace( rows )
                 for tbl, rows in tblrows ]
        
        n, lastids = zip(*rsts)
        n = sum(n)
        
        return n, lastids

    
    def _read( self, cond, cols = None, limit = None, offset = None ):
        
        cond = self._buildrow(cond) if cond else cond
        tbls = self._splitter(cond) # todo : set to all tablets if cond is none
        
        tlimit = limit
        rst = []
        nx = 0
        for tbl in tbls : # read lazy
            n, r = self._gettablets(tbl)._select( cond, cols, tlimit )
            nx += n
            rst = rst + r
            tlimit = ( tlimit - n ) if tlimit != None else tlimit
            if tlimit <= 0 :
                break
        
        return nx, rst
        
    def _set( self, row, cond, limit = None ):
        
        cond = self._buildrow(cond) if cond else cond
        tbls = self._splitter(cond) # todo : set to all tablets if cond is none
        
        row = self._buildrow(row)
        
        tlimit = limit
        nx = 0
        for tbl in tbls :
            n, r = self._gettablets(tbl)._update( row, cond, tlimit )
            nx += n
            tlimit = ( tlimit - n ) if tlimit != None else tlimit
            if tlimit <= 0 :
                break
        
        return nx, None
    
    def _delete( self, cond, limit = None ):
        
        cond = self._buildrow(cond) if cond else cond
        tbls = self._splitter(cond) # todo : set to all tablets if cond is none
        
        tlimit = limit
        rst = []
        nx = 0
        for tbl in tbls : # read lazy
            n, r = self._gettablets(tbl)._delete( cond, tlimit )
            nx += n
            rst = rst + r
            tlimit = ( tlimit - n ) if tlimit != None else tlimit
            if tlimit <= 0 :
                break
        
        return nx, None
        
    def __lshift__ ( self, row ):
        '''
        table << {'attr':'inserted'}
        '''
        
        n, lastid = self._write( [row,] )
        
        if n == 0:
            raise DuplicateError, ''
        
        return self
    
    def append( self, row, ondup=None ):
        '''
        lastid = table.append( {'attr':'inserted'} )
        
        lastid = table.append( {'attr':'inserted'},
                                     ondup = {'attr':'updated'} )
                                     
        return None or lastid
        '''
        
        n, lastid = self._write( [row,], ondup )
        
        if n == 1 :
            return None
        else :
            return lastid[0]
            
    def extend( self, rows ):
        '''
        lastid = table.expend( [{'attr':'inserted'},] )
        
        return successed number
        '''
        
        n, lastid = self._write( rows )
        
        return n
        
    def get( self, cond, default=NoArg, keys=[] ):
        '''
        table.get({'ID':1}, default=None, keys=[] )
        '''
        
        n, rst = self._read( cond, cols=keys, limit=1)
        
        if n != 1 and default != NoArg :
            return default
        
        if n != 1 :
            raise NotFoundError, 'not found'
        
        return rst[0]
    
    def __rshift__ ( self, cond ):
        '''
        a = {'ID':1} ; table >> a
        '''
        
        n, rst = self._read( cond, limit = 1 )
        
        if n != 1 :
            raise NotFoundError, 'not found'
        
        cond.update(rst[0])
        
        return rst[0]
        
    def gets( self, cond, keys = [] ):
        '''
        table.gets({'ID':1}, keys=[], limited=())
        '''
        
        n, rst = self._read( cond, cols=keys, limit=1)
        
        return rst

    def __getitem__( self, sls ):
        '''
        table[{'ID':1}]
        table['a','b']
        table['a','b',{'ID':1}]
        table[10:50]
        talbe[::{'ID':1}]]
        table['a','b',0:50:{'ID':10}]
        table['a','b',{'ID':1}:50:{'ID':10}]
        
        table[('a','b'),::{'ID':10}]
        '''
        
        if type(sls) in ( types.StringType, types.UnicodeType ):
            sls = (sls,)
        
        if type(sls) == types.DictType :
            keys = None
            cond = sls
            limit = 1
            offset = None
            single = True
        
        if type(sls) == types.TupleType :
            
            if type(sls[-1]) == types.SliceType :
                keys = sls[:-1]
                cond = sls[-1].step
                limit = sls[-1].stop
                offset = sls[-1].start
                single = False
            elif type(sls[-1]) == types.DictType :
                keys = sls[:-1]
                cond = sls[-1]
                limit = 1
                offset = None
                single = True
            else :
                keys = sls
                cond = None
                limit = None
                offset = None
                single = True
                
        if type(sls) == types.SliceType :
            keys = None
            cond = sls.step
            limit = sls.stop
            offset = sls.start
            single = False
            
        offset = None if offset == 1 else offset
        
        if keys :
            
            keys = [ x if type(x) in ( types.TupleType, types.ListType )
                       else [x,]
                     for x in keys ]
            keys = sum(keys,[])
        
            if not all( [ type(k) == types.StringType for k in keys ] ):
                raise TypeError, \
                          ( 'easysql indices(get) must be as '\
                            '[[col, col, ... ,][offset:limit:]where]', sls )
        
        n, rst = self._read( cond, keys, limit, offset )
        
        if single == False :
            return rst
            
        if n != 1 :
            raise NotFoundError, 'not found'
        
        return rst[0]
        
        
    def __setitem__( self, sls, value ):
        '''
        table[{'ID':1}] = {'A':1}
        table[10:50] = {'A':1}
        talbe[::{'ID':1}]] = {'A':1}
        table['ID'] = {'ID':1, 'A':1}
        table['a','b',:50] = {'a':1,'b':2,'ID':gt(3)}
        
        table[('a','b'),::{'ID':10}] = {'a':1,'b':2,'c':4}
        '''
        
        if type(sls) in ( types.StringType, types.UnicodeType ):
            sls = (sls,)
        
        if type(sls) == types.DictType :
            cond = sls
            condk = []
            limit = 1
            single = True
        
        if type(sls) == types.TupleType :
            
            if type(sls[-1]) == types.SliceType :
                cond = sls[-1].step
                condk = sls[:-1]
                limit = sls[-1].stop
                single = False
                if sls[-1].start != None :
                    raise TypeError, ( 'offset must be none in set', sls )
            elif type(sls[-1]) == types.DictType :
                cond = sls[-1]
                condk = sls[:-1]
                limit = 1
                single = True
            else :
                cond = None
                condk = sls
                limit = None
                single = True
                
        if type(sls) == types.SliceType :
            cond = sls.step
            condk = []
            limit = sls.stop
            single = False
            
            if sls[-1].start != None :
                raise TypeError, ( 'offset must be none in set', sls )
            
            
        condk = [ x if type(x) in ( types.TupleType, types.ListType )
                   else [x,]
                 for x in condk ]
        condk = sum(condk,[])
        
        if not all( [ type(k) == types.StringType for k in condk ] ):
            raise TypeError, \
                      ( 'easysql indices(set) must be as '\
                        '[[col, col, ... ,][:limit:]where]', sls )
        
        cond = cond.items() if cond != None else []
        cond = cond + [ ( k, value[k] ) for k in condk ]
        cond = dict(cond) if cond != [] else None
        
        row = dict([ (k, v) for k, v in value.items() if k not in condk ])
        
        if row == {} :
            raise TypeError, \
                      ( 'value must at least one to set', value, condk )
            
        n, x = self._set( row, cond, limit )
        
        if single == True and n == 0 :
            raise NotFoundError, 'not found'
        
        return
    
    def __delitem__( self, sls ):
        '''
        del table[{'attr1':1}]
        del table[::{'attr1':1}]
        '''
        
        if type(sls) == types.DictType :
            
            cond = sls
            condk = []
            limit = 1
            offset = None
            single = True
            
        elif type(sls) == types.SliceType :
            
            cond = sls.step
            condk = []
            limit = sls.stop
            offset = sls.start
            single = False
            
        else :
            raise TypeError, \
                      ( 'easysql indices(delete) must be as '\
                        '[offset:limit:]where]', sls )
        
        return
    
    def __contains__( self, name ):
        '''
        {} in table
        '''
        
        return
    
    def __invert__(obj):
        '''
        (~table)[...]
        SQL(table)[...]
        table.sql[]
        '''
        
        return

if __name__ == '__main__' :
    
    a = Table('A')
    
    a << {'a':1,'b':2} << {'c':1,'d':2}
    
    x = {'a':1}
    a >> x
    print 'x',x
    
    a[{'a':1}]
    
    keys = ['a','b']
    a[keys,]
    print 'a[:]',a[:]
    
    a.extend( [{'a':1,'b':2},{'b':2,'c':3},{'a':default(),'c':3}] )
    
    a[{'a':1}] = {'b':this('c')+1}
    a['a',::] = {'a':1,'b':this('c')+2}



