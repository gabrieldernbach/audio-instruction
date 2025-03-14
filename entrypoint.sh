#!/bin/bash

if [[ "$1" == "--pytest" ]]; then
  shift
  exec pytest "$@"
elif [[ "$1" == "--yt-test" ]]; then
  shift
  if [[ -z "$1" ]]; then
    exec python /app/test_yt_download.py "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
  else
    exec python /app/test_yt_download.py "$@"
  fi
else
  exec "$@"
fi 