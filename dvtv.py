#!/usr/bin/env python3

import urllib.request
import re
import subprocess
import os

from datetime import *

class Video:
    def __init__(self, link, filename):
        self.link = link
        self.filename = filename
        self.date = None
        self.description = None

    def set_date(self, s):
        dates = s.split('.')
        if dates[0] == 'dnes':
            dates = datetime.strftime(datetime.now(), '%Y.%m.%d').split('.')

        for i in range(len(dates)):
            if len(dates[i]) == 1:
                dates[i] = '0' + dates[i]
        if dates[-1] == '':
            dates[-1] = str(date.today().year)

        if int(dates[2]) > 31:
            dates = reversed(list(dates))

        prefix = '-'.join(dates)
        self.date = prefix

    def __str__(self):
        return 'link: %s, filename: %s, description: %s, date: %s' % (self.link, self.filename, self.description, self.date)

    def get_filename(self, suffix):
        return '%s-%s.%s' % (self.date, self.filename, suffix)

def get_links(url):
    response = urllib.request.urlopen(url)
    data = response.read()
    text = data.decode('utf-8')
    links = []
    last_video = None
    for line in text.split('\n'):
        m = re.match('.*href="(/dvtv.*r~.*)".*', line)
        if m != None:
            if last_video != None:
                links.append(last_video)
            last_video = Video(m.group(1), re.match('.*/dvtv/(.*)/r~.*', line).group(1))
        m2 = re.match('<span>(.*)</span></h5></div>', line)
        if m2 != None and last_video != None:
            d = m2.group(1).replace('&#32;', '')
            last_video.set_date(d)
        m3 = re.match('.*<span class="nazev">(.*)</span>.*', line)
        if m3 != None and last_video != None:
            last_video.description = m3.group(1)

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
    d[link.link] = link

print(len(all_links))

c = 0
for video in sorted(all_links, reverse = True, key = lambda x: x.date):
    c += 1
    print('%u/%u: %s' % (c, len(all_links), str(video)))
    u = 'http://video.aktualne.cz/%s' % video.link

    mp3 = video.get_filename ('mp3')
    mp4 = video.get_filename ('mp4')

    if os.path.isfile(mp3):
        print('File exists: ' + mp3)
        continue

    args = ["./youtube-dl", u, '-o', mp4]
    subprocess.call(args)

    if not os.path.isfile(mp4):
        print('Error in downloading: ' + mp4)
        continue

    subprocess.call(['ffmpeg', '-y', '-i', mp4, mp3])
    subprocess.call(['id3v2', '-2', '-g', 'Žurnalistika', '-a', 'DVTV', '-A', 'DVTV', '-t', 'DVTV: ' + video.description, mp3])

    print('Removing: %s' % mp4)
    os.remove(mp4)
