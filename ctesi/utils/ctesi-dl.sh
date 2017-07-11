#!/bin/bash

set -e

if [[ $# -eq 0 ]] ; then
    echo 'Please provide a url to download from.'
    exit 1
fi


dataset_url_root='http://titanic.scripps.edu/zip/'


for i in "$@"; do
    # check if we are passed just a number
    if ! [[ -n ${input//[0-9]/} ]]; then
        i="${dataset_url_root}${i}"
    fi

    dl($i)
done

function dl() {
    url=$1

    filename=$(curl -JO "$url" | grep -o -E 'filename\s'\''(.*)'\''$' | sed -e 's/filename //' -e 's/'\''//g')

    if [[ $filename ]]; then
        unzip -q -d "${filename%*.zip}" "$filename" && rm "$filename"
    else
        echo 'File not found!'
    fi
}

