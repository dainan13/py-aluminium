
from pyquery import PyQuery as pq
import urllib


def get_playlists( pageurl ):
    
    d = pq( pageurl )
    playlists = d("embed")
    playlists = [ pq(plist).attr("src") for plist in playlists ]
    playlists = [ urllib.urlopen(plist).geturl() for plist in playlists ]
    playlists = [ plist.split('?',1)[1] for plist in playlists ]
    playlists = [ dict( item.split('=',1) for item in plist.split('&') ) for plist in playlists ]
    playlists = [ plist['xml'] for plist in playlists ]
    playlists = [ urllib.unquote(plist) for plist in playlists ]
    
    return playlists

def get_tracks( playlist ):
    
    #d = pq( playlist, parser='html_fragments' )
    c = urllib.urlopen(playlist).read()
    #c = urllib.urlopen(playlist).read().replace('<![CDATA[','').replace(']]>','')
    #print c
    d = pq( c, parser='html_fragments' )
    
    titles = d('title')
    print len(titles)
    titles = [ t.text_content() for t in titles ]
    
    tracks = d('location')
    tracks = [ t.text_content() for t in tracks ]
    
    return titles[0], zip(titles[1:],tracks)

if __name__ == '__main__' :
    
    playlists = get_playlists('http://www.kamiro.net/diary/info_2761.shtml')
    
    for plist in playlists :
        print get_tracks(plist)