#!/bin/sh
# Homebrew shim for the TinCan container: Homebrew must not run as root, so
# when called as root re-exec as the "linuxbrew" user that owns the prefix.
BREW=/home/linuxbrew/.linuxbrew/bin/brew
if [ "$(id -u)" = "0" ] && id linuxbrew >/dev/null 2>&1; then
  exec setpriv --reuid=linuxbrew --regid=linuxbrew --init-groups \
    env HOME=/home/linuxbrew USER=linuxbrew PATH="$PATH" "$BREW" "$@"
fi
exec "$BREW" "$@"
