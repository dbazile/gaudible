#!/bin/bash

set -xe

SOUND_DEFAULT="${SOUND_DEFAULT:-$HOME/.local/share/sounds/__custom/uncategorized/appointed.oga}"
SOUND_CALENDAR="${SOUND_CALENDAR:-$HOME/.local/share/sounds/__custom/uncategorized/solemn.oga}"


cd "$(dirname $(realpath $0))"

# Move the executable into place
mkdir -p ~/bin
cp gaudible.py ~/bin/gaudible

# CentOS 7 doesn't support systemctl --user
if [[ "$(cat /etc/redhat-release)" =~ ^CentOS\ Linux\ release\ 7 ]]; then
	cat <<-EOT > ~/.config/autostart/gaudible.desktop
		[Desktop Entry]
		Name=gaudible
		Type=Application
		Exec=/home/ddb/bin/gaudible --sound "calendar:$SOUND_CALENDAR" --sound "$SOUND_DEFAULT"
		Hidden=false
		NoDisplay=false
		Terminal=false
		X-GNOME-Autostart-enabled=true
	EOT
	exit
fi

# Create systemd service
mkdir -p ~/.config/systemd/user
cat <<-EOT > ~/.config/systemd/user/gaudible.service
	[Service]
	ExecStart=$HOME/bin/gaudible --sound "calendar:$SOUND_CALENDAR" --sound "$SOUND_DEFAULT"
	Restart=always
	NoNewPrivileges=true

	[Install]
	WantedBy=default.target
EOT

# Enable systemd service
systemctl --user daemon-reload
systemctl --user stop gaudible
systemctl --user enable --now gaudible

# Check if it's running
journalctl --user -u gaudible --since '-1min'
