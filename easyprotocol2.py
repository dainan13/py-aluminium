
from pyparsing import Word, alphas, nums, alphanums, delimitedList, Optional, Forward, StringEnd, Keyword, Suppress

_keywords = [ 'struct', 'union', 
              'true', 'false', 'none', 'auto',  
              'default', '-',
            ]

kwords = reduce( ( lambda a, b : a|b ), map( Keyword, _keywords ) )

LPAREN, RPAREN, LBRACK, RBRACK = map(Suppress, "()[]")


ident = Word(alphas, alphanums+'_') #identifier
xident = Optional('@') + ident
numvalue = Word(nums) | ('0x'+Word(nums)) | ( Word(nums)+'B' )
case = numvalue | 'true' | 'false'
cases = delimitedList(case.setName('case'))
oper = Word('+-*/', max=1)
expr = Forward()
call = ident + LPAREN + delimitedList(expr) + RPAREN
etok = ( call | ident | numvalue ) + oper + expr
expr << ( etok | call | ident | numvalue )
syntax = Optional( cases + ':' ) \
         + ident.setName('name') + ident.setName('struct') \
         + Optional( LPAREN+expr+RPAREN ).setName('length') \
         + Optional( LBRACK+expr+RBRACK ).setName('array') \
         + StringEnd()

#print expr.parseString( 'a(1,1)+1' )
x = syntax.parseString( "true:name struct(abc)[a(1,1)+b(2,2)]" )
print x