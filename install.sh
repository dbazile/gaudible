#!/bin/bash

set -xe

cd "$(dirname $(realpath $0))"

# Move the executable into place
cp gaudible.py ~/bin

# Create systemd service
mkdir -p ~/.config/systemd/user
cat <<-EOT > ~/.config/systemd/user/gaudible.service
	[Service]
	ExecStart=$HOME/bin/gaudible.py --file $HOME/.local/share/sounds/Dave/system-ready.oga
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
