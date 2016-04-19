#!/bin/bash

SCRIPTNAME=build.py
SCRIPT=$HOME/$SCRIPTNAME
SHA1=$HOME/.$SCRIPTNAME.sha1

CURRENT_SHA=$(sha1sum $SCRIPT 2>/dev/null)
OLD_SHA=$(cat $SHA1 2>/dev/null)

if [ -f $SHA1 ] && [ "$CURRENT_SHA" == "$OLD_SHA" ]; then
    curl --retry 1 --retry-max-time 60 -L "https://raw.githubusercontent.com/DeviationTX/deviation-docker/master/$SCRIPTNAME" > $SCRIPT.tmp
    HEADER=$(head -n 1 $SCRIPT.tmp 2>/dev/null)
    if [ -f $SCRIPT.tmp ] && [[ "$HEADER" =~ "python" ]]; then
       echo "Updating $SCRIPTNAME"
       mv $SCRIPT.tmp $SCRIPT
       chmod +x $SCRIPT
       sha1sum $SCRIPT > $SHA1
    else
       echo "Unable to fetch updated $SCRIPTNAME"
       rm $SCRIPT.tmp
    fi
else
    echo "Skipping update of $SCRIPTNAME"
fi

exec $SCRIPT
