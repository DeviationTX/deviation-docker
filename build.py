#!/usr/bin/env python

from snack import *
import os
import json
import inspect
from optparse import OptionParser

VERSION       = "0.9.2"
SETTINGS_FILE = os.environ["HOME"] + "/.build_settings"
GITREPO       = "https://github.com/DeviationTx/deviation"

#DOCKER settings
GITDIR        = "/git/deviation"
CACHEDIR      = os.environ["HOME"]
RELEASEDIR    = "/release"

#TEST settings
if 'TESTBUILD' in os.environ:
    GITDIR        = os.environ["HOME"] + "/git/deviation"
    CACHEDIR      = os.environ['TESTBUILD'] + "/build"
    RELEASEDIR    = os.environ['TESTBUILD'] + "/release"

def append_checkbox(cb, values, str):
    if str in values:
        value = 1
    else:
        value = 0
    cb.append(str, None, value)

def addItem_checkbox(cb, values, group, str):
    if str in values:
        value = 1
    else:
        value = 0
    cb.addItem(str, (group, snackArgs['append']), None, value)

def get_targets(dir):
    txs = []
    emus = []
    for f in sorted(os.listdir(dir)):
        if f == "common":
            continue
        if f.startswith("emu_"):
            emus.append(f)
        else:
            txs.append(f)
    return [txs, emus]

def gui():
    if 'TERM' not in os.environ:
        os.environ['TERM'] = "xterm"

    rows, columns = os.popen('stty size', 'r').read().split()

    if os.path.isfile(SETTINGS_FILE):
        with open(SETTINGS_FILE, 'r') as f:
            config = json.load(f)
    else:
        config = {}
    txs, emus = get_targets(GITDIR + "/src/target/")
    screen = SnackScreen();
    screen.pushHelpLine("    <Tab>/<Alt-Tab> between elements   |  <Space> selects   |  <ESC> exits")

    gitcb = Checkbox("Update GIT before build", config.setdefault('update-git', 1))
    gitbut = Button("Update GIT now")

    config.setdefault('targets', ["default", "emu_default"])
    rows = int(rows)
    if rows < 29:
        if rows <= 24:
           cbheight = 5
        else:
           cbheight = 10 - (29 - rows)
    else:
        cbheight = 10
    targets = CheckboxTree(height = cbheight, scroll = 1)
   
    append_checkbox(targets, config.get('targets'), "default") 
    append_checkbox(targets, config.get('targets'), "emu_default") 
    targets.append("Transmitter builds", None, 1)
    for f in txs:
        addItem_checkbox(targets, config.get('targets'), 2, f)
    targets.append("Emulators for Windows", None, 1)
    for f in emus:
        addItem_checkbox(targets, config.get('targets'), 3, f)

    buttons = ButtonBar(screen, (("Build", "build"), ("Cancel", "cancel"), ("Shell", "shell")))
    makeopts = Entry(32, config.setdefault('makeopts', ""))
    optslabel = Label("Make Options:")

    gitgrid = Grid(2, 1)
    gitgrid.setField(gitcb, 0, 0, padding = (0, 0, 1, 0))
    gitgrid.setField(gitbut, 1, 0, padding = (1, 0, 0, 0))

    optsgrid = Grid(2, 1)
    optsgrid.setField(optslabel, 0, 0, padding = (0, 0, 1, 0))
    optsgrid.setField(makeopts, 1, 0, padding = (1, 0, 0, 0))

    grid = GridForm(screen, "Deviation Firmware Builder " + VERSION, 1, 4)
    grid.add(buttons, 0, 0, growx = 1)
    grid.add(targets, 0, 1, growx = 1, padding = (0, 1, 0, 0))
    grid.add(gitgrid, 0, 2, padding = (1, 1, 1, 0))
    grid.add(optsgrid, 0, 3, padding = (1, 1, 1, 0))
    result = grid.runOnce()

    screen.finish();

    if result == "ESC" or result == "F12" or buttons.buttonPressed(result) == "cancel":
        print "No action"
        return None, None

    # Save settings
    config['update-git'] = gitcb.value()
    config['makeopts']   = makeopts.value()
    config['targets']    = targets.getSelection()
    with open(SETTINGS_FILE, 'w') as f:
        json.dump(config, f)

    if result == gitbut:
        cmd = "git"
    else:
        cmd = buttons.buttonPressed(result)
    return cmd, config


def git_update():
    os.system("cd " + GITDIR + " && git pull -u")

def pre_install_arm():
    print "Preparing for ARM build"
    if not os.path.isdir(CACHEDIR + "/gcc-arm-none-eabi-4_8-2013q4/bin"):
        os.system("cd " + CACHEDIR + " && " +
                  "curl --retry 10 --retry-max-time 120 -L 'https://launchpad.net/gcc-arm-embedded/4.8/4.8-2013-q4-major/+download/gcc-arm-none-eabi-4_8-2013q4-20131204-linux.tar.bz2' | tar xfj -")

def setenv_arm():
    os.environ['PATH'] += ":" + CACHEDIR + "/gcc-arm-none-eabi-4_8-2013q4/bin"

def pre_install_windows():
    print "Preparing for Windows build"
    # don't build 'tests' because they don't work on a cross-compile, so we need to specify 'DIRS' explicitly
    if not os.path.isdir(CACHEDIR + "/fltk-1.3.3-w32/bin"):
        os.system("mkdir -p " + CACHEDIR + "/src 2>/dev/null")
        os.system("mkdir -p " + CACHEDIR + "/fltk-1.3.3-w32 2>/dev/null")
        os.system("cd " + CACHEDIR + "/src && " +
           "curl --retry 10 --retry-max-time 120 -L 'http://fltk.org/pub/fltk/1.3.3/fltk-1.3.3-source.tar.gz' | tar xzf -")
        os.system("cd " + CACHEDIR + "/src/fltk-1.3.3 && " +
           "./configure --prefix=" + CACHEDIR + "/fltk-1.3.3-w32 --enable-localzlib --enable-localpng --disable-gl --host=i586-mingw32msvc && " +
           "make DIRS='jpeg zlib png src fluid' &&" +
           "make install DIRS='jpeg zlib png src fluid'")

    if not os.path.isdir(CACHEDIR + "/portaudio-w32/bin"):
        os.system("mkdir -p " + CACHEDIR + "/src 2>/dev/null")
        os.system("mkdir -p " + CACHEDIR + "/portaudio-w32 2>/dev/null")
        os.system("cd " + CACHEDIR + "/src && " +
           "curl --retry 10 --retry-max-time 120 -L 'http://www.portaudio.com/archives/pa_stable_v19_20140130.tgz' | tar xzf -")
        os.system("cd " + CACHEDIR + "/src/portaudio && " +
           "./configure --prefix=" + CACHEDIR + "/portaudio-w32 --host=i586-mingw32msvc && " +
           "make install")
        os.system("cp " + CACHEDIR + "/portaudio-w32/bin/libportaudio-2.dll " + GITDIR + "/src/")

def setenv_windows():
    os.environ['FLTK_DIR'] = CACHEDIR + "/fltk-1.3.3-w32"
    os.environ['PORTAUDIO_DIR'] = CACHEDIR + "/portaudio-w32"

def restart():
    # For some reason in docker we can't restart snack once we stop it, so just restart the process instead
    os.execl("/usr/bin/python", "python", inspect.getfile(inspect.currentframe()))

def main():
    usage = """
Display build menu:
	%prog
Install ARM build environment:
	%prog --arm-prereq
Install Windows build environment:
	%prog --win-prereq"""
    parser = OptionParser(usage=usage)
    parser.add_option("-a", "--arm-prereq", action="store_true", dest="arm")
    parser.add_option("-w", "--win-prereq", action="store_true", dest="win")
    (options, args) = parser.parse_args()
    if options.arm:
        pre_install_arm()
    if options.win:
        pre_install_windows()

    #If any options were specified, we should exit
    optdict = vars(options)
    for i in optdict:
        if optdict[i]:
            return

    if not os.path.isdir(GITDIR):
        os.system("cd " + os.path.dirname(GITDIR) + " && git clone --depth 50 " + GITREPO)

    [cmd, config] = gui()
    if not cmd:
        return
    os.system("clear")

    if cmd == "shell":
        print "The git repository is in: " + GITDIR
        print "If you have it yet setup the build environment, you may want to run:"
        print "\t" + inspect.getfile(inspect.currentframe()) + " --arm-prereq"
        print "\t" + inspect.getfile(inspect.currentframe()) + " --win-prereq"
        print "Type 'exit' to return to the menu"
        setenv_arm()
        setenv_windows()
        os.system("/bin/bash")
        restart()
    if cmd == "git" or config['update-git']:
        git_update()
        if cmd is "git":
            restart()

    win_build = 0
    arm_build = 0
    targets = []
    for t in config['targets']:
        if t == "default":
            targets.append("zips")
            arm_build=1
        elif t == "emu_default":
            targets.append("winzips")
            win_build=1
        elif t.startswith("emu_"):
            targets.append("zip_win_" + t)
            win_build=1
        else:
            targets.append("zip_" + t)
            arm_build=1

    print "Building " + " ".join(targets)

    if arm_build:
        pre_install_arm()
        setenv_arm()
    if win_build:
        pre_install_windows()
        setenv_windows()

    os.system("cd " + GITDIR + "/src && make distclean && make " + " ".join(targets) + " && cp *.zip " + RELEASEDIR)


main()
