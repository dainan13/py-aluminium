# -*- coding: utf-8 -*-

import sys

__all__ = ['TextWrapper', 'wrap', 'fill', 'dedent']

class TextWrapper(object):
    
    x = ['Word','Compound','Blank','Empty']
    y = ['space','initials','tails','letter','terminal']
    
    statmachine = {
        'EL':('W',False),
        'EI':('C',False),
        'ET':('A',False),
        'Ei':('C',False),
        'Et':('A',False),
        'ES':('E',False),
        'EH':('S',False),
        
        'CL':('W',False),
        'CI':('C',False),
        'CT':('A',False),
        'Ci':('C',False),
        'Ct':('A',False),
        'CS':('E',True),
        'CH':('S',False),

        'AL':('W',True),
        'AI':('C',True),
        'AT':('A',False),
        'Ai':('W',False),
        'At':('W',False),
        'AS':('A',False),
        'AH':('S',True),
        
        'WL':('W',False),
        'WI':('C',True),
        'WT':('A',False),
        'Wi':('W',False),
        'Wt':('W',False),
        'WS':('E',True),
        'WH':('S',True),
        
        'SL':('W',True),
        'SI':('C',True),
        'ST':('A',False),
        'Si':('C',True),
        'St':('W',False),
        'SS':('E',True),
        'SH':('S',True),
    }
    
    initials = u'([{<$'\
               u'￥（【“‘《'
               
    tails = u'!%)]:;>?,.'\
            u'·！…）】、：；”’》，。？'
    
    def __init__(self,
                 width=70,
                 initial_indent="",
                 subsequent_indent="",
                 expand_tabs=True,
                 replace_whitespace=True,
                 fix_sentence_endings=False,
                 break_long_words=True,
                 drop_whitespace=True,
                 break_on_hyphens=True):
        self.width = width
        self.initial_indent = initial_indent
        self.subsequent_indent = subsequent_indent
        self.expand_tabs = expand_tabs
        self.replace_whitespace = replace_whitespace
        self.fix_sentence_endings = fix_sentence_endings
        self.break_long_words = break_long_words
        self.drop_whitespace = drop_whitespace
        self.break_on_hyphens = break_on_hyphens
        self.eliminate_error = False
        
    @classmethod
    def chrtype( cls, c ):
        
        if c == ' ':
            return 'S'
        elif c in cls.initials :
            return 'i' if ord(c) < 256 else 'I'
        elif c in cls.tails :
            return 't' if ord(c) < 256 else 'T'
        elif ord(c) < 256 and c != '-' :
            return 'L'
        else :
            return 'H'
    
    def _split_iter( self, inp ):
        
        s = 'E'
        start = 0
        cur = 0
        
        i = 0
        for i, c in enumerate(inp) :
            
            ctype = self.chrtype(c)
            s, ending = self.statmachine[s+ctype]
            
            if ending :
                width = self.getwordwidth(inp, start, cur+1 )
                yield start, cur+1, i, width
                start = i
                
            if ctype != 'S' :
                cur = i
            
        width = self.getwordwidth(inp,start,cur+1)
        yield start, cur+1, i, width
        
        return
    
    @staticmethod
    def getwordwidth( w, st, ed ):
        return sum( [ (1 if ord(c) < 256 else 2) for c in w[st:ed] ] )
    
    @staticmethod
    def getwordwidth_iter( w, st, ed ):
        
        for c in w[st:ed] :
            yield (1 if ord(c) < 256 else 2)
        
        return
    
    @classmethod
    def _wrap_long_word( cls, word, width ):
        
        anticur = width
        start = 0
        
        yield 0, len(word), width
        
        #for i, c in enumerate(word) :
        #    
        #    w = cls.getchrwidth(c)
        #    anticur -= w
        #    
        #    if anticur < 0 :
        #        yield start, i+1, None
        #        
        #        start = i
        #        anticur = width - w
        #    
        #yield start, i+1, anticur
        
        return
    
    def wrap( self, text, width=70 ):
        
        r = []
        l = []
        
        for i in self._wrap_iter( text, width ):
            if i == None :
                r.append(''.join(l))
                l = []
        
        return r

    def fill( self, text, width=70 ):
        return '\n'.join( self.wrap( text, width ) )
        
    def show( self, text, width=70 ):
        
        for i in self._wrap_iter( text, width ):
            sys.stdout.write(i if i!= None else '\n')
        
        return
    
    def _wrap_iter( self, text, width=70, maxwidth=None ):
        
        anticur = width
        
        leave = (maxwidth-width) if maxwidth else 0
        leave = max(0,leave)
        
        ln_st = None
        ln_ed = None
        
        for wst, bst, ed, ww in self._split_iter(text):
            
            if self.eliminate_error and ( anticur+leave < ww or anticur < 0 ):
                anticur = width - self.getwordwidth( text, ln_st, ln_ed )
                
            if anticur+leave < ww or anticur < 0 :
                
                yield None
                ln_st = ln_ed = None
                anticur = width
                
                if ww > width :
                    
                    word = text[wst:bst]
                    
                    for subst, subed, subcur in self._wrap_long_word( word, width ):
                        
                        yield word[subst:subed]
                        #ln_st = ln_st or subst
                        ln_st = ln_st if ln_st is not None else wst
                        ln_ed = subed
                        if subcur == None:
                            yield None
                            ln_st = ln_ed = None
                        anticur = subcur
                        
                else :
                    
                    yield text[wst:bst]
                    #ln_st = ln_st or wst
                    ln_st = ln_st if ln_st is not None else wst
                    ln_ed = bst
                    anticur -= ww
                    
            else :
                
                yield text[wst:bst]
                #ln_st = ln_st or wst
                ln_st = ln_st if ln_st is not None else wst
                ln_ed = bst
                anticur -= ww
                
            #blankwidth = ed-bst
            
            #if anticur >= blankwidth :
            #    yield ' '*blankwidth
                
            #anticur -= blankwidth
        
        return
    
    def _line_iter( self, text, width=70, maxwidth=None ):
        
        for txln in text.splitlines() :
            
            ln = []
            
            for i in self._wrap_iter( txln, width, maxwidth ):
                
                if i is not None :
                    ln.append(i)
                else :
                    yield ''.join(ln)
                    ln = []
                    
            if ln != [] :
                yield ''.join(ln)
        
        return
        
        
import re
# the function in follows is copy from textwrap in standard lib 

def wrap(text, width=70, **kwargs):
    """Wrap a single paragraph of text, returning a list of wrapped lines.

    Reformat the single paragraph in 'text' so it fits in lines of no
    more than 'width' columns, and return a list of wrapped lines.  By
    default, tabs in 'text' are expanded with string.expandtabs(), and
    all other whitespace characters (including newline) are converted to
    space.  See TextWrapper class for available keyword args to customize
    wrapping behaviour.
    """
    w = TextWrapper(width=width, **kwargs)
    return w.wrap(text)

def fill(text, width=70, **kwargs):
    """Fill a single paragraph of text, returning a new string.

    Reformat the single paragraph in 'text' to fit in lines of no more
    than 'width' columns, and return a new string containing the entire
    wrapped paragraph.  As with wrap(), tabs are expanded and other
    whitespace characters converted to space.  See TextWrapper class for
    available keyword args to customize wrapping behaviour.
    """
    w = TextWrapper(width=width, **kwargs)
    return w.fill(text)


# -- Loosely related functionality -------------------------------------

_whitespace_only_re = re.compile('^[ \t]+$', re.MULTILINE)
_leading_whitespace_re = re.compile('(^[ \t]*)(?:[^ \t\n])', re.MULTILINE)

def dedent(text):
    """Remove any common leading whitespace from every line in `text`.

    This can be used to make triple-quoted strings line up with the left
    edge of the display, while still presenting them in the source code
    in indented form.

    Note that tabs and spaces are both treated as whitespace, but they
    are not equal: the lines "  hello" and "\thello" are
    considered to have no common leading whitespace.  (This behaviour is
    new in Python 2.5; older versions of this module incorrectly
    expanded tabs before searching for common leading whitespace.)
    """
    # Look for the longest leading string of spaces and tabs common to
    # all lines.
    margin = None
    text = _whitespace_only_re.sub('', text)
    indents = _leading_whitespace_re.findall(text)
    for indent in indents:
        if margin is None:
            margin = indent

        # Current line more deeply indented than previous winner:
        # no change (previous winner is still on top).
        elif indent.startswith(margin):
            pass

        # Current line consistent with and no deeper than previous winner:
        # it's the new winner.
        elif margin.startswith(indent):
            margin = indent

        # Current line and previous winner have no common whitespace:
        # there is no margin.
        else:
            margin = ""
            break

    # sanity check (testing/debugging only)
    if 0 and margin:
        for line in text.split("\n"):
            assert not line or line.startswith(margin), \
                   "line = %r, margin = %r" % (line, margin)

    if margin:
        text = re.sub(r'(?m)^' + margin, '', text)
    return text
        









if __name__ == '__main__' :
    
    tw = TextWrapper()
    
    w = 23
    
    print '-'*w
    
    tw.show( 'The quick brown fox jumps over the lazy dog', w )
    print 
    print 
    
    tw.show( 'The quick brown fox jumps over the lazy dog.', w )
    print 
    print 
    
    tw.show( 'The quick brown fox ( jumps ) over the lazy doooooooooooooooooooooooooog.', w )
    print 
    print 
    
    tw.show( 'A quick movement of the enemy will jeopardize six gunboats.', w )
    print
    print
    
    tw.show( '"Who am taking the ebonics quiz?", the prof jovially axed.', w )
    print
    print
    
    tw.show( 'The quick brown fox jumps over a lazy dog.', w)
    print
    print
    
    tw.show( '   Waaaaaaatch "Jeopardy!", Alex Trebek\'s fun TV quiz game.', w)
    print
    print
    
    tw.show( 'JoBlo\'s movie review of The Yards: Mark Wahlberg, Joaquin Phoenix, Charlize Theron...', w)
    print 
    print
    
    tw.show( u'I sang, and thought I sang very well; '\
             u'but he just looked up into my face with a very '\
             u'quizzical expression, and said, ‘How long have been singing, '\
             u'Mademoiselle?’', w)
    print 
    print
    
    print '-'*w
    
    print
    print
    
    for w in [23,26,29,32] :
    
        print '-'*w
        
        tw.show( u'包含有字母表中所有字母并且言之成义的句子称为全字母句（英语：pangram或holoalphabetic sentence，希腊语：pan gramma（意为“每一个字母”））。'\
                 u'全字母句被用于显示字体和测试打字机。英语中最知名的全字母句是“The quick brown fox jumps over the lazy dog（敏捷的棕色狐狸跳过懒狗身上）”。'\
                 u'一般，有趣的全字母句都很短；写出一个包含有最少重复字母的全字母句是一件富有挑战性的工作。长的全字母句在正确的前提下，显著地富有启迪性，或是很幽默，或是很古怪。'\
                 u'从某种意义上，全字母句是漏字文（英语：Lipogram）的对立物，因为后者在文章中有意不使用一个或几个特定字母。', w )
        print 
        print
        
        print '-'*w
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    