#!/bin/bash
# usage: chat-blank.sh <case.mp4>
# Prints the time ranges (10 fps) where the chat area between the header and the keyboard input
# (y 350-1050 on a 1080x2340 screen) is one flat color, i.e. every message is scrolled out of view.
# Exit 1 when any frame is blank.
ffmpeg -nostats -loglevel error -i "$1" -vf "fps=10,crop=1080:700:0:350,signalstats,metadata=print:file=-" -f null - \
  | awk '/pts_time/ {split($0,a,"pts_time:"); t=a[2]} /YMIN/ {split($0,b,"="); mn=b[2]} /YMAX/ {split($0,c,"="); if (c[2]-mn<20) {n++; printf "blank %.1f s\n", t}} END {print n+0 " blank frames"; exit (n>0)}'
