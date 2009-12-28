
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


def condcheck( func ):
    
    def _checker( self, another ):
        
        if self.iscond == True :
            raise EasySqlException, 'Syntax Error of `this` in easysql'
        
        return func( self, another )
    
    _checker._decorator = func
    _checker.__name__ = func.__name__
    _checker.__doc__  = func.__doc__
    
    return _checker

class This( object ):
    
    def __init__( self, colname=None ):
        
        self.iscond = False
        self.str = '`'+colname+'`' if colname else ''
        
    @condcheck
    def __add__ ( self, another ):
        
        self.str = '(' + self.str + '+' + \
        ( another._tosql if hasattr( another, '_tosql' ) else str(another) ) + \
        ')'
        
        return self
    
    @condcheck
    def __sub__( self, another ):
        
        self.str = '(' + self.str + '-' + \
        ( another._tosql if hasattr( another, '_tosql' ) else str(another) ) + \
        ')'
        
        return self
    
    @condcheck
    def __mul__( self, another ) :
        
        self.str = '(' + self.str + '*' + \
        ( another._tosql if hasattr( another, '_tosql' ) else str(another) ) + \
        ')'
        
        return self
    
    @condcheck
    def __div__( self, another ) :
        
        self.str = '(' + self.str + '/' + \
        ( another._tosql if hasattr( another, '_tosql' ) else str(another) ) + \
        ')'
        
        return self
    
    @condcheck
    def __gt__( self, another ):
        
        self.iscond = True
        
        self.str = '(' + self.str + '>' + \
        ( another._tosql if hasattr( another, '_tosql' ) else str(another) ) + \
        ')'
    
    @condcheck
    def __ge__( self, another ):
        
        self.iscond = True
        
        self.str = '(' + self.str + '>=' + \
        ( another._tosql if hasattr( another, '_tosql' ) else str(another) ) + \
        ')'
        
        return self
    
    @condcheck
    def __lt__( self, another ):
        
        self.iscond = True
        
        self.str = '(' + self.str + '<' + \
        ( another._tosql if hasattr( another, '_tosql' ) else str(another) ) + \
        ')'
    
    @condcheck
    def __le__( self, another ):
        
        self.iscond = True
        
        self.str = '(' + self.str + '<=' + \
        ( another._tosql if hasattr( another, '_tosql' ) else str(another) ) + \
        ')'
        
        return self
    
    def _tosql( self ):
        
        return self.str
    
def this( colname ):
    return This( colname )

SQLThisType = type( This() )




class SQLFunction( object ):
    
    def __init__ ( self, fname ):
        
        self.fname = fname
        
    def __call__ ( self, *args ):
        
        args = ','.join( [ a._tosql if hasattr( a, '_tosql' )
                                    else "'"+str(a)+"'"
                           for a in args ] )
        
        r = This('')
        r.str = self.fname+'('+args+')'
        
        return r 

def func( fname ):
    return SQLFunction(fname)





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
    
    
    
class Raw( object ):
    
    def __init__( self, raw ):
        self. raw = raw 
    
    def _tosql(self):
        return raw
    
def raw( rawdata ):
    return Raw( rawdata )
    
    
    
    
    
class NoArg( object ):
    pass
    


ArrayTypes = ( types.ListType, types.TupleType )
StrTypes = ( types.StringType, types.UnicodeType )


class Tablet( object ) :
    '''
    tablet of table
    '''
    
    def _buildrow( self, row ):
        
        return dict( [ ( k, v._tosql() if hasattr(v, '_tosql')
                            else "'"+str(v)+"'"
                       ) for k, v in row.items() if k in self.cols ] )
    
    def __init__ ( self, name, cols=[] ):
        
        self.name = name
        
        self.cols = ['a','b','c','d','e']
        
        pass
        
    def _insert( self, rows, dup=None ):
        
        rows = [ self._buildrow(row) for row in rows ]
        dup = self._buildrow(dup) if dup else None
        
        sql = self._insert_sql( rows, dup )
        
        # self.query()
        print sql
        
        # return ( affect rows number , lastid )
        return 1, 1
        
    def _insert_sql( self, rows, dup = None, ignore = True ):
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
        
        return sql
    
    def _select( self, cond=None, condx=[], cols=None, limit=None, offset=None ):
        
        cond = self._buildrow(cond) if cond else None
        
        sql = self._select_sql( cond, condx, cols, limit, offset )
        
        # self.query()
        print sql
        
        # return ( result rows, result )
        return 1, [{'a':1,'b':2,'c':3,'d':4,'e':5}]
    
    def _select_sql( self,
                     cond=None, condx=[], cols=None,
                     limit=None, offset=None, vset=None ):
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
        
        print 's',condx
        sql = ' '.join( [
            
            'SELECT',
            'DISTINCT' if vset else '',
            ','.join([ '`%s`' % (c,) for c in cols ]),
            'FROM `%s`' % self.name ,
            'WHERE' if cond or condx!=[] else '',
                ','.join( [ '`%s`=%s' % i for i in cond.items() ] ) \
                                                                if cond else '',
                ',' if cond and condx !=[] else '',
                ','.join( [ i._tosql() for i in condx ] ),
            ('LIMIT %d' % (limit,) ) if limit else '',
            ('OFFSET %d' % (offset,) ) if limit and offset else '',
            
        ] )
        
        return sql
        
    def _delete( self, cond=None, condx=[], limit=None ):
        
        cond = self._buildrow(cond) if cond else None
        
        sql = self._delete_sql( cond, condx, limit )
        
        # self.query()
        print sql
        
        # return ( affect rows, None )
        return 1, None
        
    def _delete_sql( self, cond=None, condx=[], limit=None, ignore = True ):
        '''
        DELETE [LOW_PRIORITY] [QUICK] [IGNORE] FROM tbl_name
            [WHERE where_condition]
            [ORDER BY ...]
            [LIMIT row_count]
        '''
        
        sql = ' '.join( [
            
            'DELETE',
            'IGNORE' if ignore else '',
            'FROM `%s`' % self.name ,
            'WHERE' if cond or condx!=[] else '',
                ','.join( [ '`%s`=%s' % i for i in cond.items() ] ) \
                                                                if cond else '',
                ',' if cond and condx !=[] else '',
                ','.join( [ i._tosql() for i in condx ] ),
            ('LIMIT %d' % (limit,) ) if limit else '',
            
        ] )
        
        return sql
        
    def _replace( self, rows ):
        
        rows = [ self._buildrow(row) for row in rows ]
        
        sql = self._replace_sql( rows )
        
        # self.query()
        print sql
        
        # return ( affect rows, lastid )
        return 1, 1
        
    def _replace_sql( self, rows ):
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
        
        return sql
        
    def _update( self, row, cond=None, condx=[], limit=None):
        
        row = self._buildrow(row)
        cond = self._buildrow(cond) if cond else None
        
        sql = self._update_sql( row, cond, condx, limit )
        
        # self.query()
        print sql
        
        # return ( matched rows, affectrows )
        return 1, 1
        
        
    def _update_sql( self, row, cond=None, condx=[],
                           limit=None, ignore = True  ):
        '''
        UPDATE [LOW_PRIORITY] [IGNORE] table_reference
            SET col_name1={expr1|DEFAULT} [, col_name2={expr2|DEFAULT}] ...
            [WHERE where_condition]
            [ORDER BY ...]
            [LIMIT row_count]
            
        using Mysql_info() to get the match number affact number
        '''
        
        sql = ' '.join( [
            
            'UPDATE',
            'IGNORE' if ignore else '',
            '`%s`' % self.name ,
            'SET',
                ','.join( [ '`%s`=%s' % i for i in row.items() ] ),
            'WHERE' if cond or condx!=[] else '',
                ','.join( [ '`%s`=%s' % i for i in cond.items() ] ) \
                                                                if cond else '',
                ',' if cond and condx !=[] else '',
                ','.join( [ i._tosql for i in condx ] ),
            ('LIMIT %d' % (limit,) ) if limit else '',
            
        ] )
        
        return sql

class Table ( object ) :
    '''
    table class of easysql
    '''
    
    @staticmethod
    def getresult( conn ):
        
        rst = conn.store_result()
        
        return rst.fetch_row( rst.num_rows() )
        
    
    @staticmethod
    def _sliceparser( slc ):
        '''
        table[::]
        table[col,col,[col,]]
        table[(col,col,)]
        table[::(cond,cond)]
        talbe[::cond]
        talbe[col,::]
        '''
        
        type_slc = type(slc)
        
        if type_slc in StrTypes :
            
            cols = [slc,]
            slc = None
            type_slc = None
        
        elif type_slc in ArrayTypes :
            
            if type( slc[-1] ) == types.SliceType :
                
                cols = slc[:-1]
                cols = sum([c if c in ArrayTypes else [c,] for c in cols], [])
                slc = slc[-1]
                type_slc = type(slc)
                
            else :
                
                for i, e in enumerate(slc):
                    if type(e) in ( types.DictType, SQLThisType ):
                        break
                else :
                    i += 1
                
                cols = slc[:i]
                cols = sum([c if c in ArrayTypes else [c,] for c in cols ], [])
                
                slc = slc[i:]
                type_slc = None
            
        else :
            cols = []
            
        if type_slc == None :
            limit = 1
            offset = None
            cond = {} if slc == [] else slc
            single = True
        elif type_slc == types.DictType :
            #cols = []
            limit = 1
            offset = None
            cond = slc
            single = True
        elif type_slc == types.SliceType :
            #cols = []
            offset = slc.start
            limit = slc.stop
            cond = slc.step
            single = False
        else :
            raise Exception, slc
            
        type_cond = type(cond)
            
        if type_cond in ArrayTypes :
            
            cond = dict( sum( [ s.items() for s in cond
                                if type(s) == types.DictType
                              ], [] ) )
            condx = [ s for s in slc if type(s) == SQLThisType ]
            
        elif type_cond == types.DictType :
            
            condx = []
            
        elif type_cond == types.NoneType :
            
            condx = []
            
        else :
            
            raise Exception, cond
            
        return cols, offset, limit, cond, condx, single
    
    def __init__ ( self, tablets = [] ):
        
        self.colconv = []
        
        #self.tablets = [ Tablet('testtable') ]
        self.tablets = tablets
        
        return
        
    def _splitter( self, row ):
        
        return [0,]
    
    def _gettablets( self, tbl ):
        
        return self.tablets[0]
        
    def _buildrow( self, row ):
        
        return row.copy()
        
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
        tblc = [ r for r, t in zip(rows, tbls) if len(t) != 1 ]
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

    
    def _read( self, cond, condx=[], cols = None, limit = None, offset = None ):
        
        cond = self._buildrow(cond) if cond else cond
        tbls = self._splitter(cond) # todo : set to all tablets if cond is none
        
        tlimit = limit
        rst = []
        nx = 0
        for tbl in tbls : # read lazy
            n, r = self._gettablets(tbl)._select( cond, condx, cols, tlimit )
            nx += n
            rst = rst + r
            tlimit = ( tlimit - n ) if tlimit != None else tlimit
            if tlimit <= 0 :
                break
        
        return nx, rst
        
    def _set( self, row, cond, condx=[], limit = None ):
        
        cond = self._buildrow(cond) if cond else cond
        tbls = self._splitter(cond) # todo : set to all tablets if cond is none
        
        row = self._buildrow(row)
        
        tlimit = limit
        nx = 0
        for tbl in tbls :
            n, r = self._gettablets(tbl)._update( row, cond, condx, tlimit )
            nx += n
            tlimit = ( tlimit - n ) if tlimit != None else tlimit
            if tlimit <= 0 :
                break
        
        return nx, None
    
    def _delete( self, cond, condx=[], limit = None ):
        
        cond = self._buildrow(cond) if cond else cond
        tbls = self._splitter(cond) # todo : set to all tablets if cond is none
        
        tlimit = limit
        nx = 0
        for tbl in tbls : # read lazy
            n, r = self._gettablets(tbl)._delete( cond, condx, tlimit )
            nx += n
            tlimit = ( tlimit - n ) if tlimit != None else tlimit
            if tlimit <= 0 :
                break
        
        return nx, None
        
    def __lshift__ ( self, rows ):
        '''
        table << {'attr':'inserted'}
        table << [{'attr':'inserted'},]
        '''
        
        if type(rows) == types.DictType :
            rows = [rows,]
            single = True
        elif type(rows) in ( types.ListType, types.TupleType ) :
            single = False
        else :
            raise TypeError, 'easysql << must row|[row,...]'
        
        n, lastid = self._write( rows )
        
        if single == True and n == 0:
            raise DuplicateError, ''
        
        return self
    
    def __iadd__ ( self, rows ):
        '''
        table += [{'attr':'inserted'},]
        '''
        
        if type(rows) in ( types.ListType, types.TupleType ) :
            single = False
        else :
            raise TypeError, 'easysql << must row|[row,...]'
        
        n, lastid = self._write( rows )
        
        if n != len(rows):
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
        
        n, rst = self._read( cond, [], cols=keys, limit=1)
        
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
        
    def gets( self, cond, keys=[], limit=None, offset=None):
        '''
        table.gets( {'a':1}, keys=[], limit=n, offset = p )
        '''
        
        n, rst = self._read( cond, [], cols=keys, limit=limit, offset=offset )
        
        return rst

    def __getitem__( self, slc ):
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
        
        keys, offset, limit, cond, condx, single = self._sliceparser( slc )
        
        n, rst = self._read( cond, condx, keys, limit, offset )
        
        if single == False :
            return rst
            
        if n != 1 :
            raise NotFoundError, 'not found'
        
        return rst[0]
        
    def set( self, cond, row ):
        '''
        table.set( {'ID':1}, {'attr':'updated'} )
        '''
        
        if row == {} :
            raise TypeError, \
                      ( 'value must at least one to set', value, condk )
        
        n, x = self._set( row, cond, [], 1 )
        
        if n == 0 :
            raise NotFoundError, 'no found'
        
        return
    
    def sets( self, cond, row, limit ):
        '''
        table.sets( {'ID':1}, {'attr':'updated'}, limit=n )
        '''
        
        if row == {} :
            raise TypeError, \
                      ( 'value must at least one to set', value, condk )
        
        n, x = self._set( row, cond, [], limit )
        
        return n
        
    def __setitem__( self, slc, value ):
        '''
        table[{'ID':1}] = {'A':1}
        table[10:50] = {'A':1}
        talbe[::{'ID':1}]] = {'A':1}
        table['ID'] = {'ID':1, 'A':1}
        table['a','b',:50] = {'a':1,'b':2,'ID':gt(3)}
        
        table[('a','b'),::{'ID':10}] = {'a':1,'b':2,'c':4}
        '''
        
        keys, offset, limit, cond, condx, single = self._sliceparser( slc )
        
        cond = dict(   ( cond.items() if cond else [] ) \
                     + [ ( k, value[k] ) for k in keys ] )
        
        row = dict([ (k, v) for k, v in value.items() if k not in keys ])
        
        if row == {} :
            raise TypeError, \
                      ( 'value must at least one to set', value, condk )
            
        n, x = self._set( row, cond, condx, limit )
        
        if single == True and n == 0 :
            raise NotFoundError, 'not found'
        
        return
    
    def __ilshift__( self, rows ):
        '''
        table <<= {'attr':'inserted'}
        table <<= [{'attr':'inserted'},]
        '''
        
        if type(rows) == types.DictType :
            rows = [rows,]
            single = True
        elif type(rows) in ( types.ListType, types.TupleType ) :
            single = False
        else :
            raise TypeError, 'easysql << must row|[row,...]'
        
        n, x = self._replace( rows )
        
        return self
        
    def load( self, row ):
        '''
        table.load( {'attr':'replaced'} )
        '''
        
        n, x = self._replace( [row, ] )
        
        if n == 0 :
            raise EasySqlException, 'row error in load.'
        
        return x[0]
        
    def loads( self, rows ):
        '''
        table.loads( [{'attr':'replaced'},] )
        '''
        
        n, x = self._replace( rows )
        
        return n
    
    def remove( self, cond ):
        
        n, x = self._delete( cond, [], 1 )
        
        if n == 0 :
            raise NotFoundError, 'not found'
        
        return
    
    def removes( self, cond, limit=None ):
        
        n, x = self._delete( cond, [], limit )
        
        return n
    
    def __delitem__( self, slc ):
        '''
        del table[{'attr1':1}]
        del table[::{'attr1':1}]
        '''
        
        keys, offset, limit, cond, condx, single = self._sliceparser( slc )
        
        n, x = self._delete( cond, condx, limit )
        
        if single == True and n == 0 :
            raise NotFoundError, 'not found'
        
        return
    
    def __contains__( self, name ):
        '''
        {} in table
        '''
        
        return
    
    def __invert__( self, obj ):
        '''
        (~table)[...]
        SQL(table)[...]
        table.sql[]
        '''
        
        return
    
    def __concat__( self, other ):
        
        return Tablet( self.tablets + other.tablets )
        
    def __len__( self ):
        
        return len(tablets)
        
    @staticmethod
    def sum( table ):
        
        return Tablet( sum([ t.tablets for t in table ],[]) )

if __name__ == '__main__' :
    
    t = Table([Tablet('testtable'),])
    
    
    print '-- insert --'
    
    t << {'a':1,'b':2} << {'c':1,'d':2}
    print t.append( {'a':1,'b':2} )
    
    t << [{'a':1,'b':2},{'c':1,'d':2}]
    t += [{'a':1,'b':2},]
    print t.extend([{'a':1,'b':2},{'c':1,'d':2}])
    
    t.append( {'a':1}, ondup = {'b':2} )
    
    print '-- select --'
    
    print t[{'a':1}]
    print t['a','b']
    print t.get( {'a':1} )
    
    x = {'a':1}
    t >> x
    print 'x', x
    
    print t[::{'a':1}]
    print t['a','b',:50:]
    print t.gets( {'a':1}, limit=3, offset=8 )
    
    print '-- update --'
    
    t[{'a':1}] = {'b':this('c')+1}
    t['a'] = {'a':1,'b':this('c')+2}
    t.set( {'a':1}, {'b':default()} )
    
    t[::{'attr1':1}] = {'b':2}
    t['a',::] = {'a':1,'b':this('c')+2}
    t.sets( {'a':1}, {'b':2}, limit=5 )
    
    print '-- replace --'
    
    t <<= {'a':1}
    print t.load( {'a':1} )
    t <<= [{'a':1},]
    print t.loads( [{'a':1},] )
    
    
    print '-- delete --'
    
    del t[{'a':1}]
    t.remove({'a':1})
    del t[::{'a':1}]
    t.removes({'a':1})



