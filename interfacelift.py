#!/usr/bin/env python
import sys
import os
import urllib2
import optparse

try:
    import lxml.html
except ImprotError:
    sys.stderr.write("Needs lxml library.\n")
    sys.exit()


DIRNAME = "interfacelift_wallpapers" #change this to whatever

try:
    os.makedirs(DIRNAME)
    sys.stdout.write("Created dir: %s\n" % DIRNAME)
    os.chdir(DIRNAME)
except OSError, e:
    if e.errno == 17: #Dir exists, we'll just change into it
        os.chdir(DIRNAME)
        sys.stdout.write("Changing dirs: %s\n" % DIRNAME)
    else:
        sys.stderr.write("OSError: %s\n" % e.strerror) #WTF?
        sys.exit()

parser = optparse.OptionParser()

SORTBY = [
    "date",
    "downloads",
    "rating",
    "comments",
    "random"
]

parser.add_option("-r", "--res", action="store", type="string", dest="res", help="The resolution to grab images at in the form: HHHHxWWWW")
parser.add_option("-s", "--sortby", action="store", type="string", dest="sortby", help="Sort wallpapers by (retrieve by): %s" % ", ".join(SORTBY))
parser.add_option("-n", "--number", action="store", type="int", dest="number", help="Stop grabbing when we reached this number.")

(options, args) = parser.parse_args(sys.argv)

if not options.res:
    options.res = '1280x1024' 
if not options.sortby:
    options.sortby = 'date'
if not options.number:
    options.number = 10

BASEURL = "http://interfacelift.com/wallpaper_beta/downloads/%(sort)s/any"
PAGINATED_URL = "http://interfacelift.com/wallpaper_beta/downloads/%(sort)s/any/index%(pagenum)i.html"
IMG_URL = "http://interfacelift.com/wallpaper_beta/grab/%(imgid)s_%(imgname)s_%(imgres)s.jpg" #id_name_resolution.jpg

BUILT_BASEURL = BASEURL % {'sort': options.sortby}

response = urllib2.urlopen(BUILT_BASEURL)

soup = lxml.html.fromstring(response.read())

select = soup.cssselect('select')[0]

select_opts = {}

for el in select.getchildren():
    select_opts[el.get('label').strip() if el.get('label') else None] = [text for text in el.itertext()]

resolutions = []

for value in select_opts.values():
    for v in value:
        resolutions.append(v.split()[0])

if not options.res in resolutions:
    sys.stderr.write("Resolution wasn't found :/\n")
    sys.exit()

def cleanname(name):
    import string
    return name.translate(string.maketrans("", ""), string.punctuation + ' ').lower()

def grab(url, fname):
    if os.path.exists(fname+'.jpg'):
        sys.stdout.write("File %s exists. Skipping.\n" % fname)
        pass
    try:
        headers = {'User-Agent': 'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)'}
        data = urllib2.urlopen(url) 
        f = open(fname+'.jpg', 'wb')
        for d in data:
            f.write(d)
        f.close()
        sys.stdout.write("Grabbed: %s\n" % fname)
    except Exception, e:
        sys.stderr("Error while grabbing: %s\n" % e.strerror)

sys.stdout.write("Grabbing %i wallpapers sorted by %s @ %s resolution... chu chu!\n\n"  % (options.number, options.sortby, options.res))

totalpages = int(soup.find_class('pagenums_bottom')[0].cssselect('a')[-2].text_content())
sys.stdout.write("Total pages: %i\n" % totalpages)
currentpage = 1
grabcount = 0
while True:
    if currentpage == totalpages:
        sys.stdout.write("Exhausted all %i pages. Exiting.\n" % totalpages)
        break

    url = PAGINATED_URL % {'sort': options.sortby, 'pagenum': currentpage}
    response = urllib2.urlopen(url)
    sys.stdout.write("Opened page: %s\n\n" % url) 

    newsoup = lxml.html.fromstring(response.read())
    wallpapers = newsoup.cssselect("#wallpaper div.item")
    
    wallpaper_ids = []
    wallpaper_names = [cleanname(el.cssselect('.details h1')[0].text_content()) for el in wallpapers]
    
    for els in [el.cssselect('.preview a img') for el in wallpapers]:
        src =  els[0].attrib['src']
        img = src.split('/')[-1]
        id = img.split('_')[0]
        wallpaper_ids.append(id)

    for id, name in zip(wallpaper_ids, wallpaper_names):
        _name = name + "_%s" % options.res
        if os.path.exists(_name + '.jpg'):
            continue #no need to regrab
        sys.stdout.write("Grab count: %s/%s\n" % (grabcount, options.number))
        if grabcount == options.number:
            break
        grabcount += 1
        built_imgurl = IMG_URL % {'imgid': id, 'imgname': name, 'imgres': options.res}
        if not grab(built_imgurl, _name): continue
    
    if grabcount == options.number: break #break again? probably should do this better    

    currentpage += 1
    sys.stdout.write("Current page: %s\n\n" % currentpage)
