#!/bin/bash

CURRENT_SHA=$(sha1sum $HOME/build.sh 2>/dev/null)
OLD_SHA=$(cat $HOME/.build_sh_sha1 2>/dev/null)

if [ -f $HOME/.build_sh_sha1 ] && [ "$CURRENT_SHA" == "$OLD_SHA" ]; then
    curl --retry 1 --retry-max-time 60 -L "https://raw.githubusercontent.com/DeviationTX/deviation-docker/master/build.sh" > $HOME/build.sh.tmp
    HEADER=$(head -n 1 $HOME/build.sh.tmp 2>/dev/null)
    if [ -f $HOME/build.sh.tmp ] && [[ "$HEADER" =~ "bin/bash" ]]; then
       echo "Updating build.sh"
       mv $HOME/build.sh.tmp $HOME/build.sh
       chmod +x $HOME/build.sh
       sha1sum $HOME/build.sh > $HOME/.build_sh_sha1
    else
       echo "Unable to fetch updated build.sh"
       rm $HOME/build.sh.tmp
    fi
else
    echo "Skipping update of build.sh"
fi

exec $HOME/build.sh
