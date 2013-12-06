#!/bin/bash

# 
# A script that can be used on Ubuntu Unity systems with multiple workspaces
# to start different programs in different workspace.
#
# It uses wmctrl to calculate and set the viewport coordinates that correspond
# to a given workspace on the desktop. The overall approach is inspired by
# this forum thread: http://askubuntu.com/questions/41093/is-there-a-command-to-go-a-specific-workspace
#
# Tested on Ubuntu 12.04 LTS, Unity (3D) window manager
#

# detect screen resolution in x dimension
xres=$(xdpyinfo  | grep dimensions | python -c "import re; input = raw_input(); print re.search(r'dimensions:\s+(\d+)x(\d+)', input).group(1);")
# detect screen resolution in y dimension
yres=$(xdpyinfo  | grep dimensions | python -c "import re; input = raw_input(); print re.search(r'dimensions:\s+(\d+)x(\d+)', input).group(2);")
echo "screen resolution is: ${xres}x${yres}"

# detect total desktop geometry (total resolution of all workspaces)
desktopx=$(wmctrl -d | python -c "import re; input = raw_input(); print re.search(r'DG: (\d+)x(\d+)', input).group(1);")
desktopy=$(wmctrl -d | python -c "import re; input = raw_input(); print re.search(r'DG: (\d+)x(\d+)', input).group(2);")
echo "entire desktop is:    ${desktopx}x${desktopy}"

workspaces_x=$(( ${desktopx}/${xres}  ))
workspaces_y=$(( ${desktopy}/${yres} ))
echo "desktop workspaces:   ${workspaces_x}x${workspaces_y}"

#
# Switches the workspace (by moving the desktop viewport).
#
# Arguments: (workspace_x, workspace_y)
# - workspace_x: workspace coordinate in x dimension (starts at 0)
# - workspace_y: workspace coordinate in y dimension (starts at 0)
#
function switch_workspace() {
  workspace_x=${1}
  workspace_y=${2}
  
  if [[ ${workspace_x} -ge ${workspaces_x} ]]; then
    echo "error: bad workspace coordinates (${workspace_x},${workspace_y}):"
    echo "       workspace x coordinate (${workspace_x}) out of bounds."
    echo "       only ${workspaces_x} workspaces in x dimension."
    exit 1
  fi
  if [[ ${workspace_y} -ge ${workspaces_y} ]]; then
    echo "error: bad workspace coordinates (${workspace_x},${workspace_y}):"
    echo "       workspace y coordinate (${workspace_y}) out of bounds."
    echo "       only ${workspaces_y} workspaces in y dimension."
    exit 1
  fi

  # set viewport coordinates in entire desktop for the workspace
  workspace_x_coord=$(( ${workspace_x} * ${xres} ))
  workspace_y_coord=$(( ${workspace_y} * ${yres} ))
  echo "switching to workspace (${workspace_x},${workspace_y}) == viewport (${workspace_x_coord},${workspace_y_coord})"
  wmctrl -o ${workspace_x_coord},${workspace_y_coord}
}



# 
# Main script. From here on, enter commands and "switch_workspace X Y" calls
# to have commands start in a certain workspace. It may be wise to add some
# sleep before switching to the next workspace to give programs a chance to
# start up in the desired workspace. 
#


# top-left workspace
switch_workspace 0 0
thunderbird &
skype &
sleep 15

switch_workspace 1 0
~/bin/devterms.sh
sleep 5

# bottom-left workspace
switch_workspace 0 1
chromium-browser &
sleep 10

# finally, switch back to top-left workspace
switch_workspace 0 0