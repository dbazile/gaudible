#!/bin/bash

set -x +e

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

sleep 2.5

# Simulate Evolution notification (legacy)
gdbus call \
	--session \
	--dest org.freedesktop.Notifications \
	--object-path /org/freedesktop/Notifications \
	--method org.freedesktop.Notifications.Notify \
	--timeout 1 \
	-- \
	'Evolution Reminders' \
	0 \
	system-calendar \
	'test-summary' \
	'test-body' \
	'[]' \
	'{}' \
	-1
