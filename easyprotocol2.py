
from pyparsing import Word, alphas, nums, alphanums, delimitedList, \
Optional, Forward, StringEnd, Keyword, Suppress, Literal, CaselessLiteral, \
Combine, ZeroOrMore

exprStack = []
varStack  = []

def pushFirst( str, loc, toks ):
    exprStack.append( toks[0] )

def assignVar( str, loc, toks ):
    varStack.append( toks[0] )
    

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

name = ident.copy().setName('name')
struct = ident.copy().setName('struct')
length = Optional( LPAREN+expr+RPAREN ).setName('length')
array = Optional( LBRACK+expr+RBRACK ).setName('array')

#syntax = Optional( cases + ':' ) \
#         + ident.setName('name') + ident.setName('struct') \
#         + Optional( LPAREN+expr+RPAREN ).setName('length') \
#         + Optional( LBRACK+expr+RBRACK ).setName('array') \
#         + StringEnd()

syntax = Optional( cases + ':' ) \
         + name + struct \
         + length \
         + array \
         + StringEnd()

#print expr.parseString( 'a(1,1)+1' )
x = syntax.parseString( "true:name struct(abc)[a(1,1)+b(2,2)]" )
print x
print x.asDict()

    
point = Literal('.')
e = CaselessLiteral('E')
plusorminus = Literal('+') | Literal('-')
number = Word(nums) 
integer = Combine( Optional(plusorminus) + number )
floatnumber = Combine( integer +
                       Optional( point + Optional(number) ) +
                       Optional( e + integer )
                     )

plus  = Literal( "+" )
minus = Literal( "-" )
mult  = Literal( "*" )
div   = Literal( "/" )
lpar  = Literal( "(" ).suppress()
rpar  = Literal( ")" ).suppress()
addop  = plus | minus
multop = mult | div
expop = Literal( "^" )
assign = Literal( "=" )

expr = Forward()
atom = ( ( e | floatnumber | integer | ident ).setParseAction(pushFirst) | 
         ( lpar + expr.suppress() + rpar )
       )
        
factor = Forward()
factor << atom + ZeroOrMore( ( expop + factor ).setParseAction( pushFirst ) )
        
term = factor + ZeroOrMore( ( multop + factor ).setParseAction( pushFirst ) )
expr << term + ZeroOrMore( ( addop + term ).setParseAction( pushFirst ) )

print expr.parseString('a+(1+2)*5+7')
print exprStack