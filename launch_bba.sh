#! /bin/bash

echo "args = $@"

for f in "$@"
do
    echo "f = $f"
    if [ $(basename "$f") = "bba.ica" ]; then
        echo "Launch $f"
    	open "$f"
    elif [ $(basename "$f") = "bba.ica.crdownload" ]; then
        echo sleep 5
        sleep 5
        ica="${f%%.crdownload}"
        mv "$f" "$ica"
        echo Launch $ica
        open "$ica"
    fi
done
