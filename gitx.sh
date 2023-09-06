#! /bin/sh
# Launch GitX
repo="${1:-.}"
shift
exec open -a GitX "$repo" "$@"
