#!/bin/zsh

monitors=$(xrandr -q | grep ' connected' | cut -f 1 -d' ')
pkill lemonbar
for monitor in $(xrandr -q | grep ' connected' | cut -f 1 -d' '); do
  zsh ~/.config/bspwm/panel_command.sh "$monitor" | lemonbar -B '{{ background }}' -F '{{ foreground }}' -u 13 -o "$monitor" &
done

