#!/usr/bin/env python3

import urllib.request
import re
import subprocess
import os
from datetime import date

def get_links(url):
    response = urllib.request.urlopen(url)
    data = response.read()      # a `bytes` object
    text = data.decode('utf-8')
    links = []
    for line in text.split('\n'):
        m = re.match('.*href="(/dvtv.*r~.*)".*', line)
        if m != None:
            links.append([m.group(1), re.match('.*/dvtv/(.*)/r~.*', line).group(1)])
        m2 = re.match('<span>(.*)</span></h5></div>', line)
        if m2 != None:
            d = m2.group(1).replace('&#32;', '')
            links[-1].append(d)

    return links

i = 0

all_links = []

while True:
    url = 'http://video.aktualne.cz/dvtv/?offset=%u' % (30 * i)
    links = get_links(url)
    all_links += links
    print('Getting links: %u' % i)
    if len(links) == 0:
        break

    i += 1

d = {}
for link in all_links:
    d[link[0]] = link

print(len(all_links))

c = 0
for link in all_links:
    c += 1
    print('%u/%u: %s' % (c, len(all_links), str(link)))
    u = 'http://video.aktualne.cz/%s' % link[0]
    dates = link[2].split('.')
    for i in range(len(dates)):
        if len(dates[i]) == 1:
            dates[i] = '0' + dates[i]
    if dates[-1] == '':
        dates[-1] = str(date.today().year)
    print(dates)
    prefix = '-'.join(reversed(dates))
    file_base = prefix + '-' + link[1]
    mp3 = file_base + '.mp3'
    mp4 = file_base + '.mp4'

    if os.path.isfile(mp3):
        print('File exists: ' + mp3)
        continue

    args = ["./youtube-dl", u, '-o', mp4]
    subprocess.call(args)
    subprocess.call(['ffmpeg', '-y', '-i', mp4, mp3])

    print('Removing: %s' % mp4)
    os.remove(mp4)
