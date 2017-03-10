#!/usr/bin/python
# -*- coding: utf-8 -*-

import tornado.ioloop
import tornado.web
import os
from subprocess import call
import mplayer
import json
import threading
from Queue import Queue



stations = [
    ('Guerrilla (RO)', 'http://live.guerrillaradio.ro:8010/guerrilla.aac'),
    ('Tananana (RO)', 'http://live.tananana.ro:8010/stream-48.aac'),
    ('Skylyne Radio 80\'s Rock (USA)', 'http://cabhs30.sonixcast.com:9468/'),
    ('GOLD 15-93 AM Hit Radio (IT)',  'http://sr9.inmystream.info:8008/stream'),
    ('RTVA Italia (IT)', 'http://audio.nemostream.tv:9102/'),
    ('Radio Regenbogen - Salsa-Party (DE)', 'http://scast.regenbogen.de/latin-128-mp3'),
    ('Hitradio RT1 - Lounge (DE)', 'http://mp3.hitradiort1.c.nmdn.net/rt1loungehp/livestream.mp3'),
    ('CRBS - Salsa Merengue (Colombia)', 'http://69.64.58.8:8022/live'),
    ('CRBS Melodia Clásica (Colombia)', 'http://69.64.58.8:8041/live'),
    # ('sound', '../9_mm_gunshot-mike-koenig-123.mp3')
    # ('spanish.m4a', '../spanish.m4a'),
    # ('carbonInterloper', '../mp3/Interloper.mp3'),
    # ('HydroponicGarden.mp3', '../mp3/HydroponicGarden.mp3')
]

file_list = []
file_list_version = 0

def refresh_file_list():
    global file_list_version
    file_list[:] = []
    for fname in sorted(os.listdir('../yt/')):
        file_list.append((fname[:-5], '../yt/'+fname))
    file_list_version += 1 

refresh_file_list()

current_station = 0
p = None
def restart_player():
    global p
    call(['killall', 'mplayer'])
    p = mplayer.Player(args=('-ao', 'alsa:device=hw=1.0')) 

restart_player()
volume = 20
icy_info = ''

downloads = []
queue = Queue()
def download_task():
	while True:
		url = queue.get()
		call(['/usr/local/bin/youtube-dl', '--extract-audio', '--no-playlist', url, '-o', '../yt/%(title)s-%(id)s.%(ext)s'])
		print 'done'
		downloads.pop()
		queue.task_done()
		refresh_file_list()

t = threading.Thread(target=download_task)
t.daemon = True
t.start()


def log(data):
    data = data.encode('utf8')
    if data.startswith('ICY'):
        global icy_info
        icy_info = data[data.index('=')+1:data.index(';')].strip("'")
        icy_info = icy_info.replace('????', '')
    elif data.startswith('EOF'):
        print data
    else:
    	print data
p.stdout.connect(log)
# p.stderr.connect(error)


class MainHandler(tornado.web.RequestHandler):
    def get(self):
        if self.get_argument('data', False):
            self.write({
                'stations': [name for name, url in stations],
                'files': [name for name, url in file_list],
                'list_version': file_list_version,
                'crt': current_station,
                'volume': volume,
                'icy_info': icy_info,
                'downloads': '\n'.join(downloads)
            })
            return
        if self.get_argument('info', False):
            try:
                pos = p.time_pos / p.length * 100.0
            except TypeError:
                pos = -1

            self.write({
                'info': icy_info,
                'list_version': file_list_version,
                'pos': pos
            })
            return

        self.render('index.html')

    def post(self):
        global current_station, volume, icy_info
        action = self.get_argument('action')
        if action == 'station':
            current_station = int(self.get_argument('value'))
        if action == 'play' or action == 'station':
            p.volume = volume
            icy_info = (stations+file_list)[current_station][0]
            p.loadfile((stations+file_list)[current_station][1])
            p.volume = volume
        elif action == 'pause':
        	p.pause()
        elif action == 'stop':
            p.stop()
        elif action == 'fw':
            try:
                p.time_pos = p.time_pos + p.length / 20
            except:
                pass
        elif action == 'bw':
            try:
                p.time_pos = p.time_pos - p.length / 20
            except:
                pass
        elif action == 'volume':
            volume = int(self.get_argument('value'))
            p.volume = volume
        elif action == 'download':
        	value = self.get_argument('value')
        	downloads.append(value)
        	queue.put(value)
        elif action == 'del':
            file_id = int(self.get_argument('value'))
            file_name = (stations+file_list)[file_id][1]
            with open('log.txt', 'a') as fh:
                fh.write('DEL:' + file_name + '\n')
            os.remove(file_name)
            refresh_file_list()
        elif action == 'restart':
            restart_player()

class TempHandler(tornado.web.RequestHandler):
    def get(self):
	self.write('<h1>{}&deg;</h1>'.format(float(os.popen('./temperature.sh').read())/1000))



if __name__ == "__main__":
    base_dir = os.path.dirname(__file__)
    settings = {
        "static_path": base_dir + '/static',
        "cookie_secret": "A/TtehJ358iy87A0YJA3LYavL5jTTs0T1XclIXMuIwg=",
        "login_url": "/login",
        # "xsrf_cookies": True,
        'template_path': base_dir + '/template',
        'debug': True
    }

    application = tornado.web.Application([
        (r"/", MainHandler),
	(r'/temp', TempHandler)
    ], **settings)
    application.listen(8000)
    tornado.ioloop.IOLoop.current().start()
