#!/usr/bin/env python3

import urllib.request
import re
import subprocess
import os
import json

from datetime import *
from feedgen.feed import FeedGenerator
from pytz import timezone
from urllib.parse import urljoin
from mutagen.mp3 import MP3

dest_folder = 'podcasts'
podcast_file = 'dvtv.rss'
root_url = 'http://192.168.10.201/'
start_date = datetime(2015, 1, 1, tzinfo = timezone('Europe/Prague'))
datetime_format = '%Y-%m-%d %H:%M:%S'
prague_tz = timezone('Europe/Prague')

def build_url(suffix):
    return 'http://video.aktualne.cz/%s' % suffix

class VideoDatabase:
    def __init__(self, rss_filename, json_filename):
        self.videos = set()
        self.rss_filename = rss_filename
        self.json_filename = json_filename

        if os.path.exists(json_filename):
            with open(json_filename, 'r') as ifile:
                for i in json.load(ifile):
                    self.videos.add(Video(json = i))

        if len(self.videos) > 0:
            latest_date = max(map(lambda x: x.date, self.videos))
            global start_date
            if latest_date > start_date:
                start_date = latest_date

        print('Downloading videos younger than: ' + datetime.strftime(start_date, datetime_format))

        fg = FeedGenerator()
        fg.load_extension('podcast')
        fg.podcast.itunes_category('Technology', 'Podcasting')

        fg.id('marxin-dvtv')
        fg.title('DVTV')
        fg.author({'name': 'Martin Liška', 'email': 'marxin.liska@gmail.com' })
        fg.language('cs-CZ')
        fg.link(href = 'test.cz', rel = 'self')
        fg.description('DVTV')

        self.feed_generator = fg

    def add_video(self, video):
        self.videos.add(video)

    def serialize(self):
        with open(self.json_filename, 'w') as ofile:
           json.dump([x.serialize() for x in self.videos], ofile)

        self.feed_generator.rss_file(self.rss_filename)

    def get_page_links(self, url):
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
            m2 = re.match('.*<span>(.*)</span></h5>', line)
            if m2 != None and last_video != None:
                d = m2.group(1).replace('&#32;', '')
                last_video.set_date(d)
            m3 = re.match('.*<span class="nazev">(.*)</span>.*', line)
            if m3 != None and last_video != None:
                last_video.description = m3.group(1)
            m4 = re.match('<img src="([^"]*)".*', line)
            if m4 != None and last_video != None:
                last_video.image = m4.group(1)

        return (links, all(map(lambda x: x.date < start_date, links)))

    def get_links(self):
        all_links = []

        i = 0
        while True:
            url = 'http://video.aktualne.cz/dvtv/?offset=%u' % (5 * i)
            links = self.get_page_links(url)
            all_links += links[0]
            # all links are older that threshold
            if links[1]:
                print("Breaking")
                break;
            print('Getting links: %u' % i)
            if len(links) == 0:
                break

            i += 1

        d = {}
        for link in all_links:
            d[link.link] = link

        all_links = list(set(filter(lambda x: not 'Drtinová Veselovský TV' in x.description and x.date >= start_date, all_links)))
        all_links = sorted(all_links, reverse = True, key = lambda x: x.date)
        return all_links

    def add_podcast_entry(self, video, filename):
        fe = self.feed_generator.add_entry()
        fe.id(video.link)
        fe.title(video.description)
        fe.description(video.full_description)
        u = urljoin(root_url, filename)
        fe.link(href = u, rel = 'self')
        fe.enclosure(u, str(os.stat(filename).st_size), 'audio/mpeg')
        fe.published(video.date)
        mp3_length = round(MP3(filename).info.length)
        fe.podcast.itunes_duration(mp3_length)

        self.feed_generator.rss_file(os.path.join(dest_folder, podcast_file))

    def main(self):
        FNULL = open(os.devnull, 'w')

        if not os.path.exists(dest_folder):
            os.makedirs(dest_folder)

        all_links = self.get_links()
        c = 0
        for video in all_links:
            c += 1
            print('%u/%u: %s' % (c, len(all_links), str(video)))

            mp3 = video.get_filename ('mp3')
            mp4 = video.get_filename ('mp4')

            if not os.path.isfile(mp3):
                u = build_url(video.link)
                args = ["./youtube-dl", u, '-o', mp4]
                subprocess.call(args)

                if not os.path.isfile(mp4):
                    print('Error in downloading: ' + mp4)
                    continue

                print(['ffmpeg', '-y', '-i', mp4, mp3])
                subprocess.check_call(['ffmpeg', '-y', '-i', mp4, mp3])
                subprocess.check_call(['id3v2', '-2', '-g', 'Žunalistika', '-a', 'DVTV', '-A', 'DVTV ' + video.date.strftime('%Y-%m'), '-t', 'DVTV: ' + video.date.strftime('%d. %m. ') + video.description, mp3])
                subprocess.check_call(['eyeD3', '--add-image', 'cover.jpg:OTHER', mp3], stderr = FNULL, stdout = FNULL)

                print('Removing: %s' % mp4)
                os.remove(mp4)
            else:
                print('File exists: ' + mp3)

            # add new RSS feed entry
            print('Getting full description for: '+ video.description)
            video.get_description()

            self.add_video(video)
            self.add_podcast_entry(video, mp3)

class Video:
    def __init__(self, link = None, filename = None, json = None):
        self.link = link
        self.filename = filename
        self.date = None
        self.description = None
        self.full_description = None

        if json != None:
            self.link = json['link']
            self.filename = json['filename']
            self.date = prague_tz.localize(datetime.strptime(json['date'], datetime_format))
            self.description = json['description']
            self.full_description = json['full_description']

    def serialize(self):
        return { 'link': self.link, 'filename': self.filename, 'date': datetime.strftime(self.date, datetime_format), 'description': self.description, 'full_description': self.full_description }

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

        dates = list(map(lambda x: int(x), dates))
        self.date = datetime(dates[0], dates[1], dates[2], tzinfo = prague_tz)

    def create_folder(self):
        f = datetime.strftime(self.date, '%Y-%m')
        f = os.path.join(dest_folder, f)
        if not os.path.exists(f):
            os.makedirs(f)
        return f

    def get_date_str(self):
        return self.date.strftime('%d. %m. %Y')

    def __str__(self):
        return 'link: %s, filename: %s, description: %s, date: %s' % (self.link, self.filename, self.description, self.get_date_str())

    def get_filename(self, suffix):
        f = self.create_folder()
        return os.path.join(f, '%s-%s.%s' % (self.date.strftime('%Y-%m-%d'), self.filename, suffix))

    def get_description(self):
        response = urllib.request.urlopen(build_url(self.link))
        data = response.read()
        text = data.decode('utf-8')
        description = '' 
        start = False
        for line in text.split('\n'):
            m = re.match('.*<p class="popis" data-replace="description"><span>[^|]*(.*)', line)
            if start:
                description += line
            elif m != None:
                description = m.group(1).strip().lstrip('| ')
                start = True

            if '</p>' in description:
                break

        self.full_description = description.strip().strip('</p>')

    def __eq__(self, other):
        return other != None and self.link == other.link

    def __hash__(self):
        return hash(self.link)

db = VideoDatabase(os.path.join(dest_folder, 'podcast.rss'), os.path.join(dest_folder, 'db.json'))
db.main()
db.serialize()
