#!/bin/bash

set -e

url=$1
filename=$(curl -JO "$url" | grep -o -E 'filename\s'\''(.*)'\''$' | sed -e 's/filename //' -e 's/'\''//g')
unzip -q -d "${filename%*.zip}" "$filename"
rm "$filename"
