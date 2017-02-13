#!/usr/bin/python

import mplayer

p = mplayer.Player(args=('-ao', 'alsa:device=hw=1.0'))

def log(data):
    if data.startswith('ICY'):
        print '\n' + data


p.stdout.connect(log)
# p.stderr.connect(error)

p.loadfile('http://live.tananana.ro:8010/stream-48.aac')
