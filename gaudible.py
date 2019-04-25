#!/usr/bin/python

import argparse
import logging
import os
import subprocess
import sys
import threading
import time

from dbus import SessionBus
from dbus.mainloop.glib import DBusGMainLoop
from glib import MainLoop


DEFAULT_PLAYER        = '/usr/bin/paplay'
DEFAULT_FILE          = '/usr/share/sounds/freedesktop/stereo/alarm-clock-elapsed.oga'
INTERFACE_FREEDESKTOP = 'org.freedesktop.Notifications'
INTERFACE_GTK         = 'org.gtk.Notifications'
METHOD_FREEDESKTOP    = 'Notify'
METHOD_GTK            = 'AddNotification'
ORIGIN_EVOLUTION      = 'org.gnome.Evolution-alarm-notify'

LOG = logging.getLogger('gaudible')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('-d', '--debug', action='store_true')
    ap.add_argument('-f', '--file', default=DEFAULT_FILE)
    ap.add_argument('-p', '--player', default=DEFAULT_PLAYER)
    ap.add_argument('-q', '--quieter', action='store_true')
    params = ap.parse_args()

    logging.basicConfig(
        datefmt='%H:%M:%S',
        format='%(asctime)s %(levelname)5s - %(message)s',
        level='DEBUG' if params.debug else 'INFO',
        stream=sys.stdout,
    )

    LOG.debug('Testing for player and audio file')

    if not os.access(params.player, os.R_OK | os.X_OK):
        ap.error('player does not exist or is not executable: %s' % params.player)
    if not os.access(params.file, os.R_OK):
        ap.error('audio file does not exist or is not readable: %s' % params.file)

    LOG.debug('Initializing')

    DBusGMainLoop(set_as_default=True)
    bus = SessionBus()
    subscribe_to_messages(bus, params.quieter)

    LOG.debug('Creating audio player')
    audio_player = AudioPlayer(params.player, params.file)

    LOG.debug('Adding message handler')
    attach_message_handler(bus, audio_player)

    LOG.info('ONLINE')

    loop = MainLoop()
    try:
        loop.run()
    except KeyboardInterrupt:
        loop.quit()


def attach_message_handler(bus, audio_player):
    """
    :type bus:          SessionBus
    :type audio_player: AudioPlayer

    References:
    - https://developer.gnome.org/notification-spec/
    - https://wiki.gnome.org/Projects/GLib/GNotification
    """

    def on_notify(_, msg):
        try:
            method = msg.get_member()
            interface = msg.get_interface()
            args = msg.get_args_list()
            origin = str(args[0])

            args = [str(o) for o in args]

            if interface == INTERFACE_GTK \
                    and method == METHOD_GTK \
                    and origin == ORIGIN_EVOLUTION:
                pass
            elif interface == INTERFACE_FREEDESKTOP \
                    and method == METHOD_FREEDESKTOP:
                pass
            else:
                LOG.debug('DROP: \033[2m%s:%s\033[0m (args=%s)', interface, method, args)
                return

            LOG.info('RECEIVE: \033[1m%s:%s\033[0m (args=%s)', interface, method, args)

            audio_player.play()

        except Exception as e:
            LOG.error('Something bad happened', exc_info=e)

    bus.add_message_filter(on_notify)


def subscribe_to_messages(bus, quieter=True):
    """
    :type bus: SessionBus
    :type quieter: bool

    References:
    - https://dbus.freedesktop.org/doc/dbus-specification.html#message-bus-routing-match-rules
    """

    rules = ('type=method_call, interface=%s, member=%s' % (INTERFACE_GTK, METHOD_GTK),)

    if not quieter:
        rules = rules + ('type=method_call, interface=%s, member=%s' % (INTERFACE_FREEDESKTOP, METHOD_FREEDESKTOP),)

    for rule in rules:
        LOG.info('Subscribe to %s', rule)

    proxy = bus.get_object('org.freedesktop.DBus', '/org/freedesktop/DBus')
    proxy.BecomeMonitor(rules, 0, dbus_interface='org.freedesktop.DBus.Monitoring')


class AudioPlayer:
    def __init__(self, player, file_):
        self._player = player
        self._file = file_

    def play(self):
        t = threading.Thread(target=self._play, name='%s:%s' % (self.__class__.__name__, time.time()))
        t.start()
        t.join(0.1)
        return t

    def _play(self):
        cmd = [self._player, self._file]
        LOG.debug('EXEC: %s (thread=%s)', cmd, threading.current_thread().name)
        subprocess.check_call(cmd)


if __name__ == '__main__':
    main()
