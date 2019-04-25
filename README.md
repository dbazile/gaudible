# gaudiblenotifier

> Single-file program that makes notifications audible for Gnome.

![screenshot](/screenshot.png)

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

The only package dependencies are Python 2 and `pulseaudio-utils`,
both of which have a high chance of being installed by default on
Fedora and CentOS.
