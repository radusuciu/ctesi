#!/bin/bash

set -e

if [[ $# -eq 0 ]] ; then
    echo 'Please provide a url to download from'
    exit 1
fi

url=$1

filename=$(curl -JO "$url" | grep -o -E 'filename\s'\''(.*)'\''$' | sed -e 's/filename //' -e 's/'\''//g')

if [[ $filename ]]; then
    unzip -q -d "${filename%*.zip}" "$filename" && rm "$filename"
else
    echo 'File not found!'
fi
