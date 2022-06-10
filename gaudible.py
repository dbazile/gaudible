#!/bin/env python3

import argparse
import logging
import os
import re
import subprocess
import sys
import threading
import time

from dbus import SessionBus
from dbus.mainloop.glib import DBusGMainLoop
from gi.repository import GLib, Gio


DEFAULT_PLAYER  = '/usr/bin/paplay'
DEFAULT_SOUND   = '/usr/share/sounds/freedesktop/stereo/bell.oga'
DEFAULT_RATE_MS = 500

FILTERS = {
    'calendar':        ('org.gtk.Notifications', 'AddNotification', 'org.gnome.Evolution-alarm-notify'),
    'calendar-legacy': ('org.freedesktop.Notifications', 'Notify', 'Evolution Reminders'),
    'firefox':         ('org.freedesktop.Notifications', 'Notify', 'Firefox'),
    'notify-send':     ('org.freedesktop.Notifications', 'Notify', 'notify-send'),
    'chrome':          ('org.freedesktop.Notifications', 'Notify', 'Google Chrome'),
}

GNOME_SETTINGS    = Gio.Settings(schema='org.gnome.desktop.notifications')
PATTERN_BLOB      = re.compile(r'\[(dbus.Byte\(\d+\)(, )?){5,}\]')
PATTERN_SOUNDSPEC = re.compile(r'^(?P<name>[\w\-]+):(?P<path>.*)$')
LOG               = logging.getLogger('gaudible')  # type: logging.Logger


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--debug', action='store_true')
    ap.add_argument('--sound', dest='sound_spec', action='append', help='registers a sound for a specific filter with format <filter-name>:<file-path> or use format <file-path> for everything')
    ap.add_argument('--filter', dest='filters', action='append', choices=FILTERS.keys())
    ap.add_argument('--player', default=DEFAULT_PLAYER)
    ap.add_argument('--rate-ms', type=int, default=DEFAULT_RATE_MS)
    params = ap.parse_args()

    logging.basicConfig(
        datefmt='%H:%M:%S',
        format='%(asctime)s %(levelname)5s - %(message)s',
        level='DEBUG' if params.debug else 'INFO',
        stream=sys.stdout,
    )

    LOG.debug('build sound registry: %s', params.sound_spec)

    sounds = {'*': DEFAULT_SOUND}
    if params.sound_spec:
        for spec in params.sound_spec:
            spec = spec.strip()  # type: str
            m = PATTERN_SOUNDSPEC.match(spec)
            if m:
                key = m.group('name').lower()
                value = m.group('path')

                if key not in FILTERS:
                    ap.error('unknown filter %r in sound spec %r' % (key, spec))
                    return
            else:
                key = '*'
                value = spec

            if not os.access(value, os.R_OK):
                ap.error('audio file %r cannot be read in sound spec %r' % (value, spec))
                return

            sounds[key] = value

    LOG.debug('sound registry: %s', sounds)

    LOG.debug('check audio player')

    if not os.access(params.player, os.R_OK | os.X_OK):
        ap.error('player %r does not exist or is not executable' % (params.player,))

    LOG.debug('initialize dbus')

    DBusGMainLoop(set_as_default=True)
    bus = SessionBus()

    filter_keys = tuple(sorted(set(params.filters if params.filters else FILTERS.keys())))

    subscribe_to_messages(bus, filter_keys)
    audio_player = AudioPlayer(params.player, sounds, params.rate_ms)
    attach_message_handler(bus, audio_player, filter_keys)

    LOG.info('ONLINE')

    loop = GLib.MainLoop()
    try:
        loop.run()
    except KeyboardInterrupt:
        loop.quit()


def attach_message_handler(bus, audio_player, filter_keys):
    """
    :type bus:          SessionBus
    :type audio_player: AudioPlayer
    :type filter_keys:  tuple

    References:
    - https://developer.gnome.org/notification-spec/
    - https://wiki.gnome.org/Projects/GLib/GNotification
    """

    def on_message(_, msg):
        """
        :type msg: dbus.lowlevel.SignalMessage
        """

        try:
            interface = msg.get_interface()
            method = msg.get_member()
            args = msg.get_args_list()
            origin = str(args[0])

            for filter_key in filter_keys:
                filter_interface, filter_method, filter_origin = FILTERS[filter_key]

                if filter_interface == interface and filter_method == method and filter_origin == origin:

                    # Suppress audio if we're in 'do not disturb' mode
                    if not GNOME_SETTINGS.get_boolean('show-banners'):
                        LOG.info('SUPPRESS: \033[1m%-15s\033[0m (from=%s:%s, args=%s)',
                                 filter_key, interface, method, truncate_repr(args))
                        return

                    LOG.info('RECEIVE: \033[1m%-15s\033[0m (from=%s:%s, args=%s)',
                             filter_key, interface, method, truncate_repr(args))

                    audio_player.play(filter_key)
                    return

            LOG.debug('DROP: \033[2m%s:%s\033[0m (args=%s)',
                      interface, method, args)

        except Exception as e:
            LOG.error('Something bad happened', exc_info=e)

    bus.add_message_filter(on_message)


def subscribe_to_messages(bus, filter_keys):
    """
    :type bus:         SessionBus
    :type filter_keys: [str]

    References:
    - https://dbus.freedesktop.org/doc/dbus-specification.html#message-bus-routing-match-rules
    """

    rules = set()
    for k in filter_keys:
        interface, method, origin = FILTERS[k]

        rule = 'type=method_call, interface=%s, member=%s' % (interface, method)

        # Prevent messages forwarded by org.freedesktop.Notifications to
        # org.gtk.Notifications from showing up in the stream twice
        if interface == 'org.freedesktop.Notifications':
            rule = 'type=method_call, interface=%s, member=%s, sender=%s' % (interface, method, interface)

        LOG.info('Subscribe: \033[1m%-15s\033[0m (rule=%r, origin=%r)', k, rule, origin)

        rules.add(rule)

    proxy = bus.get_object('org.freedesktop.DBus', '/org/freedesktop/DBus')  # type: dbus.proxies.ProxyObject
    proxy.BecomeMonitor(rules, 0, dbus_interface='org.freedesktop.DBus.Monitoring')


def truncate_repr(o):
    return PATTERN_BLOB.sub('<binary blob>', repr(o))


class AudioPlayer:
    def __init__(self, player, files, rate_ms):
        self._player = player
        self._files = files  # type: dict
        self._rate_ms = max(0.01, rate_ms) / 1000
        self._quiet_until = -1

    def play(self, name):
        if self._enforce_rate_limit():
            return

        t = threading.Thread(target=self._play, args=[name], name='%s:%s' % (self.__class__.__name__, time.time()))
        t.start()

        # HACK: Without this, sometimes the first execution gets deferred until
        #       the process is about to exit.  Probably related to using GLib's
        #       event loop.
        t.join(0.1)

        return t

    def _play(self, name):
        sound_file = self._files.get(name, self._files.get('*'))
        cmd = [self._player, sound_file]
        LOG.debug('EXEC: %s (thread=%s)', cmd, threading.current_thread().name)
        subprocess.check_call(cmd)

    def _enforce_rate_limit(self):
        now = time.time()

        if now <= self._quiet_until:
            LOG.debug('audioplayer: in quiet period for another %.2f seconds',
                      self._quiet_until - now)
            return True

        self._quiet_until = now + self._rate_ms

        LOG.debug('audioplayer: setting quiet period: now=%.2f quiet_until=%.2f rate_ms=%.2f',
                  now, self._quiet_until, self._rate_ms)

        return False


if __name__ == '__main__':
    main()
