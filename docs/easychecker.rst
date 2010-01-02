=========================
 Easychecker
=========================




 Designs
=========================

The aim is a datastructure checker which like the datastructure defines in
documents.

there is an example function ::

    # doc.txt
    
    '''
    Function : foo
    
    Arguments datastructures :
        a  ->  dict( int:int, ... )
        b  ->  list( str, ... )
        
    Return datastructures:
        dict( str:str, ... )
    '''
    
    # code.py :
    
    def foo( a, b ):
        
        return dict([ (b[k], k[v]) for k, v in a.items() ])
        
We want to check that the aruments passed in is compitiable to the
datastructures written in document. Write the code to check arguments?
NO. we already write the datastructures define in documents, i didn't like to
translate it to code. so, i want to write a lib which trans the datastructures
in documents to a reality checker in code. it may be like this ::
    
    foo_a_check = Checker( 'dict( int:int, ... )' )
    foo_b_check = Checker( 'list( str, ... )' )
    foo_r_check = Checker( 'dict( str:str, ... )' )
    
    def foo_safe( a, b ):
        
        assert ( not foo_a_check(a) ) and ( not foo_b_check(b) )
        
        rst = dict([ (b[k], k[v]) for k, v in a.items() ])
        
        assert not foo_r_check(rst)
        
        return rst

It can used with `autochecker` and `easydocstring` , a combo application
maybe wrote like this ::
    
    import easydocstring
    import autochecker
    
    def safe( func ):
        
        checkers = easydocstring.parsedocstring( func.__doc__ )
        checkers = dict( [ (k, Checker(v)) for k, v in chekers.items() ] )
        
        return autochecker.Parachecker( checkers )( func )
    
    @safe
    def foo( a, b ):
        '''
        Arguments `a`'s datastructures                               .value as a
            dict( int:int, ... )
        Arguments `b`'s datastructures                               .value as b
            list( str, ... )
            
        Return datastructures                                       .value as ''
            dict( str:str, ... )
        '''
        
        return dict([ (b[k], k[v]) for k, v in a.items() ])
    
Imitate json and database's style, these most likely using checker.
so, the json's style identifier must be supported ::
        
    python style identifier    json style identifier
    
    dict                       object
    list / tuple               array
    str                        string
    int                        number
    
    supported all identifier
    
    
    database datatype's style  checker's style
    
    string(20)                 string(-20)
    int(5)                     int(-5)         # not same meaning
    
    not compelete copy.
        
        
In usually, checker often couple with parser, to keep the program high
efficiency, we like making recursion once than twice. so the checker need
a function to parse the datastructures or accelerate the parser ::
    
    foo_doc = '''
        
        Arguments `a`'s datastructures                            .value as a, f
            dict( int:int, ... )
                  F   F
        Arguments `b`'s datastructures                               .value as b
            list( str, ... )
            
        Return datastructures                                       .value as ''
            dict( str:str, ... )
        
        '''
    
    doc = easydocstring( foo_doc )
    
    foo_a_check = Checker( doc['a'], parser=[doc['f'],] )
    foo_b_check = Checker( doc['b'] )
    foo_r_check = Checker( doc[''] )
    
    
    def foo( a, b ):
        
        a = a.copy()
        
        assert ( not foo_a_check( a, parser = { 'F' : lambda x : b[x] } ) ) \
               and ( not foo_b_check(b) )
        
        assert not foo_r_check(a)
        
        return a



 Basic operation
-------------------------

============================   =================================================
Format                         examples ( T = True , F = False )
============================   =================================================
number                         123 -> T ; '123' -> F
number(>200)                   456 -> T ; 123 -> F ; 200 -> F
number(-200)                   456 -> F ; 123 -> T ; 200 -> F
string                         123 -> F ; '123' -> T
string(<3)                     'a' -> T ; '123' -> F
string(+3)                     'a' -> F ; '123' -> T ; '1234' -> T
string(3)                      'a' -> F ; '123' -> T ; '1234' -> F
'a'                            'a' -> T ; 'b' -> F
.a                             'a' -> T ; 'b' -> F
bool                           True -> T ; False -> T
null                           None -> T ; 123 -> F
array                          [a,b,c] -> T ; (a,b) -> T
array(3)                       [a,b,c] -> T ; (a,b) -> F ; [a,b,(a,b)] -> T
array(string)                  ['a','b','c'] -> T ; ('a',0) -> F
array(3, string)               ['a','b','c'] -> T ; ('a','b') -> F
array(2, string(2))            ['ab','bc'] -> T ; ('ab','b') -> F
set                            [a,b,c] -> T ; (a,b) -> T ; (a,b,a) -> F
set(number(<10))               [0,1] -> T ; (0,'1') -> F ; (2,6,15) -> F
object                         {'a':1} -> T ;
object(string:number)          {'a':1} -> T ; {'a':'b'} -> F ; {True:6} -> F
string | number                123 -> T ; '123' -> T
============================   =================================================



 Advance operation
-------------------------

::
    array(.a, .b, .c)
           ['a','b','c'] -> T ; ['a','a','b'] -> T ; [] -> T ; ['a','d'] -> F
    array(.a, #.b, .c)
           ['a','b','c'] -> T ; ['a','a','b'] -> T ; [] -> F ; ['a'] -> F
           ['b','d'] -> F ; ['a','b','b'] -> T
    array(.a, #.b, .c, string)
           ['a','b','c'] -> T ; ['a','a','b'] -> T ; [] -> F ; ['a'] -> F
           ['b','d'] -> T ; ['a','b','b'] -> T
    object(.a:bool, #.b:string, string:number)
           {'a':6, 'b':'b'} -> F ; {'b':'b'} -> T ; {'b':0} -> F ;



 Grammer
=========================


 Basic Grammer
-------------------------

checker( [ checker, ... ] ) or \
checker( [ checker, ... ] [ checker:checker, ...] )


 Checker's Type
-------------------------

**tag checker**
    
tag checker is the additional checker of parent checker
it check will the obj which the parent checker checked.

eg ::
    checker : A(T)
    data    : o
    logic   : checker_A(o) and checker_T(o)

and tag checker can't using as top checker.

you can use 'checkerattr' wrapper to set a checker as tag checker.

eg ::
    @checkerattr('tag')
    @autologchecker
    def checker_T( self, x ):
        ...
        
    
**child checker ( default )**
    
child checker check for the test data's child item.
it only be used in 'object ( in python as dict )' or
'array ( in python as list or tuple )'.

eg ::
    checker : A(C)
    data    : o # list type or tuple type
    logic   : checker_A(o) and all( [ checker_C(x) for x in o ] )

eg ::
    checker : A(K:V)
    data    : o # dict type
    logic   : checker_A(o) and \
              all([ checker_K(k) and checker_K(v) for k, v in o.items() ])

and if has multi child checker, the child item passed any one will be ok.
  
eg ::
    checker : A(C1,C2,C3)
    data    : o
    logic   : checker_A(o) and \
              all( [ any( [ checker_C1(x),
                            checker_C2(x),
                            checker_C3(x),
                          ]) for x in o ] )
    
**absolute checker**
    
absolute checker is a type of child checker, it has all property of
child checker. 'object' or 'array' will check that is there child item
pass the checker. if not, the parent checker will return False.
Commonly, we use '#' to make a child checker to an absolute checker.
Also you can use 'checkerattr' wrapper to set a checker as absolute
checker , but it not recommend , it will confound the child checker and
absolute checker.

eg ::
    checker : A(#C)
    data    : o # list type or tuple type
    logic   : checker_A(o) and all( [ checker_C(x) for x in o ] ) \
              and len( [ True for x in o if checker_C(x) ] ) > 1

