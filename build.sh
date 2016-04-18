#!/bin/bash
export TERM=xterm
export GITDIR=/git
export RELEASEDIR=/release

get_targets() {
    dirlist=""
    emulist=""
    
    if [ -f $HOME/.preferences ]; then
        previous=`cat $HOME/.preferences`
    else
        previous="default default_emu"
    fi
    
    count=2
    
    pushd $GITDIR/deviation/src/target/ >/dev/null
    for f in *; do
        if [ "$f" == "common" ]; then
            continue
        fi
        let count+=1
        if [[ "$f" == "emu_"* ]]; then
            emulist+="$f "
        else
            dirlist+="$f "
        fi
    done
    
    checklist=""
    for f in default default_emu $dirlist $emulist; do
        if [[ $previous =~ $f ]]; then
            status=on
        else
            status=off
        fi
        
        checklist+="$f $f $status "
    done
    popd > /dev/null
    
    exec 3>&1;
    selected=$(dialog --checklist "Cheese" 20 40 $count ${checklist} 2>&1 1>&3)
    exitcode=$?;
    exec 3>&-;
    if [ $exitcode == 0 ]; then
        echo $selected > $HOME/.preferences
    else
        exit
    fi
    targets=""
    for t in $selected; do
        if [ "$t" == "default" ]; then
            targets+="zips "
            arm_build=1
        elif [ "$t" == "default_emu" ]; then
            targets+="winzips"
            win_build=1
        elif [[ "$t" == "emu_"* ]]; then
            targets+="zip_win_$t "
            win_build=1
        else
            targets+="zip_$t "
            arm_build=1
        fi
    done
    # returns $targets
    #sets win_build and arm_build
}

pre_install_arm() {
    echo "Preparing for ARM build"
    if [ ! -d "$HOME/gcc-arm-none-eabi-4_8-2013q4/bin" ]; then
        pushd $HOME;
        curl --retry 10 --retry-max-time 120 -L "https://launchpad.net/gcc-arm-embedded/4.8/4.8-2013-q4-major/+download/gcc-arm-none-eabi-4_8-2013q4-20131204-linux.tar.bz2" | tar xfj -;
        popd;
    fi;
    export PATH=$PATH:$HOME/gcc-arm-none-eabi-4_8-2013q4/bin
}
pre_install_windows() {
    echo "Preparing for Windows build"
    # don't build 'tests' because they don't work on a cross-compile, so we need to specify 'DIRS' explicitly
    if [ ! -d "$HOME/fltk-1.3.3-w32/bin" ]; then
         mkdir $HOME/src;
         mkdir $HOME/fltk-1.3.3-w32;
         pushd $HOME/src;
         curl --retry 10 --retry-max-time 120 -L "http://fltk.org/pub/fltk/1.3.3/fltk-1.3.3-source.tar.gz" | tar xzf -;
         cd fltk-1.3.3;
         ./configure --prefix=$HOME/fltk-1.3.3-w32 --enable-localzlib --enable-localpng --disable-gl --host=i586-mingw32msvc &&
         make DIRS="jpeg zlib png src fluid" &&
         make install DIRS="jpeg zlib png src fluid";
         popd;
    fi;
    if [ ! -d "$HOME/portaudio-w32/bin" ]; then
         mkdir $HOME/src;
         mkdir $HOME/portaudio-w32;
         pushd $HOME/src;
         curl --retry 10 --retry-max-time 120 -L "http://www.portaudio.com/archives/pa_stable_v19_20140130.tgz" | tar xzf -;
         cd portaudio;
         ./configure --prefix=$HOME/portaudio-w32 --host=i586-mingw32msvc &&
         make install;
         popd;
         cp $HOME/portaudio-w32/bin/libportaudio-2.dll $GITDIR/deviation/src/;
    fi;
    export FLTK_DIR=$HOME/fltk-1.3.3-w32;
    export PORTAUDIO_DIR=$HOME/portaudio-w32;
}

#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#
if [ ! -d "$GITDIR/deviation" ]; then
         mkdir $GITDIR 2>/dev/null
         pushd $GITDIR/
         git clone --depth 50 https://github.com/DeviationTx/deviation
         popd
fi

if [ ! -d $RELEASEDIR ]; then
    mkdir $RELEASEDIR
fi

#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#

get_targets
if [[ "$targets" == "" ]]; then
    echo "Nothing to do"
    exit
fi
echo "Building $targets"

if [ "$arm_build" == "1" ]; then
    pre_install_arm
fi
if [ "$win_build" == "1" ]; then
    pre_install_windows
fi

#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#

cd $GITDIR/deviation/src
make distclean
make $targets && cp *.zip $RELEASEDIR/
