








# Copy Code from fronttools-2.3

# It used MIT Licenses

# Copyright 1999-2004
# by Just van Rossum, Letterror, The Netherlands.
# 
#                         All Rights Reserved
# 
# Permission to use, copy, modify, and distribute this software and 
# its documentation for any purpose and without fee is hereby granted,
# provided that the above copyright notice appear in all copies and 
# that both that copyright notice and this permission notice appear 
# in supporting documentation, and that the names of Just van Rossum 
# or Letterror not be used in advertising or publicity pertaining to
# distribution of the software without specific, written prior
# permission.

# JUST VAN ROSSUM AND LETTERROR DISCLAIM ALL WARRANTIES WITH
# REGARD TO THIS SOFTWARE, INCLUDING ALL IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS, IN NO EVENT SHALL JUST VAN ROSSUM OR 
# LETTERROR BE LIABLE FOR ANY SPECIAL, INDIRECT OR CONSEQUENTIAL
# DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR
# PROFITS, WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE OR OTHER
# TORTIOUS ACTION, ARISING OUT OF OR IN CONNECTION WITH THE USE OR
# PERFORMANCE OF THIS SOFTWARE.

# just@letterror.com







import types
import struct
import string


t1OperandEncoding = [None] * 256
t1OperandEncoding[0:32] = (32) * ["do_operator"]
t1OperandEncoding[32:247] = (247 - 32) * ["read_byte"]
t1OperandEncoding[247:251] = (251 - 247) * ["read_smallInt1"]
t1OperandEncoding[251:255] = (255 - 251) * ["read_smallInt2"]
t1OperandEncoding[255] = "read_longInt"
assert len(t1OperandEncoding) == 256

t2OperandEncoding = t1OperandEncoding[:]
t2OperandEncoding[28] = "read_shortInt"
t2OperandEncoding[255] = "read_fixed1616"

cffDictOperandEncoding = t2OperandEncoding[:]
cffDictOperandEncoding[29] = "read_longInt"
cffDictOperandEncoding[30] = "read_realNumber"
cffDictOperandEncoding[255] = "reserved"

cffStandardStrings = ['.notdef', 'space', 'exclam', 'quotedbl', 'numbersign', 
        'dollar', 'percent', 'ampersand', 'quoteright', 'parenleft', 'parenright', 
        'asterisk', 'plus', 'comma', 'hyphen', 'period', 'slash', 'zero', 'one', 
        'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'colon', 
        'semicolon', 'less', 'equal', 'greater', 'question', 'at', 'A', 'B', 'C', 
        'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 
        'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z', 'bracketleft', 'backslash', 
        'bracketright', 'asciicircum', 'underscore', 'quoteleft', 'a', 'b', 'c', 
        'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 
        's', 't', 'u', 'v', 'w', 'x', 'y', 'z', 'braceleft', 'bar', 'braceright', 
        'asciitilde', 'exclamdown', 'cent', 'sterling', 'fraction', 'yen', 'florin', 
        'section', 'currency', 'quotesingle', 'quotedblleft', 'guillemotleft', 
        'guilsinglleft', 'guilsinglright', 'fi', 'fl', 'endash', 'dagger', 
        'daggerdbl', 'periodcentered', 'paragraph', 'bullet', 'quotesinglbase', 
        'quotedblbase', 'quotedblright', 'guillemotright', 'ellipsis', 'perthousand', 
        'questiondown', 'grave', 'acute', 'circumflex', 'tilde', 'macron', 'breve', 
        'dotaccent', 'dieresis', 'ring', 'cedilla', 'hungarumlaut', 'ogonek', 'caron', 
        'emdash', 'AE', 'ordfeminine', 'Lslash', 'Oslash', 'OE', 'ordmasculine', 'ae', 
        'dotlessi', 'lslash', 'oslash', 'oe', 'germandbls', 'onesuperior', 
        'logicalnot', 'mu', 'trademark', 'Eth', 'onehalf', 'plusminus', 'Thorn', 
        'onequarter', 'divide', 'brokenbar', 'degree', 'thorn', 'threequarters', 
        'twosuperior', 'registered', 'minus', 'eth', 'multiply', 'threesuperior', 
        'copyright', 'Aacute', 'Acircumflex', 'Adieresis', 'Agrave', 'Aring', 
        'Atilde', 'Ccedilla', 'Eacute', 'Ecircumflex', 'Edieresis', 'Egrave', 
        'Iacute', 'Icircumflex', 'Idieresis', 'Igrave', 'Ntilde', 'Oacute', 
        'Ocircumflex', 'Odieresis', 'Ograve', 'Otilde', 'Scaron', 'Uacute', 
        'Ucircumflex', 'Udieresis', 'Ugrave', 'Yacute', 'Ydieresis', 'Zcaron', 
        'aacute', 'acircumflex', 'adieresis', 'agrave', 'aring', 'atilde', 'ccedilla', 
        'eacute', 'ecircumflex', 'edieresis', 'egrave', 'iacute', 'icircumflex', 
        'idieresis', 'igrave', 'ntilde', 'oacute', 'ocircumflex', 'odieresis', 
        'ograve', 'otilde', 'scaron', 'uacute', 'ucircumflex', 'udieresis', 'ugrave', 
        'yacute', 'ydieresis', 'zcaron', 'exclamsmall', 'Hungarumlautsmall', 
        'dollaroldstyle', 'dollarsuperior', 'ampersandsmall', 'Acutesmall', 
        'parenleftsuperior', 'parenrightsuperior', 'twodotenleader', 'onedotenleader', 
        'zerooldstyle', 'oneoldstyle', 'twooldstyle', 'threeoldstyle', 'fouroldstyle', 
        'fiveoldstyle', 'sixoldstyle', 'sevenoldstyle', 'eightoldstyle', 
        'nineoldstyle', 'commasuperior', 'threequartersemdash', 'periodsuperior', 
        'questionsmall', 'asuperior', 'bsuperior', 'centsuperior', 'dsuperior', 
        'esuperior', 'isuperior', 'lsuperior', 'msuperior', 'nsuperior', 'osuperior', 
        'rsuperior', 'ssuperior', 'tsuperior', 'ff', 'ffi', 'ffl', 'parenleftinferior', 
        'parenrightinferior', 'Circumflexsmall', 'hyphensuperior', 'Gravesmall', 
        'Asmall', 'Bsmall', 'Csmall', 'Dsmall', 'Esmall', 'Fsmall', 'Gsmall', 'Hsmall', 
        'Ismall', 'Jsmall', 'Ksmall', 'Lsmall', 'Msmall', 'Nsmall', 'Osmall', 'Psmall', 
        'Qsmall', 'Rsmall', 'Ssmall', 'Tsmall', 'Usmall', 'Vsmall', 'Wsmall', 'Xsmall', 
        'Ysmall', 'Zsmall', 'colonmonetary', 'onefitted', 'rupiah', 'Tildesmall', 
        'exclamdownsmall', 'centoldstyle', 'Lslashsmall', 'Scaronsmall', 'Zcaronsmall', 
        'Dieresissmall', 'Brevesmall', 'Caronsmall', 'Dotaccentsmall', 'Macronsmall', 
        'figuredash', 'hypheninferior', 'Ogoneksmall', 'Ringsmall', 'Cedillasmall', 
        'questiondownsmall', 'oneeighth', 'threeeighths', 'fiveeighths', 'seveneighths', 
        'onethird', 'twothirds', 'zerosuperior', 'foursuperior', 'fivesuperior', 
        'sixsuperior', 'sevensuperior', 'eightsuperior', 'ninesuperior', 'zeroinferior', 
        'oneinferior', 'twoinferior', 'threeinferior', 'fourinferior', 'fiveinferior', 
        'sixinferior', 'seveninferior', 'eightinferior', 'nineinferior', 'centinferior', 
        'dollarinferior', 'periodinferior', 'commainferior', 'Agravesmall', 
        'Aacutesmall', 'Acircumflexsmall', 'Atildesmall', 'Adieresissmall', 'Aringsmall', 
        'AEsmall', 'Ccedillasmall', 'Egravesmall', 'Eacutesmall', 'Ecircumflexsmall', 
        'Edieresissmall', 'Igravesmall', 'Iacutesmall', 'Icircumflexsmall', 
        'Idieresissmall', 'Ethsmall', 'Ntildesmall', 'Ogravesmall', 'Oacutesmall', 
        'Ocircumflexsmall', 'Otildesmall', 'Odieresissmall', 'OEsmall', 'Oslashsmall', 
        'Ugravesmall', 'Uacutesmall', 'Ucircumflexsmall', 'Udieresissmall', 
        'Yacutesmall', 'Thornsmall', 'Ydieresissmall', '001.000', '001.001', '001.002', 
        '001.003', 'Black', 'Bold', 'Book', 'Light', 'Medium', 'Regular', 'Roman', 
        'Semibold'
]

cffStandardStringCount = 391
assert len(cffStandardStrings) == cffStandardStringCount

def buildOperatorDict(table):
    d = {}
    for op, name, arg, default, conv in table:
        d[op] = (name, arg)
    return d

topDictOperators = [
#    opcode     name                  argument type   default    converter
    ((12, 30), 'ROS',        ('SID','SID','number'), None,      None),
    ((12, 20), 'SyntheticBase',      'number',       None,      None),
    (0,        'version',            'SID',          None,      None),
    (1,        'Notice',             'SID',          None,      None),
    ((12, 0),  'Copyright',          'SID',          None,      None),
    (2,        'FullName',           'SID',          None,      None),
    ((12, 38), 'FontName',           'SID',          None,      None),
    (3,        'FamilyName',         'SID',          None,      None),
    (4,        'Weight',             'SID',          None,      None),
    ((12, 1),  'isFixedPitch',       'number',       0,         None),
    ((12, 2),  'ItalicAngle',        'number',       0,         None),
    ((12, 3),  'UnderlinePosition',  'number',       None,      None),
    ((12, 4),  'UnderlineThickness', 'number',       50,        None),
    ((12, 5),  'PaintType',          'number',       0,         None),
    ((12, 6),  'CharstringType',     'number',       2,         None),
    ((12, 7),  'FontMatrix',         'array',  [0.001,0,0,0.001,0,0],  None),
    (13,       'UniqueID',           'number',       None,      None),
    (5,        'FontBBox',           'array',  [0,0,0,0],       None),
    ((12, 8),  'StrokeWidth',        'number',       0,         None),
    (14,       'XUID',               'array',        None,      None),
    ((12, 21), 'PostScript',         'SID',          None,      None),
    ((12, 22), 'BaseFontName',       'SID',          None,      None),
    ((12, 23), 'BaseFontBlend',      'delta',        None,      None),
    ((12, 31), 'CIDFontVersion',     'number',       0,         None),
    ((12, 32), 'CIDFontRevision',    'number',       0,         None),
    ((12, 33), 'CIDFontType',        'number',       0,         None),
    ((12, 34), 'CIDCount',           'number',       8720,      None),
    (15,       'charset',            'number',       0,         None),
    ((12, 35), 'UIDBase',            'number',       None,      None),
    (16,       'Encoding',           'number',       0,         None),
    (18,       'Private',       ('number','number'), None,      None),
    ((12, 37), 'FDSelect',           'number',       None,      None),
    ((12, 36), 'FDArray',            'number',       None,      None),
    (17,       'CharStrings',        'number',       None,      None),
]


class ByteCodeBase:
    
    def read_byte(self, b0, data, index):
        return b0 - 139, index
    
    def read_smallInt1(self, b0, data, index):
        b1 = ord(data[index])
        return (b0-247)*256 + b1 + 108, index+1
    
    def read_smallInt2(self, b0, data, index):
        b1 = ord(data[index])
        return -(b0-251)*256 - b1 - 108, index+1
    
    def read_shortInt(self, b0, data, index):
        bin = data[index] + data[index+1]
        value, = struct.unpack(">h", bin)
        return value, index+2
    
    def read_longInt(self, b0, data, index):
        bin = data[index] + data[index+1] + data[index+2] + data[index+3]
        value, = struct.unpack(">l", bin)
        return value, index+4
    
    def read_fixed1616(self, b0, data, index):
        bin = data[index] + data[index+1] + data[index+2] + data[index+3]
        value, = struct.unpack(">l", bin)
        return value / 65536.0, index+4
    
    def read_realNumber(self, b0, data, index):
        number = ''
        while 1:
            b = ord(data[index])
            index = index + 1
            nibble0 = (b & 0xf0) >> 4
            nibble1 = b & 0x0f
            if nibble0 == 0xf:
                break
            number = number + realNibbles[nibble0]
            if nibble1 == 0xf:
                break
            number = number + realNibbles[nibble1]
        return float(number), index
        
        
        
class DictDecompiler(ByteCodeBase):
    
    operandEncoding = cffDictOperandEncoding
    
    def __init__(self, strings):
        self.stack = []
        self.strings = strings
        self.dict = {}
    
    def getDict(self):
        assert len(self.stack) == 0, "non-empty stack"
        return self.dict
    
    def decompile(self, data):
        index = 0
        lenData = len(data)
        push = self.stack.append
        while index < lenData:
            b0 = ord(data[index])
            index = index + 1
            code = self.operandEncoding[b0]
            handler = getattr(self, code)
            value, index = handler(b0, data, index)
            if value is not None:
                push(value)
    
    def pop(self):
        value = self.stack[-1]
        del self.stack[-1]
        return value
    
    def popall(self):
        all = self.stack[:]
        del self.stack[:]
        return all
    
    def do_operator(self, b0, data, index):
        if b0 == 12:
            op = (b0, ord(data[index]))
            index = index+1
        else:
            op = b0
        operator, argType = self.operators[op]
        self.handle_operator(operator, argType)
        return None, index
    
    def handle_operator(self, operator, argType):
        if type(argType) == type(()):
            value = ()
            for i in range(len(argType)-1, -1, -1):
                arg = argType[i]
                arghandler = getattr(self, "arg_" + arg)
                value = (arghandler(operator),) + value
        else:
            arghandler = getattr(self, "arg_" + argType)
            value = arghandler(operator)
        self.dict[operator] = value
    
    def arg_number(self, name):
        return self.pop()
    
    def arg_SID(self, name):
        
        SID = self.pop()
        
        if SID < cffStandardStringCount:
            return cffStandardStrings[SID]
        else:
            return self.strings[SID - cffStandardStringCount]
            
    def arg_array(self, name):
        return self.popall()
    
    def arg_delta(self, name):
        out = []
        current = 0
        for v in self.popall():
            current = current + v
            out.append(current)
        return out

        
        
class TopDict( DictDecompiler ):
    operators = buildOperatorDict(topDictOperators)

        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
