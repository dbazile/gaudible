#!/bin/bash

set -xe

# Simulate regular-old notification
notify-send whee

sleep 2.5

# Simulate Evolution notification
gdbus call \
	--session \
	--dest org.gtk.Notifications \
	--object-path /org/gtk/Notifications \
	--method org.gtk.Notifications.AddNotification \
	--timeout 1 \
	org.gnome.Evolution-alarm-notify \
	system-calendar \
	'{}'
