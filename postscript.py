
from simpleparse.parser import Parser

declaration = r'''
EXPRESSION := (TYPE, SAFESPACES?)*, DELIMITER
DELIMITER  := [\r\n]+
SAFESPACES := [ \t]+
COMMENT    := '%', [a-zA-Z0-9 \t]*, ('\r\n' / '\n')
TYPE       := STRING / NUMBERIC / BOOLEAN / NAME / NULL / OPERATOR / ARRAY / DICTIONARY
BOOLEAN    := 'true' / 'false'
OPERATOR   := ([a-zA-Z]+, '*'?) / '"' / '\''
SPACES     := [ \t\r\n]+ / COMMENT+
NUMBERIC   := FLOAT / INTEGER 
INTEGER    := [+-]?, [0-9]+
FLOAT      := [+-]?, ([0-9]+, '.', [0-9]*) / ('.', [0-9]+) 
STRING     := LITERAL_STRING / HEXADECIMAL_STRING
LITERAL_STRING     := '(', ( '\\\\' / '\\)' / -[)] )* ,')'
HEXADECIMAL_STRING := '<', [0-9A-Fa-f]* ,'>'
NAME       := '/', -[\x5B\x5D()<>{}\/\%\0\t\r\n \x0C]+
NULL       := 'null'
ARRAY      := '[' , SPACES?, (TYPE, SPACES?)*, ']'
DICTIONARY := '<<' , SPACES?, (TYPE, SPACES?)*, '>>'
'''

#operators  argc info
type4 = r'''
add         2   %(1)s + %(2)s
sub         2   %(1)s - %(2)s
mul         2   %(1)s * %(2)s
div         2   float(%(1)s) / %(2)s
ldiv        2   %(1)s / %(2)s
mod         2   %(1)s %% %(2)s
neg         1   -%(1)s
abs         1   abs(%(1)s)
ceiling     1   math.ceil(%(1)s)
floor       1   math.floor(%(1)s)
round       1   int(round(%(1))s)
truncate    1   math.trunc(%(1)s)
sqrt        1   math.sqrt(%(1)s)
sin         1   math.sin(%(1)s)
cos         1   math.cos(%(1)s)
atan        1   math.atan(%(1)s)
exp         1   math.atan(%(1)s)
ln          1   math.log(%(1)s)
log         1   math.log10(%(1)s)
cvl         1   int(%(1)s)
cvr         1   float(%(1)s)
eq          2   %(1)s == %(2)s
ne          2   %(1)s != %(2)s
gt          2   %(1)s > %(2)s
ge          2   %(1)s >= %(2)s
lt          2   %(1)s < %(2)s
le          2   %(1)s <= %(2)s
and         2   %(1)s and %(2)s
or          2   %(1)s or %(2)s
xor         2   %(1)s xor %(2)s
not         1   not %(1)s
bitshift    2   %(1)s << %(s)s
'''

#operators  argc 
type4ext = r'''
if          2      if %(1)s : %(2)s
ifelse      3      if %(1)s : %(2)s else : %(3)s
pop         1      %(1)
exch        2      a, b = %(1)s, %(2)s 
dup         2      a = %(1)s
copy        -
index       -
roll        -
'''

#operators      argc rstc
psoperators = r'''
clip            0    0
closepath       0    0
concat          1    0
curveto         6    0
eoclip          0    0
eofill          0    0
fill            0    0
grestore        0    0    
gsave           0    0
lineto          2    0
moveto          2    0
selectfont      1    0
setcachedevice  6    0
setcharwidth    2    0
setcmykcolor    4    0 
setcolor
setcolorspace   1    0
setdash         2    0
setflat         1    0
setgray         1    0 
setlinecap      1    0
setlinejoin     1    0
setlinewidth    1    0
setmiterlimit   1    0
setrgbcolor     3    0
shfill          1    0
show            1    0
stroke          0    0
'''

pdfoperators = r'''
b
closepath, fill, stroke
Close, fill, and stroke path using nonzero winding number rule
4.10
230

B
fill, stroke
Fill and stroke path using nonzero winding number rule
4.10
230

b*
closepath, eofill, stroke
Close, fill, and stroke path using even-odd rule
4.10
230

B*
eofill, stroke
Fill and stroke path using even-odd rule
4.10
230

BDC
(PDF 1.2) Begin marked-content sequence with property list
10.7
851

BI
Begin inline image object
4.42
352

BMC
(PDF 1.2) Begin marked-content sequence
10.7
851

BT
Begin text object
5.4
405

BX
(PDF 1.1) Begin compatibility section
3.29
152

c
curveto
Append curved segment to path (three control points)
4.9
226

cm
concat
Concatenate matrix to current transformation matrix
4.7
219

CS
setcolorspace
(PDF 1.1) Set color space for stroking operations
4.24
287

cs
setcolorspace
(PDF 1.1) Set color space for nonstroking operations
4.24
287

d
setdash
Set line dash pattern
4.7
219

d0
setcharwidth
Set glyph width in Type 3 font
5.10
423

d1
setcachedevice
Set glyph width and bounding box in Type 3 font
5.10
423

Do
Invoke named XObject
4.37
332

DP
(PDF 1.2) Define marked-content point with property list
10.7
851

EI
End inline image object
4.42
352

EMC
(PDF 1.2) End marked-content sequence
10.7
851

ET
End text object
5.4
405

EX
(PDF 1.1) End compatibility section
3.29
152

f
fill
Fill path using nonzero winding number rule
4.10
230

F
fill
Fill path using nonzero winding number rule (obsolete)
4.10
230

f*
eofill
Fill path using even-odd rule
4.10
230

G
setgray
Set gray level for stroking operations
4.24
288

g
setgray
Set gray level for nonstroking operations
4.24
288

gs
(PDF 1.2) Set parameters from graphics state parameter dictionary
4.7
219

h
closepath
Close subpath
4.9
227

i
setflat
Set flatness tolerance
4.7
219

ID
Begin inline image data
4.42
352

j
setlinejoin
Set line join style
4.7
219

J
setlinecap
Set line cap style
4.7
219

K
setcmykcolor
Set CMYK color for stroking operations
4.24
288

k
setcmykcolor
Set CMYK color for nonstroking operations
4.24
288

l
lineto
Append straight line segment to path
4.9
226

m
moveto
Begin new subpath
4.9
226

M
setmiterlimit
Set miter limit
4.7
219

MP
(PDF 1.2) Define marked-content point
10.7
851
n
End path without filling or stroking
4.10
230

q
gsave
Save graphics state
4.7
219

Q
grestore
Restore graphics state
4.7
219

re
Append rectangle to path
4.9
227

RG
setrgbcolor
Set RGB color for stroking operations
4.24
288

rg
setrgbcolor
Set RGB color for nonstroking operations
4.24
288

ri
Set color rendering intent
4.7
219

s
closepath, stroke
Close and stroke path
4.10
230

S
stroke
Stroke path
4.10
230

SC
setcolor
(PDF 1.1) Set color for stroking operations
4.24
287

sc
setcolor
(PDF 1.1) Set color for nonstroking operations
4.24
288

SCN
setcolor
(PDF 1.2) Set color for stroking operations (ICCBased and special color spaces)
4.24
288

scn
setcolor
(PDF 1.2) Set color for nonstroking operations (ICCBased and special color spaces)
4.24
288

sh
shfill
(PDF 1.3) Paint area defined by shading pattern
4.27
303

T*
Move to start of next text line
5.5
406

Tc
Set character spacing
5.2
398

Td
Move text position
5.5
406

TD
Move text position and set leading
5.5
406

Tf
selectfont
Set text font and size
5.2
398

Tj
show
Show text
5.6
407

TJ
Show text, allowing individual glyph positioning
5.6
408

TL
Set text leading
5.2
398

Tm
Set text matrix and text line matrix
5.5
406

Tr
Set text rendering mode
5.2
398

Ts
Set text rise
5.2
398

Tw
Set word spacing
5.2
398

Tz
Set horizontal text scaling
5.2
398

v
curveto
Append curved segment to path (initial point replicated)
4.9
226

w
setlinewidth
Set line width
4.7
219

W
clip
Set clipping path using nonzero winding number rule
4.11
235

W*
eoclip
Set clipping path using even-odd rule
4.11
235

y
curveto
Append curved segment to path (final point replicated)
4.9
226

'
Move to next line and show text
5.6
407

"
Set word and character spacing, move to next line, and show text
5.6
407
'''


paser = Parser( declaration, 'EXPRESSION' )

data = 'q\nBT\n/F1 24 Tf\n24 TL\n1 0 0.2126 1 50 700 Tm\n(\x00+\x00H\x00O\x00O\x00R\x00\x03\x00Z\x00R\x00U\x00O\x00G\x00\x04\x00\x03\x04L+\x82\x05\x96\x0f\xb3\x00\x03\x00\x04)Tj\n1 0 0.2126 1 50 676 Tm\n(\x00\x0b\x00V\x00D\x00\\\\\x00V\x00\x03\x003\x00\\\\\x00W\x00K\x00R\x00Q\x00\x0c)Tj\nET\nQ\n0.5335 0.8458 -0.8458 0.5335 88.5386 11.0368 cm\n3.7611 w\nBT\n/F2 125.3695 Tf\n1 Tr\n0 TL\n0 0 Td\n(zzzPsgiolePfrp)Tj\n1 w\nET\n'

pos = 0
success = 1
while( success ):
    success, tree, nchar = paser.parse( data[pos:] )
    print '----'
    print data[pos:pos+nchar]
    pos += nchar
    print tree
    print

pdfopers = [ l.strip() for l in pdfoperators.strip().splitlines() ]
els = [ i for i, l in enumerate(pdfopers) if l == '']
pdfopers = [ pdfopers[i+1:j] for i,j in zip([-1]+els,els+[None]) ]

psopers = [ op for op in pdfopers if len(op) == 5 ]
psopers = [ x.strip() for op in psopers for x in op[1].strip().split(',') ]
psopers = list(set(psopers))
psopers.sort()
print '\r\n'.join(psopers)

















