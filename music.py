
from pyquery import PyQuery as pq
import urllib

d = pq('http://www.kamiro.net/diary/info_2761.shtml')
playlists = d("embed")
playlists = [ pq(plist).attr("src") for plist in playlists ]
print playlists
playlists = [ urllib.urlopen(plist).geturl() for plist in playlists ]
playlists = [ plist.split('?',1)[1] for plist in playlists ]
playlists = [ dict( item.split('=',1) for item in plist.split('&') ) for plist in playlists ]
playlists = [ plist['xml'] for plist in playlists ]
playlists = [ urllib.unquote(plist) for plist in playlists ]
print playlists


p = pq('<p class="hello">Hi</p><p>Bye</p>')('p')
#print p.attr.id
print p