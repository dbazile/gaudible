#!/bin/bash

set -x +e

# Simulate regular-old notification
notify-send \
	'simulated: notify-send' \
	'test-body'

sleep 2.5

# Simulate Evolution notification
gdbus call \
	--session \
	--dest        'org.gtk.Notifications' \
	--object-path '/org/gtk/Notifications' \
	--method      'org.gtk.Notifications.AddNotification' \
	'org.gnome.Evolution-alarm-notify' \
	'' \
	'{
		"title": <"simulated: Evolution Reminder">,
		"body": <"test-body">,
		"icon": <"file:///usr/share/icons/Adwaita/48x48/legacy/appointment-soon.png">
	}'

sleep 2.5

# Simulate Evolution notification (legacy)
gdbus call \
	--session \
	--dest        'org.freedesktop.Notifications' \
	--object-path '/org/freedesktop/Notifications' \
	--method      'org.freedesktop.Notifications.Notify' \
	-- \
	'Evolution Reminders' \
	0 \
	'file:///usr/share/icons/Adwaita/48x48/legacy/appointment-soon.png' \
	'simulated: Evolution Reminder (legacy)' \
	'test-body' \
	'[]' \
	'{}' \
	-1

sleep 2.5

# Simulate Firefox
gdbus call \
	--session \
	--dest        'org.freedesktop.Notifications' \
	--object-path '/org/freedesktop/Notifications' \
	--method      'org.freedesktop.Notifications.Notify' \
	-- \
	'Firefox' \
	0 \
	'web-browser' \
	'simulated: Firefox' \
	'test-body' \
	'[]' \
	'{}' \
	-1
