

from string import Template


showfun = '''
<li class= "optitem" width="100%%">
  <div style="float: left; width: 20px">&nbsp;</div>
  <a onclick="server.spring()" python="%s" href="#" width="100%%">%s</a>
</li>
'''

#hr = '''<HR>'''

jsonlib = r'''
if (!this.JSON) {
    this.JSON = {};
}

(function () {
    "use strict";

    function f(n) {
        // Format integers to have at least two digits.
        return n < 10 ? '0' + n : n;
    }

    if (typeof Date.prototype.toJSON !== 'function') {

        Date.prototype.toJSON = function (key) {

            return isFinite(this.valueOf()) ?
                   this.getUTCFullYear()   + '-' +
                 f(this.getUTCMonth() + 1) + '-' +
                 f(this.getUTCDate())      + 'T' +
                 f(this.getUTCHours())     + ':' +
                 f(this.getUTCMinutes())   + ':' +
                 f(this.getUTCSeconds())   + 'Z' : null;
        };

        String.prototype.toJSON =
        Number.prototype.toJSON =
        Boolean.prototype.toJSON = function (key) {
            return this.valueOf();
        };
    }

    var cx = /[\u0000\u00ad\u0600-\u0604\u070f\u17b4\u17b5\u200c-\u200f\u2028-\u202f\u2060-\u206f\ufeff\ufff0-\uffff]/g,
        escapable = /[\\\"\x00-\x1f\x7f-\x9f\u00ad\u0600-\u0604\u070f\u17b4\u17b5\u200c-\u200f\u2028-\u202f\u2060-\u206f\ufeff\ufff0-\uffff]/g,
        gap,
        indent,
        meta = {    // table of character substitutions
            '\b': '\\b',
            '\t': '\\t',
            '\n': '\\n',
            '\f': '\\f',
            '\r': '\\r',
            '"' : '\\"',
            '\\': '\\\\'
        },
        rep;


    function quote(string) {

// If the string contains no control characters, no quote characters, and no
// backslash characters, then we can safely slap some quotes around it.
// Otherwise we must also replace the offending characters with safe escape
// sequences.

        escapable.lastIndex = 0;
        return escapable.test(string) ?
            '"' + string.replace(escapable, function (a) {
                var c = meta[a];
                return typeof c === 'string' ? c :
                    '\\u' + ('0000' + a.charCodeAt(0).toString(16)).slice(-4);
            }) + '"' :
            '"' + string + '"';
    }


    function str(key, holder) {

// Produce a string from holder[key].

        var i,          // The loop counter.
            k,          // The member key.
            v,          // The member value.
            length,
            mind = gap,
            partial,
            value = holder[key];

// If the value has a toJSON method, call it to obtain a replacement value.

        if (value && typeof value === 'object' &&
                typeof value.toJSON === 'function') {
            value = value.toJSON(key);
        }

// If we were called with a replacer function, then call the replacer to
// obtain a replacement value.

        if (typeof rep === 'function') {
            value = rep.call(holder, key, value);
        }

// What happens next depends on the value's type.

        switch (typeof value) {
        case 'string':
            return quote(value);

        case 'number':

// JSON numbers must be finite. Encode non-finite numbers as null.

            return isFinite(value) ? String(value) : 'null';

        case 'boolean':
        case 'null':

// If the value is a boolean or null, convert it to a string. Note:
// typeof null does not produce 'null'. The case is included here in
// the remote chance that this gets fixed someday.

            return String(value);

// If the type is 'object', we might be dealing with an object or an array or
// null.

        case 'object':

// Due to a specification blunder in ECMAScript, typeof null is 'object',
// so watch out for that case.

            if (!value) {
                return 'null';
            }

// Make an array to hold the partial results of stringifying this object value.

            gap += indent;
            partial = [];

// Is the value an array?

            if (Object.prototype.toString.apply(value) === '[object Array]') {

// The value is an array. Stringify every element. Use null as a placeholder
// for non-JSON values.

                length = value.length;
                for (i = 0; i < length; i += 1) {
                    partial[i] = str(i, value) || 'null';
                }

// Join all of the elements together, separated with commas, and wrap them in
// brackets.

                v = partial.length === 0 ? '[]' :
                    gap ? '[\n' + gap +
                            partial.join(',\n' + gap) + '\n' +
                                mind + ']' :
                          '[' + partial.join(',') + ']';
                gap = mind;
                return v;
            }

// If the replacer is an array, use it to select the members to be stringified.

            if (rep && typeof rep === 'object') {
                length = rep.length;
                for (i = 0; i < length; i += 1) {
                    k = rep[i];
                    if (typeof k === 'string') {
                        v = str(k, value);
                        if (v) {
                            partial.push(quote(k) + (gap ? ': ' : ':') + v);
                        }
                    }
                }
            } else {

// Otherwise, iterate through all of the keys in the object.

                for (k in value) {
                    if (Object.hasOwnProperty.call(value, k)) {
                        v = str(k, value);
                        if (v) {
                            partial.push(quote(k) + (gap ? ': ' : ':') + v);
                        }
                    }
                }
            }

// Join all of the member texts together, separated with commas,
// and wrap them in braces.

            v = partial.length === 0 ? '{}' :
                gap ? '{\n' + gap + partial.join(',\n' + gap) + '\n' +
                        mind + '}' : '{' + partial.join(',') + '}';
            gap = mind;
            return v;
        }
    }

// If the JSON object does not yet have a stringify method, give it one.

    if (typeof JSON.stringify !== 'function') {
        JSON.stringify = function (value, replacer, space) {

// The stringify method takes a value and an optional replacer, and an optional
// space parameter, and returns a JSON text. The replacer can be a function
// that can replace values, or an array of strings that will select the keys.
// A default replacer method can be provided. Use of the space parameter can
// produce text that is more easily readable.

            var i;
            gap = '';
            indent = '';

// If the space parameter is a number, make an indent string containing that
// many spaces.

            if (typeof space === 'number') {
                for (i = 0; i < space; i += 1) {
                    indent += ' ';
                }

// If the space parameter is a string, it will be used as the indent string.

            } else if (typeof space === 'string') {
                indent = space;
            }

// If there is a replacer, it must be a function or an array.
// Otherwise, throw an error.

            rep = replacer;
            if (replacer && typeof replacer !== 'function' &&
                    (typeof replacer !== 'object' ||
                     typeof replacer.length !== 'number')) {
                throw new Error('JSON.stringify');
            }

// Make a fake root object containing our value under the key of ''.
// Return the result of stringifying the value.

            return str('', {'': value});
        };
    }


// If the JSON object does not yet have a parse method, give it one.

    if (typeof JSON.parse !== 'function') {
        JSON.parse = function (text, reviver) {

// The parse method takes a text and an optional reviver function, and returns
// a JavaScript value if the text is a valid JSON text.

            var j;

            function walk(holder, key) {

// The walk method is used to recursively walk the resulting structure so
// that modifications can be made.

                var k, v, value = holder[key];
                if (value && typeof value === 'object') {
                    for (k in value) {
                        if (Object.hasOwnProperty.call(value, k)) {
                            v = walk(value, k);
                            if (v !== undefined) {
                                value[k] = v;
                            } else {
                                delete value[k];
                            }
                        }
                    }
                }
                return reviver.call(holder, key, value);
            }


// Parsing happens in four stages. In the first stage, we replace certain
// Unicode characters with escape sequences. JavaScript handles many characters
// incorrectly, either silently deleting them, or treating them as line endings.

            text = String(text);
            cx.lastIndex = 0;
            if (cx.test(text)) {
                text = text.replace(cx, function (a) {
                    return '\\u' +
                        ('0000' + a.charCodeAt(0).toString(16)).slice(-4);
                });
            }

// In the second stage, we run the text against regular expressions that look
// for non-JSON patterns. We are especially concerned with '()' and 'new'
// because they can cause invocation, and '=' because it can cause mutation.
// But just to be safe, we want to reject all unexpected forms.

// We split the second stage into 4 regexp operations in order to work around
// crippling inefficiencies in IE's and Safari's regexp engines. First we
// replace the JSON backslash pairs with '@' (a non-JSON character). Second, we
// replace all simple value tokens with ']' characters. Third, we delete all
// open brackets that follow a colon or comma or that begin the text. Finally,
// we look to see that the remaining characters are only whitespace or ']' or
// ',' or ':' or '{' or '}'. If that is so, then the text is safe for eval.

            if (/^[\],:{}\s]*$/
.test(text.replace(/\\(?:["\\\/bfnrt]|u[0-9a-fA-F]{4})/g, '@')
.replace(/"[^"\\\n\r]*"|true|false|null|-?\d+(?:\.\d*)?(?:[eE][+\-]?\d+)?/g, ']')
.replace(/(?:^|:|,)(?:\s*\[)+/g, ''))) {

// In the third stage we use the eval function to compile the text into a
// JavaScript structure. The '{' operator is subject to a syntactic ambiguity
// in JavaScript: it can begin a block or an object literal. We wrap the text
// in parens to eliminate the ambiguity.

                j = eval('(' + text + ')');

// In the optional fourth stage, we recursively walk the new structure, passing
// each name/value pair to a reviver function for possible transformation.

                return typeof reviver === 'function' ?
                    walk({'': j}, '') : j;
            }

// If the text is not JSON parseable, then a SyntaxError is thrown.

            throw new SyntaxError('JSON.parse');
        };
    }
}());
'''


maincss = r'''
body  {
    font: 90% Arial, Verdana, Helvetica, sans-serif;
    height: 100%;
    background: #FFFFFF; 
    margin: 0;
    padding: 0;
    text-align: center; 
    color: #000000;
}

.twoColHybLt #toptip {
    position:absolute; 
    z-index:100;
}

.twoColHybLt #main_toolbar {
    width: auto;
    text-align: right; 
    margin: 0;
    border-bottom: 1px solid #C2CFF1;
    overflow:auto;
    height: 20px;
}

.twoColHybLt #main_title {
    font: 120% Arial;
    width: auto;
    text-align: left;
    margin: 0;
    overflow:auto;
    height: 70px;
}

.twoColHybLt #container {
    width: auto;  
    border: 0px none #000000;
    text-align: left; 
    margin-top: 0;
    margin-right: 0px;
    margin-bottom: 0;
    margin-left: 0px;
    overflow:auto;
} 

.twoColHybLt #sidebar {
    float: left;
    width: 18em;
    padding-right: 0;
    padding-left: 0;
    overflow: auto;
}

.twoColHybLt #splitbar {
    float: left;
    width: 8px;
    background: #EBEFF9; 
    padding-right: 0;
    padding-left: 0;
    overflow: auto;
    border-left: 1px solid #C2CFF1;
}

.twoColHybLt #splitbar:hover {
    background: #C2CFF1; 
}

.twoColHybLt #sidebar h3,
.twoColHybLt #sidebar p {
    margin-left: 10px; 
    margin-right: 10px;
}

.twoColHybLt #mainContent { 
    margin: 0 0 0 13em; 
}

#mainContent #tabcontent {
    overflow: auto;
}

.twoColHybLt #topbar {
    font: 170% arial;
    width: auto;
    height: 30px;
    background: #C2CFF1;
    overflow: auto;
    padding: 0 10px 0 10px;
}

.twoColHybLt #argbar {
    font: 120% arial;
    width: auto;
    height: auto !important; height: 30px; min-height: 30px;
    text-align: left;
    background: #EBEFF9;
    border-bottom: 1px solid #C2CFF1;
    overflow: auto;
    padding: 0 10px 0 10px;
}


.opts {
    padding: 5px 0px 5px 0px;
    margin: 0;
    border-top: 1px solid #C2CFF1;
}

.opts span {
    padding-left: 5px;
    margin-bottom: 25px;
    font-weight: bold;
}

.optitem {
    list-style-type:none;
    padding-right: 0;
    padding-left: 0;
}

.optitem:hover{
    background: #FFFFAA;
}

.optitem a {
    text-decoration: none;
    color: #3f3f3f;
}

.fltrt {
    float: right;
    margin-left: 8px;
}

.fltlft {
    float: left;
    margin-right: 8px;
}

.clearfloat {
    clear:both;
    height: 100%;
    font-size: 1px;
    line-height: 0px;
}

html { 
    height:100%;
}
'''

maincss = maincss + '''

.ep-table {
    padding: 0;
    margin: 0;
}

caption {
    padding: 0 0 5px 0;
    width: 700px;     
    font: italic 11px "Trebuchet MS", Verdana, Arial, Helvetica, sans-serif;
    text-align: right;
}

th {
    font: bold 11px "Trebuchet MS", Verdana, Arial, Helvetica, sans-serif;
    color: #4f6b72;
    border-right: 1px solid #C1DAD7;
    border-bottom: 1px solid #C1DAD7;
    border-top: 1px solid #C1DAD7;
    letter-spacing: 2px;
    text-align: left;
    padding: 6px 6px 6px 12px;
    background: #CAE8EA;
    width: 30px;
}

th.nobg {
    border-top: 0;
    border-left: 0;
    border-right: 1px solid #C1DAD7;
    background: none;
}

td {
    border-right: 1px solid #C1DAD7;
    border-bottom: 1px solid #C1DAD7;
    background: #fff;
    padding: 6px 6px 6px 12px;
    color: #4f6b72;
}


td.alt {
    background: #F5FAFA;
    color: #797268;
}

th.spec {
    border-left: 1px solid #C1DAD7;
    border-top: 0;
    background: #fff;
    font: bold 10px "Trebuchet MS", Verdana, Arial, Helvetica, sans-serif;
}

th.specalt {
    border-left: 1px solid #C1DAD7;
    border-top: 0;
    background: #f5fafa url(images/bullet2.gif) no-repeat;
    font: bold 10px "Trebuchet MS", Verdana, Arial, Helvetica, sans-serif;
    color: #797268;
}

.ep-bar {
    height: 100%; 
    _position: relative; 
    margin: 0 auto; 
    padding: 1px 1px 1px 1px;
}

.ep-bar-in {
    height: 100%; 
    background-color: #B1D632; 
    position: relative; 
    display: table;
}

.ep-bar-iin{
    _position: absolute; 
    _top: 50%; 
    vertical-align: middle; 
    display: table-cell;
}

.ep-bar-iiin {
    _position: relative; 
    width: 100%; 
    height: 100%; 
    _top: -50%;
}

.ep-number {
    white-space: nowrap;
}

'''


ajaxlib = r'''
function Server() {
    
    this.url = document.URL;
    
    try {
        this.conn = new XMLHttpRequest();
    } catch(exp) {
        this.conn = new ActiveXObject("MSXML2.XMLHTTP.3.0");
    };
    
    this.conn.onreadystatechange = function() 
    {
        if( this.readyState == 4 ) 
        {
            if ( this.status == "200" ) 
            {
                eval( this.responseText ) ;
                tip = document.getElementById("toptip") ;
                tip.style.display = "none" ;
            }
            else
            {
                tip = document.getElementById("toptip") ;
                tip.style.display = "none" ;
                tip.innerHTML = "error catched : " + this.status ;
                tip.style.display = "" ;
            }
        }
    };
    
    this.ajaxcall = function( content, info ) {
    
        ajaxurl = this.url;
        
        if ( info != null )
        {
            tip = document.getElementById("toptip") ;
            tip.style.display = "none" ;
            tip.innerHTML = info ;
            tip.style.display = "" ;
        }
    
        content = JSON.stringify(content);

        this.conn.open( "POST" , ajaxurl , true );
        this.conn.setRequestHeader("Content-Length", content.length);
        this.conn.send( content );
        
    };
    
    this.onload = function() {
    
        var content = { id:null, event:"onload", python:"", 
                        uri:document.URL };
        this.ajaxcall( content, "loading page..." );
    
    };
    
    this.spring = function() {
        
        var ev = window.event || arguments.callee.caller.arguments[0];
        var target = ev.srcElement || ev.target;
        var python = target.getAttribute("python");
        
        if( python == null ) {
            python = "";
        }
        
        var content = { id:target.id, event:ev.type, python:python, 
                        uri:document.URL };
        this.ajaxcall( content, "loading page..." );

    };

    this.ontimer = function() {
        
        var d = document.getElementById( this.id );
        
        if ( d === undefined || d == null ) {
            this.removetimer();
            return;
        }
        
        var content = { id:this.id, event:"timer", python:this.info, 
                        uri:document.URL };
        this.ajaxcall( content, null );
    };
    
    this.settimer = function(info, id) {
        this.info = info;
        this.id = id;
        var _this = this;
        this.timer = setInterval(function(){_this.ontimer();}, 2000 );
    };
    
    this.removetimer = function() {
        clearInterval(this.timer);        
    };
    
};

var server = new Server();
'''

jsothers = r'''
window.onload = function(){
    resize();
    server.onload();
};
window.onresize = resize;
function resize(){
    function $(id){
        return window.document.getElementById(id);
    }
    var doc = window.document;
    var h = Math.max(doc.body.offsetHeight, doc.documentElement.offsetHeight);
    
    h = h - document.getElementById( "main_toolbar" ).offsetHeight;
    h = h - document.getElementById( "main_title" ).offsetHeight;
    
    $("container").style.height = h + "px";
    $("sidebar").style.height = h + "px";
    $("splitbar").style.height = h + "px";
    $("mainContent").style.height = h + "px";
    doc = null;
}
'''

mainhtml = r'''
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
<meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
<title>Monitor</title>
<style type="text/css"> 
$maincss
</style>
<!--[if IE]>
<style type="text/css"> 
.twoColHybLt #sidebar { padding-top: 30px; }
.twoColHybLt #mainContent { zoom: 1; padding-top: 15px; }
</style>
<![endif]-->
<script type="text/javascript">
$ajaxlib
</script>
<script type="text/javascript">
$jsothers
</script>
</head>
<body class="twoColHybLt">
<div id="toptip" style="display:none;">A</div>
<div id="main_toolbar">
Login
</div>
<div id="main_title">
<h3>$title</h3>
</div>
<div id="container">
  <div id="sidebar">
    $funclist
  </div>
  <div id="splitbar">
  </div>
  <div id="mainContent">
    <div id="topbar" ></div>
    <div id="argbar" ></div>
    <div id="contentzone" ></div>
  </div>
</div>
</body>
</html>
'''

mainhtml = Template(mainhtml)




from Al import easydoc
import json
from pprint import pprint
from urlparse import urlparse
import eprint
import xml.sax.saxutils

class EasyWeb( object ):
    
    def __init__( self, title = None ):
        
        self.title = title or "EasyWeb"
        
        self.methods = dict( ( k[4:], getattr( self, k ) ) for k in dir(self) 
                             if k.startswith('web_') )
        
        self.respmakers = dict( ( k[5:], getattr( self, k ) ) for k in dir(self) 
                             if k.startswith('resp_') )
        
        self.methods[''] = self._web_default
        self.methods[None] = self.main_page
        
        self.methods_meta = dict( ( k, easydoc.parse( v.__doc__, 'object_ex' ) ) 
                                  for k, v in self.methods.items() )
        
        #pprint( self.methods_meta )
        
        self.mp = self.make_mainpage()
        
    def make_mainpage( self ):
        '''
        '''
        
        funclist = [ ( k, v.get( 'name', k), v.get('group', '') ) 
                     for k, v in self.methods_meta.items() if k ]
        
        grps = set( g for f, n, g in funclist )
        funclist = [ '\n'.join( 
                       [ showfun % (f, n) for f, n, _g in funclist if _g == g ]
                    ) for g in grps ]
        
        grps = [ ( ( '<span>' + g + '</span>\n' ) if g else '' )
                 for g in grps ]
        
        funclist = [ '<ul class="opts">' + g + fl + '</ul>' 
                     for g , fl in zip( grps, funclist ) ]
        funclist = '\n'.join(funclist)
        
        #return mainhtml % ( 'Monitor', funlist )
        return mainhtml.safe_substitute( title = self.title,
                                         funclist = funclist,
                                         
                                         jsothers = jsothers,
                                         ajaxlib = ajaxlib,
                                         maincss = maincss,
                                       )
        
    def run( self, env, start_response ):
        
        uri = env['PATH_INFO']
        qs = env['QUERY_STRING']
        
        work_n = None
        args = []
        
        if env['REQUEST_METHOD'] == 'GET' :
            
            page = uri.split('#',1)[0]
            if page != '/' :
                start_response( '404 NOT FOUND', [] )
                #yield resp.get( 'body', '' )
                return
            
        elif env['REQUEST_METHOD'] == 'POST' :
            
            clen = int(env['CONTENT_LENGTH'])
            req = json.loads( env['wsgi.input'].read(clen) )
            
            if req['event'] == 'onload' :
                
                page = ( uri.split('#',1)+[''] )[1] if 'uri' not in req else \
                                                urlparse(req['uri']).fragment
                                                
                print page
                
                if page != '' :
                    page = page.split('/')
                    work_n, args = page[0], page[1:]
                    #work = self.methods[work_n]
                else :
                    work_n = ''
                
            else :
                
                work_n = req['python']
                args = []
        
        else :
            
            raise Exception, 'not supported'
        
        work = self.methods[work_n]
        rtmk = self.respmakers[ self.methods_meta[work_n]['showtype'] ]
        
        resp = rtmk( work( None, *args ) )
        
        start_response( '200 OK', [] )
        
        yield resp
        
        if work_n is None :
            return
        
        yield '''document.getElementById('topbar').innerHTML = '%s';''' \
                    % ( str(self.methods_meta[work_n].get('name', work_n )), )
        
        if req['event'] == 'onload' :
            return
        
        yield '''window.location.href=window.location.href+"%s";''' \
                    %( str(work_n), )
        
        showargs = self.methods_meta[work_n].get( "arguments", {} )
        showargs = self.make_args( showargs )
        
        yield '''document.getElementById('argbar').innerHTML = '%s';''' \
                                       % ( showargs.encode('string_escape'), )
        
    def make_args( self, args ):
        
        r = [ getattr(self,'arg_'+v[''] )( k, v ) for k, v in args.items() ]
        r = [ k + i for k, i in zip(args.keys(), r)]
        r = '<br />'.join(r)
        
        return r
    
    def arg_dropdownlist( self, name, arg ):
        
        items = eval( arg['items'] )
        default = eval( arg.get( 'default','None') )
        
        r = [ '<option value="%s" %s >%s</option>' \
                     % ( i, 'selected="selected"' if i == default else '', i) 
              for i in items ]
        
        r = '\n'.join(r)
        r = ( '<select name="%s">\n' % (name,) ) + r + '\n</select>'
        
        return r
    
    def arg_text( self, name, arg ):
        
        default = eval( arg.get( 'default','""') )
        
        r = '<input type="test" name="%s" value="%s" />' % ( name, default)
        
        return r
    
    def serve( self, port, engine = '' ):
        
        if engine == '' :
            
            from wsgiref.simple_server import make_server
            
            httpd = make_server( '', port, self.run )
            print "Serving HTTP on port %d..." % ( port, )
            
            # Respond to requests until process is killed
            httpd.serve_forever()
            
            return
        
        elif engine == 'flup.fastcgi' :
            
            from flup.server.fcgi_fork import WSGIServer
            
            # Respond to requests until process is killed
            WSGIServer( wflow.run , bindAddress=port ).run()
            
            return
            
        raise Exception, 'unsupported engine.'
    
    def main_page( self, user ):
        '''
        showtype: html
        '''
        
        return self.mp
    
    def _web_default( self, user ):
        '''
        showtype: text
        '''
        
        return "hello world"
        
    def resp_html( self, r ):
        
        return r
        
    def resp_raw( self, r ):
        
        if type(r) == type(u''):
            r = r.encoding('utf-8')
        
        if type(r) != type(''):
            r = str(r)
        
        return '''document.getElementById('contentzone').innerHTML = '%s';''' \
                                               % ( r.encode('string_escape'), )
        
    def resp_text( self, r ):
        
        if type(r) == type(u''):
            r = r.encoding('utf-8')
        
        if type(r) != type(''):
            r = str(r)
        
        r = xml.sax.saxutils.escape(r)
        
        return '''document.getElementById('contentzone').innerHTML = '%s';''' \
                                               % ( r.encode('string_escape'), )
                                                                    
    def resp_table( self, r ):
        
        r = eprint.Table( r, attr={"cellSpacing":0} ).htmlformat()
        
        return self.resp_raw(r)


class EasyWebTest( EasyWeb ):
    
    def web_test( self, user ):
        '''
        arguments:
            input1: dropdownlist
                items: ['table','list']
                default: 'table'
            input2: text
                default: 'hello'
        showtype: text
        '''
        
        return
        
    def web_test2( self, user ):
        '''
        showtype: table
        name: hello world
        group: Hello
        '''
        
        d = [ { 'colA' : 'A.1.alpha\r\nA.1.beta' ,
                'colB' : [1,2],
                'colC' : 'B.1.alpha\r\nB.1.beta\r\nB.1.gamma\r\nB.1.delta',
              },
              { 'colA' : 'A.2.alpha\r\nA.2.beta' ,
                'colB' : [0.1,0.9,0.3,0,-1],
                'colC' : [3,0.7,{'B.2.alpha':'z','B.1':'qew' },True,False],
              },
            ]
        
        return d

    def web_test3( self, user ):
        '''
        showtype: text
        name: sleep 1 sec
        group: Hello
        '''
        
        import time
        time.sleep(1)
        
        return 'server sleeped 1 sec'

if __name__ == '__main__' :
    
    t = EasyWebTest()
    #print t.methods
    
    t.serve(1088)
    