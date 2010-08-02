#!/usr/bin/env python2.6
# coding: utf-8

import sys
import operator
import re
import types

from simpleparse import generator
from mx.TextTools import TextTools


from pprint import pprint





def checkerattr( *args ):
    
    def setcheckerattr( func ):
        
        setattr( func, 'type', args )
            
        return func
    
    return setcheckerattr

    
def autologchecker( func ):
    
    def autologchecker ( self, stack, log, x, *args ):
        
        if func( self, x, *args ) == False :
            
            tostrx = str(x)
            tostrx = tostrx if len(tostrx) <= 10 else ( tostrx[:7]+'...' )
            
            self._log( stack, log, "'%s' is not correct format as <%s> " %
                                      ( tostrx, func.__name__[8:], ) )
            
            return False
        
        return True
        
    autologchecker._iswrapper = True
    autologchecker._realcmd = func
    autologchecker.__name__ = func.__name__
    autologchecker.__doc__ = func.__doc__
    
    return autologchecker




class CheckerError(Exception):
    pass


class Checker(object):
    
    checkergrammer = r'''
        expr    := funchkr / numchkr / strchkr
        exprsub := funpair / ( strhead?, strpair ) /
                   funchkr / numchkr / ( strhead?, strchkr )
        strpair := strchkr, [ \t\r\n]*, ':', [ \t\r\n]*, ( funchkr / strchkr )
        funpair := funchkr, [ \t\r\n]*, ':', [ \t\r\n]*, ( funchkr / strchkr )
        funchkr := funname,
                   ( '(', [ \t\r\n]*, ( exprsub, [ \t\r\n]*, ',', [ \t\r\n]* )*,
                                    ( exprsub )?, [ \t\r\n]*, ')' )?
        funname := [a-zA-Z@]+
        numchkr := ( [><+-]?, [0-9]+ ) / [+-]
        strchkr := ( ".", -[,:()]+) /
                   ( '"', ( '\\\\' / '\\"' / -["] )*, '"' ) /
                   ( "'", ( '\\\\' / "\\'" / -['] )* , "'" ) /
                   ( '`', ( '\\\\' / '\\`' / -[`] )* , '`' )
        strhead := '#' / '!'
    '''
    
    parser = generator.buildParser(checkergrammer).parserbyname('expr')
    
    def __init__( self, checkercode ):
        
        self.name = checkercode
        
        self.checker = self._build( checkercode )
        
        return
    
    def __call__( self, obj, stack=[], log=[] ):
        
        if log == None :
            
            log = []
            rst = self.checker( obj, stack, log )
            
            if rst == False :
                # disabled by xp
                # print '< checker :', self.name, '>'
                # print '\r\n'.join(log)
                pass
                
            return rst
        
        return self.checker( stack, log, obj )
    
    def _build( self, code ):
        
        success, tree, nchar = TextTools.tag( code, self.parser )
        
        if success == 0 or nchar != len(code):
            raise CheckerError, 'Syntax Error at %d neared \' ... %s ... \'.' \
                                  % ( nchar, code[nchar-5:nchar+5] )
        # disabled by xp
        # pprint(tree)
        
        return self._build_expr( code, tree )
    
    def _build_expr( self, code, tree ):
        
        builder = getattr( self, '_build_'+ tree[-1][0] )
        
        ckr = builder( code, tree[-1] )
        
        if type(ckr) == type(()) :
            xckr = ckr[0]
        else :
            xckr = ckr
        
        for head in tree[:-1] :
            strhead = code[head[1]:head[2]]
            
            if strhead == '#':
                xckr.type += ['abs',]
            
        return ckr
        
        
    _build_exprsub = _build_expr
    
    def _build_funchkr( self, code, tree ):
        
        checkername = tree[3][0]
        
        if checkername[0] != 'funname' :
            raise CheckerError, 'can not reach here [%s]' % \
                                                 sys._getframe().f_code.co_name 
        
        checkername = code[checkername[1]:checkername[2]]
        
        try :
            checker = getattr( self, 'checker_'+checkername )
        except :
            raise CheckerError, 'checker <%s> not found.' % checkername
        
        childs = tree[3][1:]
        
        childs = [ self._build_exprsub( code, c[3] ) for c in childs ]
        
        _types = [ ['pair',] if type(c) == type(()) else getattr( c, 'type', [] )
                   for c in childs ]
        
        _types = [ 'tag' if 'tag' in t else 'pair' if 'pair' in t else None
                   for t in _types ]

        tags = [ c for t, c in zip( _types, childs ) if t == 'tag' ]
        pairs = [ c for t, c in zip( _types, childs ) if t == 'pair' ]
        items = [ c for t, c in zip( _types, childs ) if t == None ]
        
        return self._makechecker_funchkr( checkername,
                                          checker, tags, pairs, items )
    
    @staticmethod
    def _log( stack, logger, info ):
        logger += [ (stack[:], info), ]
        return
    
    def _makechecker_funchkr( self, name, checker, tags, pairs, items  ):
        
        ckrtype = getattr( checker, 'type', [] )
        
        if 'object' in ckrtype :
            
            if items != [] :
                raise CheckerError, '%s can not contain item subchecker.' % name
            
            abses = set([ idx for idx, pair in enumerate(pairs)
                              if 'abs' in pair[0].type ])
            
            def _checker( stack, logger, obj ):
                
                if checker( stack, logger, obj ) == False :
                    return False
                
                # tag checker
                
                t_rst = [ tck( stack, logger, obj ) for tck in tags ]
                
                t_rst = all(t_rst)
                
                # item checker
                
                i_rst = [ self._buildin_checker_pairs(
                                                     stack, logger, sub, pairs )
                          for sub in obj.items() ]
                
                i_rst, n_rst = zip( *i_rst ) or [[],[]]
                
                i_rst = all(i_rst)
                
                # abs checker
                
                a_rst = abses - set(n_rst)
                
                if len(a_rst) != 0 :
                    
                    self._log( stack, logger,
                               ( a_rst, 'some arguments required' ) )
                    
                    a_rst = False
                    
                else :
                    
                    a_rst = True
                
                return t_rst and i_rst and a_rst
            
            
        elif 'array' in ckrtype :
            
            if pairs != [] :
                raise CheckerError, '%s can not contain pair subchecker.' % name
            
            abses = set([ idx for idx, item in enumerate(items)
                              if 'abs' in item.type ])
            
            def _checker( stack, logger, obj ):
                
                if checker( stack, logger, obj ) == False :
                    return False
                
                # tag checker
                
                t_rst = [ tck( stack, logger, obj ) for tck in tags ]
                
                t_rst = all(t_rst)
                
                # item checker
                
                i_rst = [ self._buildin_checker_items(
                                                     stack, logger, sub, items )
                          for sub in obj ]
                
                i_rst, n_rst = zip( *i_rst ) or [[],[]]
                
                i_rst = all(i_rst)
                
                # abs checker
                
                a_rst = abses - set(n_rst)
                
                if len(a_rst) != 0 :
                    
                    self._log( stack, logger,
                               ( a_rst, 'some arguments required' ) )
                    
                    a_rst = False
                    
                else :
                    
                    a_rst = True
                
                return t_rst and i_rst and a_rst
                
        else :
            
            if items != [] or pairs != [] :
                raise CheckerError, '%s can not contain subchecker.' % name
            
            def _checker( stack, logger, obj ):
                
                if checker( stack, logger, obj ) == False :
                    return False
                
                rst = [ tck( stack, logger, obj ) for tck in tags ]
                
                return all(rst)
        
        _checker.__name__ = checker.__name__
        _checker.type = list(ckrtype)[:]
        
        return _checker
    
    def _makechecker_numchkr( self, name, oper, y ):
        
        def _checker ( stack, logger, obj ):
            
            return self._buildin_checker_numchkr( stack, logger, obj, y, oper )
        
        _checker.__name__ = name
        orignaltype = getattr( self._buildin_checker_numchkr, 'type', [] )
        _checker.type = list(orignaltype)[:]
        
        return _checker
    
    opertable = {
        '+': operator.ge,
        '-': operator.le,
        '>': operator.gt,
        '<': operator.lt,
        '=': operator.eq,
    }
    
    def _build_numchkr( self, code, tree ):
        
        if tree[0] != 'numchkr' :
            raise CheckerError, 'can not reach here [%s]' % \
                                                 sys._getframe().f_code.co_name 
        
        checkername = code[tree[1]:tree[2]]
        
        if checkername[0] in self.opertable :
            
            oper = self.opertable[checkername[0]]
            
            y = checkername[1:]
            y = 0 if y == '' else int(y)
            
        else :
            
            oper = operator.eq
            y = int(checkername)
        
        return self._makechecker_numchkr( checkername, oper, y )
    
    def _makechecker_strchkr( self, name, y ):
        
        def _checker ( stack, logger, obj ):
            
            return self._buildin_checker_strchkr( stack, logger, obj, y )
        
        _checker.__name__ = name
        orignaltype = getattr( self._buildin_checker_strchkr, 'type', [] )
        _checker.type = list(orignaltype)[:]
        
        return _checker
    
    def _build_strchkr( self, code, tree ):
        
        if tree[0] != 'strchkr' :
            raise CheckerError, 'can not reach here [%s]' % \
                                                 sys._getframe().f_code.co_name 
        
        checkername = code[tree[1]:tree[2]]
        
        if checkername.startswith('.'):
            y = checkername[1:]
        elif checkername.startswith('`'):
            y = eval( '"""' + checkername[1:-1] + '"""' )
        else :
            y = eval( checkername )
        
        return self._makechecker_strchkr( checkername, y )
    
    def _build_strpair( self, code, tree ):
        
        pair = [ getattr( self, '_build_'+ subtree[0] )( code, subtree )
                 for subtree in tree[3] ]
        
        pair = tuple(pair)
        
        return pair
    
    _build_funpair = _build_strpair
    
    @checkerattr( 'buildin' )
    def _buildin_checker_items( self, stack, logger, subobj, subcheckers ):
        
        if subcheckers == [] :
            return ( True, None )
        
        icls = [ ( i, c, list() ) for i, c in enumerate( subcheckers ) ]
        
        for iii, ckr, log in icls :
            if ckr( stack, log, subobj ) == True :
                return ( True, iii )
            
        logs = [ ( max([ len(stk) for stk, inf in l ]), l )
                    for i, c, l in icls ]
        
        maxdeep = max( zip(*logs)[0] )
        
        logger += [ log for deep, log in logs if deep == maxdeep ]
        
        return ( False, None )
    
    @checkerattr( 'buildin' )
    def _buildin_checker_pairs( self, stack, logger, subobj, subcheckers ):
        
        if subcheckers == [] :
            return ( True, None )
        
        icls = [ ( i, c, list() ) for i, c in enumerate( subcheckers ) ]
        
        for iii, ckr, log in icls :
            kckr, vckr = ckr
            if kckr( stack, log, subobj[0] ) == True :
                if vckr( stack+[str(subobj[0]),], logger, subobj[1] ) == True :
                    return ( True, iii )
                else :
                    return ( False, iii )
        
        logs = [ ( max([ len(stk) for stk, inf in l ]+[0,]), l )
                    for i, c, l in icls ]
        
        maxdeep = max( zip(*logs)[0] )
        
        #logger += sum([ log for deep, log in logs if deep == maxdeep ], [] )
        
        self._log( stack, logger, 'Uncached key "%s"' %( str( subobj[0] ) ) )
        
        return ( False, None )
    
    inopertable = {
        operator.lt : '<',
        operator.le : '<=',
        operator.eq : '==',
        operator.ne : '!=',
        operator.ge : '>=',
        operator.gt : '>',
    }
    
    @checkerattr( 'buildin', 'tag' )
    def _buildin_checker_numchkr( self, stack, log, x, y, op ):
        
        orignalx = x
        
        if type(x) not in ( types.IntType, types.LongType, types.FloatType ):
            x = len(x)
            orignalx = ( str(orignalx) \
                            if type(orignalx) != types.UnicodeType \
                            else orignalx 
                       ) + "'s length"
        
        if not op( x, y ) :
            
            self._log( stack, log,
                       '%s not %s %s' % ( str(orignalx),
                                          self.inopertable[op], str(y) )
                     )
            
            return False
        
        return True
    
    
    @checkerattr( 'buildin' )
    def _buildin_checker_strchkr( self, stack, log, x, y ):
        
        if type(x) not in ( type(''), type(u'') ):
            
            self._log( stack, log, '%s is not a string' % ( x, ) )
            
            return False
        
        if x != y :
            
            self._log( stack, log, '"%s" != "%s" ' % ( x, y ) )
            
            return False
        
        return True
    
    
    @checkerattr( 'buildin' )
    @autologchecker
    def checker_any( self, x ):
        
        return True
    
    @checkerattr( 'buildin', 'object' )
    @autologchecker
    def checker_object( self, x ):
        return type(x) == type({})
    
    @checkerattr( 'buildin', 'array' )
    @autologchecker
    def checker_array( self, x ):
        return type(x) in ( type([]), type(()) )
        
    @checkerattr( 'buildin' )
    @autologchecker
    def checker_string( self, x ):
        
        return type(x) in ( type(''), type(u'') )
    
    @checkerattr( 'buildin' )
    @autologchecker
    def checker_bool( self, x ):
        return x in ( True, False )
    
    @checkerattr( 'buildin' )
    @autologchecker
    def checker_number( self, x ):
        return type(x) == type(0)
    
    @autologchecker
    def checker_hex( self, x ):
        return re.match(r'[a-fA-F0-9]*',x) != None
    
    @autologchecker
    def checker_ascii( self, x ):
        return type(x) in ( type(''), type(u'') ) \
               and re.match(r'[a-zA-Z0-9_-]*',x) != None
    
    @autologchecker
    def checker_alnum( self, x ):
        return type(x) in ( type(''), type(u'') ) and x.isalnum()
    
    @autologchecker
    def checker_null( self, x ):
        return x == None

    
if __name__=='__main__':
    
    testdata = {
        'object( -5, #.a:string, .b:string )':
            [ {}, {'a':'hahaha'}],
        'object( -5, .a:number )':
            [ {}, {'a':'hahaha'}, {'a':3}],
        'object( -5, #.a:string, .a:number )':
            [ {}, {'a':'hahaha'}, {'a':3}],
        'array( string(3) )':
            [ ['abd','abc'], ],
        'null':
            [ None, ]
    }
    
    for checker, datas in testdata.items() :
        
        print '--', checker
        
        ckr = Checker(checker)
        
        for data in datas :
            print '  ', data, '>', ckr(data)
    