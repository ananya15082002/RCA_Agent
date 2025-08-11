#!/bin/bash
# Wrapper script to run cleanup from the correct directory
cd "/home/ananyasingh.int/5xx-copy/5xx"
export PATH="/usr/local/bin:/usr/bin:/bin:$PATH"
export HOME="$HOME"
export USER="$USER"
export SHELL="/bin/bash"

# Run the cleanup script
"/home/ananyasingh.int/5xx-copy/5xx/cleanup_old_data.sh" >> "/home/ananyasingh.int/5xx-copy/5xx/logs/cleanup.log" 2>&1
