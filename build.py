#!/usr/bin/env python

from snack import *
import os, stat
import pwd
import json
import inspect
import tempfile
import hashlib
from optparse import OptionParser

VERSION       = "0.9.5"
SETTINGS_FILE = os.environ["HOME"] + "/.build_settings"
GITREPO       = "https://github.com/DeviationTx/deviation"
SUDO          = "sudo -u docker -E "
SCRIPTFILE    = inspect.getfile(inspect.currentframe())

#DOCKER settings
GITBASEDIR    = "/git"
CACHEDIR      = "/opt"
HOMEDIR       = "/opt/docker"
RELEASEDIR    = "/release"

#TEST settings
if 'TESTBUILD' in os.environ:
    GITBASEDIR    = os.environ["HOME"] + "/git"
    CACHEDIR      = os.environ['TESTBUILD'] + "/build"
    HOMEDIR       = CACHEDIR
    RELEASEDIR    = os.environ['TESTBUILD'] + "/release"

GITDIR        = GITBASEDIR + "/deviation"
ENV           = {"HOME": HOMEDIR}

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

def create_git_user_if_needed():
    try:
        pwd.getpwnam('docker')
    except:
	if os.path.isdir(GITDIR):
            uid = os.stat(GITDIR).st_uid
            gid = os.stat(GITDIR).st_gid
        else:
            fd, path = tempfile.mkstemp(dir=GITBASEDIR)
            os.close(fd)
            uid = os.stat(path).st_uid
            gid = os.stat(path).st_gid
            os.unlink(path)
        if (uid == 0 or gid == 0):
            os.system("groupadd -r docker && useradd -s /bin/bash -g docker docker")
            os.chmod(GITBASEDIR, stat.S_IRWXO | stat.S_IRWXG | stat.S_IRWXU)
        else :
            os.system("groupadd -r docker -g " + str(gid))
            os.system("useradd -s /bin/bash --gid " + str(gid) + " -u " + str(uid) + " docker")
	os.mkdir(HOMEDIR)
        os.system("chown docker " + HOMEDIR)
	os.chmod(HOMEDIR, stat.S_IRWXU)

def read_config():
    if os.path.isfile(SETTINGS_FILE):
        with open(SETTINGS_FILE, 'r') as f:
            config = json.load(f)
    else:
        config = {}
    return config

def save_config(config):
    with open(SETTINGS_FILE, 'w') as f:
        json.dump(config, f)

def gui(config):
    if 'TERM' not in os.environ:
        os.environ['TERM'] = "xterm"

    rows, columns = os.popen('stty size', 'r').read().split()

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
        return None

    # Save settings
    config['update-git'] = gitcb.value()
    config['makeopts']   = makeopts.value()
    config['targets']    = targets.getSelection()

    if result == gitbut:
        cmd = "git"
    else:
        cmd = buttons.buttonPressed(result)
    return cmd

def which(program):
    def is_exe(fpath):
        return os.path.isfile(fpath) and os.access(fpath, os.X_OK)

    fpath, fname = os.path.split(program)
    if fpath:
        if is_exe(program):
            return program
    else:
        for path in os.environ["PATH"].split(os.pathsep):
            path = path.strip('"')
            exe_file = os.path.join(path, program)
            if is_exe(exe_file):
                return exe_file

    return None


def sudo(str=""):
    cmd = SUDO + " ".join("=".join(_) for _ in ENV.items())
    if "" == str:
        return os.system(cmd + " /bin/bash")
    else:
        return os.system(cmd + " /bin/bash -c '" + str + "'")

def git_update():
    sudo("cd " + GITDIR + " && git pull -u")

def pre_install_arm():
    print "Preparing for ARM build"
    if not os.path.isdir(CACHEDIR + "/gcc-arm-none-eabi-4_8-2013q4/bin"):
        sudo('cd ' + CACHEDIR + ' && ' +
             'curl --retry 10 --retry-max-time 120 -L "https://launchpad.net/gcc-arm-embedded/4.8/4.8-2013-q4-major/+download/gcc-arm-none-eabi-4_8-2013q4-20131204-linux.tar.bz2" | tar xfj -')

def setenv_arm():
    ENV['PATH'] = os.environ['PATH'] + ":" + CACHEDIR + "/gcc-arm-none-eabi-4_8-2013q4/bin"

def pre_install_windows():
    print "Preparing for Windows build"
    # don't build 'tests' because they don't work on a cross-compile, so we need to specify 'DIRS' explicitly
    if not os.path.isdir(CACHEDIR + "/fltk-1.3.3-w32/bin"):
        sudo("mkdir -p " + HOMEDIR + "/src 2>/dev/null")
        os.system("mkdir -p " + CACHEDIR + "/fltk-1.3.3-w32 2>/dev/null")
        sudo('cd ' + HOMEDIR + '/src && ' +
           'curl --retry 10 --retry-max-time 120 -L "http://fltk.org/pub/fltk/1.3.3/fltk-1.3.3-source.tar.gz" | tar xzf -')
        if 0 == sudo('cd ' + HOMEDIR + '/src/fltk-1.3.3 && ' +
                     './configure --prefix=' + CACHEDIR + '/fltk-1.3.3-w32 --enable-localzlib --enable-localpng --disable-gl --host=i586-mingw32msvc && ' +
                     'make DIRS="jpeg zlib png src fluid"'):
            os.system('cd ' + HOMEDIR + '/src/fltk-1.3.3 && make install DIRS="jpeg zlib png src fluid"')

    if not os.path.isdir(CACHEDIR + "/portaudio-w32/bin"):
        sudo("mkdir -p " + HOMEDIR + "/src 2>/dev/null")
        os.system("mkdir -p " + CACHEDIR + "/portaudio-w32 2>/dev/null")
        sudo('cd ' + HOMEDIR + '/src && ' +
             'curl --retry 10 --retry-max-time 120 -L "http://www.portaudio.com/archives/pa_stable_v19_20140130.tgz" | tar xzf -')
        if 0 == sudo('cd ' + HOMEDIR + '/src/portaudio && ' +
                     './configure --prefix=' + CACHEDIR + '/portaudio-w32 --host=i586-mingw32msvc && make'):
            os.system('cd ' + HOMEDIR + '/src/portaudio && make install')
        sudo("cp " + CACHEDIR + "/portaudio-w32/bin/libportaudio-2.dll " + GITDIR + "/src/")

    if not os.path.isdir(CACHEDIR + "/mpg123-w32/bin"):
        sudo("mkdir -p " + HOMEDIR + "/src 2>/dev/null")
        os.system("mkdir -p " + CACHEDIR + "/mpg123-w32 2>/dev/null")
        sudo('cd ' + HOMEDIR + '/src && ' +
             'curl --retry 10 --retry-max-time 120 -L "http://www.mpg123.de/download/mpg123-1.23.8.tar.bz2" | tar xjf -')
        if 0 == sudo('cd ' + HOMEDIR + '/src/mpg123-1.23.8 && ' +
                     './configure --prefix=' + CACHEDIR + '/mpg123-w32 --host=i586-mingw32msvc --disable-shared && make'):
            os.system('cd ' + HOMEDIR + '/src/mpg123-1.23.8 && make install')
        os.system("strip --strip-unneeded " + CACHEDIR + "/mpg123-w32/bin/mpg123.exe")
        sudo("cp " + CACHEDIR + "/mpg123-w32/bin/mpg123.exe " + GITDIR + "/src/")

def setenv_windows():
    ENV["FLTK_DIR"]      = CACHEDIR + "/fltk-1.3.3-w32"
    ENV["PORTAUDIO_DIR"] = CACHEDIR + "/portaudio-w32"
    ENV["MPG123_DIR"] = CACHEDIR + "/mpg123-w32"

def pre_install_linux():
    if not os.path.isfile("/usr/include/FL/Fl.H"):
        os.system("apt-get update")
        os.system("apt-get install -y libfltk1.3-dev")
        os.system("apt-get clean")

def pre_install_manual():
    if which("virtualenv") and which("inkscape"):
        return
    os.system("apt-get update")
    os.system("apt-get install -y python-virtualenv inkscape python-dev libjpeg-dev libz-dev")
    os.system("apt-get clean")

def restart():
    # For some reason in docker we can't restart snack once we stop it, so just restart the process instead
    os.execl("/usr/bin/python", "python", inspect.getfile(inspect.currentframe()), "--noupdate")

def sha1_file(filepath):
    with open(filepath, 'rb') as f:
        return hashlib.sha1(f.read()).hexdigest()

def update(config):
    tmpfile = SCRIPTFILE + ".tmp"
    if os.path.isfile(tmpfile):
        # Prevent build_init.sh from auto-updating each time
        try:
            os.unlink("/root/.build.py.sha1")
        except:
            pass
        if config.setdefault('autoupdate-build-script', 1):
            #print SCRIPTFILE + ": " + sha1_file(SCRIPTFILE)
            #print tmpfile + ": " + sha1_file(tmpfile)
            if sha1_file(SCRIPTFILE) != sha1_file(tmpfile):
                #Sanity check that new file is ok
                try:
                    with open(tmpfile) as f:
                        content = f.readlines()
                        if content[-1].startswith("main()"):
                            print "Updating " + SCRIPTFILE
                            os.system("mv -f " + tmpfile + " " + SCRIPTFILE + "; chmod 755 " + SCRIPTFILE)
                            restart()
                except:
                    print "ERROR: Failed to update " + SCRIPTFILE
    os.system("curl --retry 1 --retry-max-time 60 -L 'https://raw.githubusercontent.com/DeviationTX/deviation-docker/master/build.py' 2>/dev/null > " + tmpfile + " &")

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
    parser.add_option("-l", "--linux-prereq", action="store_true", dest="linux")
    parser.add_option("-m", "--manual-prereq", action="store_true", dest="manual")
    parser.add_option("-u", "--update",     action="store_true", dest="update")
    parser.add_option("-n", "--noupdate",     action="store_true", dest="noupdate")
    (options, args) = parser.parse_args()
    if options.arm:
        pre_install_arm()
    if options.win:
        pre_install_windows()
    if options.linux:
        pre_install_linux()
    if options.manual:
        pre_install_manual()
    if options.update:
        config = {}
        update(config)

    #If any options were specified, we should exit
    optdict = vars(options)
    for i in optdict:
        if i != "noupdate" and optdict[i]:
            return

    create_git_user_if_needed()

    if not os.path.isdir(GITDIR):
        sudo("cd " + os.path.dirname(GITDIR) + " && git clone --depth 50 " + GITREPO)

    # Handle 'run_once' commands
    if os.path.isfile(GITDIR + "/.run_once"):
        setenv_arm()
        setenv_windows()
        sudo("cd " + GITDIR + "/src && /bin/sh -c " + GITDIR + "/.run_once")
        os.remove(GITDIR + "/.run_once");
        return

    config = read_config()
    if not options.noupdate:
        update(config)
    cmd = gui(config)
    if not cmd:
        return
    save_config(config)
    os.system("clear")

    if cmd == "shell":
        print "The git repository is in: " + GITDIR
        print "If you have it yet setup the build environment, you may want to run:"
        print "\tsudo " + inspect.getfile(inspect.currentframe()) + " --arm-prereq"
        print "\tsudo " + inspect.getfile(inspect.currentframe()) + " --win-prereq"
        print "\tsudo " + inspect.getfile(inspect.currentframe()) + " --linux-prereq"
        print "\tsudo " + inspect.getfile(inspect.currentframe()) + " --manual-prereq"
        print "Type 'exit' to return to the menu"
        setenv_arm()
        setenv_windows()
        sudo()
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

    os.system("cd " + GITDIR + "/src && make distclean")
    if 0 ==sudo("cd " + GITDIR + "/src && make " + " ".join(targets)):
        os.system("cd " + GITDIR + "/src && cp -p *.zip " + RELEASEDIR)


main()
