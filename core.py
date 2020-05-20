#!/usr/bin/python
# core build management script
# written by iCollin

import os
import sys
import time
import subprocess

MASTER_DIRECTORY='/home/collin/core/'
BUILDS_DIRECTORY=MASTER_DIRECTORY + 'builds/'
REPO_URL='https://github.com/smartdevicelink/sdl_core'
ATF_DIRECTORY=MASTER_DIRECTORY+'atf/sdl_atf/'

if len(sys.argv) < 2:
    print('correct usage: \'python core.py <command>\'')
    print('try \'python core.py help\' for more information')
    exit()

command = sys.argv[1].lower().strip()
available_builds = [d for d in os.listdir(BUILDS_DIRECTORY) if not os.path.isfile(BUILDS_DIRECTORY + d)]

class cprint:
    AQUA = '\033[96m'
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

class InputCommandArgumentType:
    IMPLIED = 0,
    REQUIRED = 1,
    OPTIONAL = 2

class InputCommandArgument:
    def __init__(self, name, description, arg_type = InputCommandArgumentType.IMPLIED):
        self._name = name
        self._type = arg_type
        self._desc = description

class InputCommand:
    def __init__(self, name, callback, description, aliases = [], arguments = [], notes = []):
        self._name = name
        self._aliases = aliases
        self._callback = callback

        self._implied_args = [arg for arg in arguments if arg._type is InputCommandArgumentType.IMPLIED]
        self._required_args = [arg for arg in arguments if arg._type is InputCommandArgumentType.REQUIRED]
        self._optional_args = [arg for arg in arguments if arg._type is InputCommandArgumentType.OPTIONAL]
        self._min_argc = 2 + len(self._implied_args) + len(self._required_args)

        self._description = description
        self._notes = notes

    def matches(self, query):
        return query == self._name or query in self._aliases

    def help(self):
        implied_args_str = ''
        for arg in self._implied_args:
            implied_args_str += ' <' + arg._name + '>'

        print cprint.BOLD + 'python core.py ' + self._name + implied_args_str + cprint.ENDC

        if len(self._aliases):
            print '\t aliases:\n\t\t' + ', '.join(self._aliases)

        print '\t description:\n\t\t ' + self._description

        if len(self._notes) or len(self._implied_args):
            print '\t note:'
            for arg in self._implied_args:
                print '\t\t ' + arg._desc
            for note in self._notes:
                print '\t\t ' + note

        if len(self._required_args):
            print '\t required parameters:'
            for arg in self._required_args:
                print '\t   -' + arg._name + '    ' + arg._desc

        if len(self._optional_args):
            print '\t optional parameters:'
            for arg in self._optional_args:
                print '\t   -' + arg._name + '    ' + arg._desc

#########################################
#               HELPERS                 #
#########################################

def selected_build(string):
    build_name = string

    try:
        index = int(build_name)
        build_name = available_builds[index]
    except:
        pass

    if build_name not in available_builds:
        potential_builds = []
        for i in range(0, len(available_builds)):
            if available_builds[i].startswith(build_name):
                potential_builds.append(available_builds[i])
        if len(potential_builds) == 1:
            raw_input(cprint.WARNING + 'Did you mean \'' + cprint.BOLD + potential_builds[0] + cprint.ENDC + cprint.WARNING + '\'? Press enter to continue...' + cprint.ENDC)
            return potential_builds[0]
        elif len(potential_builds) > 1:
            print 'ambiguous build \'' + string + '\', try \'python core.py list\''
            exit()

        print 'invalid build \'' + string + '\', try \'python core.py list\''
        exit()

    return build_name

__cores = None
def get_cores():
    if __cores is None:
        import multiprocessing
        __cores = multiprocessing.cpu_count() - 1
    
    return int(__cores) if '-j' in sys.argv else int(__cores / 2)

#########################################
#               COMMANDS                #
#########################################

def list_callback():
    print cprint.UNDERLINE + str(len(available_builds)) + ' builds found' + cprint.ENDC
    for i in range(0, len(available_builds)):
        print cprint.BOLD + '[' + str(i) + '] ' + available_builds[i] + cprint.ENDC
        
        if os.path.exists(BUILDS_DIRECTORY + available_builds[i] + '/.created'):
            build_created = os.stat(BUILDS_DIRECTORY + available_builds[i] + '/.created').st_ctime
            print cprint.OKGREEN + '\tCreated: ' + time.ctime(build_created) + cprint.ENDC

        if '-s' not in sys.argv:
            du_log = subprocess.check_output(['du', '-sh', BUILDS_DIRECTORY + available_builds[i]])
            print cprint.OKGREEN + '\t' + du_log.strip() + cprint.ENDC

        if not os.path.exists(BUILDS_DIRECTORY + available_builds[i] + '/sdl_core/.git'):
            print cprint.OKBLUE + '\tsdl_core git repository does not exist!' + cprint.ENDC
        elif '-g' not in sys.argv:
            os.chdir(BUILDS_DIRECTORY + available_builds[i] + '/sdl_core')
            git_branch = next(x for x in subprocess.check_output(['git', 'branch']).split('\n') if x[0] == '*')
            print cprint.AQUA + '\t' + git_branch + cprint.ENDC
            git_log = subprocess.check_output(['git', 'log', '-1'])
            git_info = [ log for log in git_log.split('\n') if log.strip() != '' ][:5]
            for info in git_info:
                if len(info.strip()) > 1:
                    print cprint.OKBLUE + '\t' + info + cprint.ENDC

def create_callback():
    build_name = sys.argv[2]

    if '-' in build_name:
        print cprint.FAIL + cprint.UNDERLINE + 'Invalid build_name: ' + build_name + cprint.ENDC
        exit()

    if build_name in available_builds:
        print cprint.FAIL + 'build ' + cprint.BOLD + build_name + cprint.ENDC + cprint.FAIL + ' already exists' + cprint.ENDC
        exit()

    os.mkdir(BUILDS_DIRECTORY + build_name)
    os.mkdir(BUILDS_DIRECTORY + build_name + '/core_build')
    subprocess.call(['touch', BUILDS_DIRECTORY + build_name + '/.created'])

    build_branch = sys.argv[sys.argv.index('-b') + 1] if '-b' in sys.argv else ''
    build_tests = '-t' in sys.argv
    build_ext_prop = '-e' in sys.argv
    build_http = '-h' in sys.argv
    build_iap2_emu = '-i' in sys.argv
    build_release_mode = '-r' in sys.argv

    os.chdir(BUILDS_DIRECTORY + build_name)
    repo = REPO_URL
    custom_remote = ':' in build_branch
    if custom_remote:
        colon_index = build_branch.index(':')
        repo = REPO_URL.replace('smartdevicelink', build_branch[:colon_index])
        build_branch = build_branch[colon_index+1:]
    subprocess.call(['git', 'clone', '--recurse-submodules', '-j', str(int(get_cores() / 2)), '-b', build_branch, repo])

    os.chdir(BUILDS_DIRECTORY + build_name + '/core_build')
    cmake_args = ['cmake', '../sdl_core']
    if build_tests:
        cmake_args.append('-DBUILD_TESTS=ON')
    if build_iap2_emu:
        cmake_args.append('-DENABLE_IAP2EMULATION=ON')
    if build_release_mode:
        cmake_args.append('-DCMAKE_BUILD_TYPE=Release')
    if build_ext_prop:
        cmake_args.append('-DEXTENDED_POLICY=EXTERNAL_PROPRIETARY')
    elif build_http:
        cmake_args.append('-DEXTENDED_POLICY=HTTP')
    subprocess.call(cmake_args)
    
    subprocess.call(['time', 'make', '-j', str(get_cores()), 'install'])

def ut_callback():
    subprocess.call(['make', 'test'], cwd=(BUILDS_DIRECTORY + selected_build(sys.argv[2]) + '/core_build'))

def test_callback():
    build_name = selected_build(sys.argv[2])
    build_parent_dir = BUILDS_DIRECTORY + build_name
    config_path = ATF_DIRECTORY + 'build/bin/modules/configuration/base_config.lua'

    if not os.path.exists(config_path):
        print cprint.FAIL + 'could not find your atf config file!' + cprint.ENDC
        print cprint.FAIL + 'edit ATF_DIRECTORY variable to remidiate' + cprint.ENDC
        exit()

    with open(config_path, "r") as f_r:
        data = f_r.read()

    path_to_sdl_index = data.index('config.pathToSDL')
    path_to_sdl_line_end = data.index('\n', path_to_sdl_index)
    path_to_sdl_interfaces_index = data.index('config.pathToSDLInterfaces')
    path_to_sdl_interfaces_line_end = data.index('\n', path_to_sdl_interfaces_index)
    new_path_to_sdl = 'config.pathToSDL = \"' + build_parent_dir + '/core_build/bin\"'
    new_path_to_sdl_interfaces = 'config.pathToSDLInterfaces = \"' + build_parent_dir + '/sdl_core/src/components/interfaces\"'

    new_config = data[:path_to_sdl_index] + new_path_to_sdl + data[path_to_sdl_line_end:path_to_sdl_interfaces_index] + new_path_to_sdl_interfaces + data[path_to_sdl_interfaces_line_end:]

    with open(config_path, "w") as f_w:
        f_w.write(new_config)
    
    print cprint.OKGREEN + 'ATF updated to use ' + cprint.BOLD + build_name + cprint.ENDC

def remove_callback():
    build_name = selected_build(sys.argv[2])
    subprocess.call(['rm', '-rf', BUILDS_DIRECTORY + build_name])
    print cprint.FAIL + 'build ' + cprint.BOLD + build_name + cprint.ENDC + cprint.FAIL + ' removed!' + cprint.ENDC

def rebase_callback():
    build_name = selected_build(sys.argv[2])
    branch_name = sys.argv[3]

    subprocess.call(['touch', BUILDS_DIRECTORY + build_name + '/.created'])

    os.chdir(BUILDS_DIRECTORY + build_name + '/sdl_core')
    subprocess.call(['git', 'fetch'])
    subprocess.call(['git', 'stash'])
    subprocess.call(['git', 'checkout', branch_name])
    subprocess.call(['git', 'stash', 'pop'])

    os.chdir(BUILDS_DIRECTORY + build_name + '/core_build')
    subprocess.call(['time', 'make', '-j', str(get_cores()), 'install'])

def update_callback():
    build_name = selected_build(sys.argv[2])

    subprocess.call(['touch', BUILDS_DIRECTORY + build_name + '/.created'])

    os.chdir(BUILDS_DIRECTORY + build_name + '/sdl_core')
    subprocess.call(['git', 'fetch'])
    subprocess.call(['git', 'stash'])
    git_pull_log = subprocess.check_output(['git', 'pull', 'origin'])
    subprocess.call(['git', 'stash', 'pop'])

    if '-f' not in sys.argv and git_pull_log.startswith('Already up to date.'):
        print 'target already up to date'
        exit()

    os.chdir(BUILDS_DIRECTORY + build_name + '/core_build')
    subprocess.call(['time', 'make', '-j', str(get_cores()), 'install'])

def run_callback():
    os.chdir(BUILDS_DIRECTORY + selected_build(sys.argv[2]) + '/core_build/bin')
    if '-k' not in sys.argv:
        subprocess.call(['rm', '-rf', 'storage'])
        subprocess.call(['rm', '-rf', 'app_info.dat'])
        subprocess.call(['rm', '-rf', 'SmartDeviceLinkCore.log'])
    subprocess.call(['./smartDeviceLinkCore'], env=dict(os.environ, LD_LIBRARY_PATH="."))

def cd_callback():
    postfix = '/sdl_core' if '-s' in sys.argv else '/core_build' if '-b' in sys.argv else ''
    print 'cd ' + BUILDS_DIRECTORY + selected_build(sys.argv[2]) + postfix

def scp_callback():
    build_name = selected_build(sys.argv[2])
    print cprint.OKGREEN + '\texecute this command on host:'
    print cprint.AQUA + '\t\tscp -r livio@jenkins.livio.io:' + BUILDS_DIRECTORY + build_name + '/core_build' + ('' if '-f' in sys.argv else '/bin') + ' ./' + build_name

def lnav_callback():
    subprocess.call(['lnav', BUILDS_DIRECTORY + selected_build(sys.argv[2]) + '/core_build/bin/SmartDeviceLinkCore.log'])

def pt_callback():
    subprocess.call(['vim', BUILDS_DIRECTORY + selected_build(sys.argv[2]) + '/core_build/bin/sdl_preloaded_pt.json'])

def ini_callback():
    subprocess.call(['vim', BUILDS_DIRECTORY + selected_build(sys.argv[2]) + '/core_build/bin/smartDeviceLink.ini'])

def help_callback():
    for cmd in supported_commands:
        print ''
        cmd.help()

supported_commands = [
    InputCommand('list', list_callback, 'list all currently installed builds', [ 'q' ], [
            InputCommandArgument('s', 'omit size info', InputCommandArgumentType.OPTIONAL),
            InputCommandArgument('g', 'omit git info', InputCommandArgumentType.OPTIONAL) ]),
    InputCommand('create', create_callback, 'clone, cmake and make a new build', [ 'build' ], [
            InputCommandArgument('name', 'name of the build to be created'),
            InputCommandArgument('t', 'build with tests', InputCommandArgumentType.OPTIONAL),
            InputCommandArgument('r', 'build in release mode', InputCommandArgumentType.OPTIONAL),
            InputCommandArgument('e', 'build with -DEXTENDED_POLICY=EXTERNAL_PROPRIETARY', InputCommandArgumentType.OPTIONAL),
            InputCommandArgument('h', 'build with -DEXTENDED_POLICY=HTTP', InputCommandArgumentType.OPTIONAL),
            InputCommandArgument('i', 'build with -DENABLE_IAP2EMULATION=ON', InputCommandArgumentType.OPTIONAL),
            InputCommandArgument('j', 'build fast with all cores the cpu has', InputCommandArgumentType.OPTIONAL),
            InputCommandArgument('b', 'specify a branch to build from remote', InputCommandArgumentType.REQUIRED) ]),
    InputCommand('ut', ut_callback, 'run the unit tests on an existing build', arguments = [
            InputCommandArgument('build', 'build can be the number shown with list or the name of the build') ]),
    InputCommand('test', test_callback, 'update atf to target a specific build for testing', [ 'atf' ], [
            InputCommandArgument('build', 'build can be the number shown with list or the name of the build') ]),
    InputCommand('remove', remove_callback, 'delete a build from the disk', [ 'rm', 'delete', 'del' ], [
            InputCommandArgument('build', 'build can be the number shown with list or the name of the build') ]),
    InputCommand('rebase', rebase_callback, 'stash changes, checkout another branch, pop changes and build', arguments = [
            InputCommandArgument('build', 'build can be the number shown with list or the name of the build'),
            InputCommandArgument('j', 'build fast with all cores the cpu has', InputCommandArgumentType.OPTIONAL) ]),
    InputCommand('update', update_callback, 'fetch, pull, and re-make a build', arguments = [
            InputCommandArgument('build', 'build can be the number shown with list or the name of the build'),
            InputCommandArgument('j', 'build fast with all cores the cpu has', InputCommandArgumentType.OPTIONAL),
            InputCommandArgument('f', 'do make install even if git pull says already up to date', InputCommandArgumentType.OPTIONAL) ]),
    InputCommand('start', run_callback, 'run a build', [ 'run' ], [
            InputCommandArgument('build', 'build can be the number shown with list or the name of the build'),
            InputCommandArgument('k', 'keep context (don\'t delete storage, app_info.dat, log)', InputCommandArgumentType.OPTIONAL) ]),
    InputCommand('cd', cd_callback, 'print the command to change directory to a build folder', arguments = [
            InputCommandArgument('build', 'build can be the number shown with list or the name of the build'),
            InputCommandArgument('s', 'go directly to the source directory', InputCommandArgumentType.OPTIONAL),
            InputCommandArgument('b', 'go directly to the build directory', InputCommandArgumentType.OPTIONAL) ],
        notes = [ 'use like this: $(core cd 0)' ]),
    InputCommand('scp', scp_callback, 'print the command to scp the bin/ folder of a build from this host', arguments = [
            InputCommandArgument('build', 'build can be the number shown with list or the name of the build'),
            InputCommandArgument('f', 'grab full build folder', InputCommandArgumentType.OPTIONAL) ]),
    InputCommand('lnav', lnav_callback, 'open the log file of a build in lnav', arguments = [
            InputCommandArgument('build', 'build can be the number shown with list or the name of the build') ]),
    InputCommand('pt', pt_callback, 'open the preloaded policy table of a build in vim', arguments = [
            InputCommandArgument('build', 'build can be the number shown with list or the name of the build') ]),
    InputCommand('ini', ini_callback, 'open the ini config of a build in vim', arguments = [
            InputCommandArgument('build', 'build can be the number shown with list or the name of the build') ]),
    InputCommand('help', help_callback, 'learn how to use this script', ['?'])
]

matched_commands = [cmd for cmd in supported_commands if cmd.matches(command)]
if len(matched_commands) is 0:
    help_callback()
else:
    cmd = matched_commands[0]
    if len(sys.argv) < cmd._min_argc:
        cmd.help()
    else:
        cmd._callback()
