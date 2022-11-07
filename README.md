# gaudible

> Single-file program that makes notifications audible for Gnome.

![screenshot](/screenshot.png)

## Usage

```bash
# all filters
./gaudible.py -v

# only specific filters
./gaudible.py -v --filter calendar --filter calendar-legacy

# register specific sounds for specific filters
./gaudible.py \
    -v \
    --sound calendar:calendar.oga \
    --sound firefox:browser.oga   \
    --sound default-sound.oga        # sound for everything else
```

## Why?

I got tired of missed meetings because Evolution doesn't play audio
for appointment reminders by default.

[This](https://gitlab.gnome.org/GNOME/evolution/issues/152) doesn't
seem to have any traction, but maybe one day
[this](https://gitlab.gnome.org/GNOME/glib/issues/1340) becomes a
thing...

## How?

All this does is listen for common notification traffic patterns on
DBus.

The only package dependencies are Python 3, PyGObject and
`pulseaudio-utils`, all of which have a high chance of being installed
by default on Fedora 30+.

Note: `paplay`, the default player, doesn't support MP3/MP4 playback so
either conversion or a different player is needed

## Reference

```bash
# see gdbus usage
cat test.py

# listen for dbus messages
dbus-monitor 'type=method_call, interface=org.gtk.Notifications, member=AddNotification' \
             'type=method_call, interface=org.freedesktop.Notifications, member=Notify'

# identify dbus unique addresses
qdbus

# describe dbus service methods
qdbus org.gtk.Notifications /org/gtk/Notifications
```
