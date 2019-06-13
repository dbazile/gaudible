#!/bin/bash

set -xe

SOUND_FILE=$HOME/.local/share/sounds/Dave/starlabs/dialog-warning.oga


cd "$(dirname $(realpath $0))"

# Move the executable into place
cp gaudible.py ~/bin/gaudible

# CentOS 7 doesn't support systemctl --user
if [[ "$(cat /etc/redhat-release)" =~ ^CentOS\ Linux\ release\ 7 ]]; then
	cat <<-EOT > ~/.config/autostart/gaudible.desktop
		[Desktop Entry]
		Name=gaudible
		Type=Application
		Exec=/home/ddb/bin/gaudible --file '$SOUND_FILE'
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
	ExecStart=$HOME/bin/gaudible --file "$SOUND_FILE"
	Restart=always
	NoNewPrivileges=true

	[Install]
	WantedBy=default.target
EOT

# Enable systemd service
systemctl --user daemon-reload
systemctl --user enable gaudible
systemctl --user start gaudible

# Check if it's running
journalctl --user -u gaudible
