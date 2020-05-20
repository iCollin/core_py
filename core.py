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
SHELL_NAME='gnome-terminal'

if len(sys.argv) < 2:
    print('correct usage: \'python core.py <command>\'')
    print('try \'python core.py help\' for more information')
    exit()

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

command = sys.argv[1].upper()

available_builds = [d for d in os.listdir(BUILDS_DIRECTORY) if not os.path.isfile(BUILDS_DIRECTORY + d)]

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

def update_atf_target(build_parent_dir):
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

__cores = None
def get_cores():
    if __cores is None:
        import multiprocessing
        __cores = multiprocessing.cpu_count() - 1
    
    return int(__cores) if '-j' in sys.argv else int(__cores / 2)

#########################################
#               COMMANDS                #
#########################################

if command in [ 'LIST', 'Q' ]:
    print cprint.UNDERLINE + str(len(available_builds)) + ' builds found' + cprint.ENDC
    for i in range(0, len(available_builds)):
        print cprint.BOLD + '[' + str(i) + '] ' + available_builds[i] + cprint.ENDC
        
        if os.path.exists(BUILDS_DIRECTORY + available_builds[i] + '/.created'):
            build_created = os.stat(BUILDS_DIRECTORY + available_builds[i] + '/.created').st_ctime
            print cprint.OKGREEN + '\tCreated: ' + time.ctime(build_created) + cprint.ENDC
        else:
            print cprint.OKGREEN + '\tCreated: ???' + cprint.ENDC

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

elif command in [ 'CREATE', 'BUILD' ]:
    if len(sys.argv) < 5 or '-b' not in sys.argv:
        print 'correct usage: \'python core.py create <name>\''
        print '\t -b \t\t specify a branch to build from remote'
        print 'optional parameters:'
        print '\t -r \t\t build in release mode'
        print '\t -e \t\t build with -DEXTENDED_POLICY=EXTERNAL_PROPRIETARY'
        print '\t -h \t\t build with -DEXTENDED_POLICY=HTTP'
        print '\t -i \t\t build with -DENABLE_IAP2EMULATION=ON'
        print '\t -j \t\t build fast with all cores the cpu has'
        print 'try \'python core.py help\' for more information'
        exit()
    
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

    print cprint.UNDERLINE + 'Creating build from git!' + cprint.ENDC
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
        if '-m' in sys.argv:
            cmake_args.append('-DCMAKE_BUILD_TYPE=MinSizeRel')
        else:
            cmake_args.append('-DCMAKE_BUILD_TYPE=Release')
    if build_ext_prop:
        cmake_args.append('-DEXTENDED_POLICY=EXTERNAL_PROPRIETARY')
    elif build_http:
        cmake_args.append('-DEXTENDED_POLICY=HTTP')
    subprocess.call(cmake_args)
    
    subprocess.call(['time', 'make', '-j', str(get_cores()), 'install'])

elif command == 'UT':
    if len(sys.argv) < 3:
        print 'correct usage: \'python core.py ut <build>\''
        print 'NOTE: build can be the number shown with list or the name of the build'
        exit()

    build_name = selected_build(sys.argv[2])

    os.chdir(BUILDS_DIRECTORY + build_name + '/core_build')
    subprocess.call(['make', 'test'])

elif command == 'TEST':
    if len(sys.argv) < 3:
        print 'correct usage: \'python core.py test <build>\''
        print 'NOTE: build can be the number shown with list or the name of the build'
        exit()

    build_name = selected_build(sys.argv[2])

    update_atf_target(BUILDS_DIRECTORY + build_name)
    print cprint.OKGREEN + 'ATF updated to use ' + cprint.BOLD + build_name + cprint.ENDC

elif command in [ 'REMOVE', 'RM', 'DEL', 'DELETE' ]:
    if len(sys.argv) < 3:
        print 'correct usage: \'python core.py remove <build>\''
        print 'NOTE: build can be the number shown with list or the name of the build'
        exit()

    build_name = selected_build(sys.argv[2])

    subprocess.call(['rm', '-rf', BUILDS_DIRECTORY + build_name])
    print cprint.FAIL + 'build ' + cprint.BOLD + build_name + cprint.ENDC + cprint.FAIL + ' removed!' + cprint.ENDC

elif command == 'UPDATE':
    if len(sys.argv) < 3:
        print 'correct usage: \'python core.py update <name>\''
        print 'try \'python core.py help\' for more information'
        exit()
    
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

elif command == 'REBASE':
    if len(sys.argv) < 4:
        print 'correct usage: \'python core.py rebase <name> <branch>\''
        print 'try \'python core.py help\' for more information'
        exit()
    
    build_name = selected_build(sys.argv[2])
    branch_name = sys.argv[3]

    subprocess.call(['touch', BUILDS_DIRECTORY + build_name + '/.created'])

    os.chdir(BUILDS_DIRECTORY + build_name + '/sdl_core')
    subprocess.call(['git', 'fetch'])
    subprocess.call(['git', 'stash'])
    subprocess.call(['git', 'checkout', branch_name])
    subprocess.call(['git', 'stash', 'pop'])

    os.chdir(BUILDS_DIRECTORY + build_name + '/core_build')
    subprocess.call(['time', 'make', '-j', str(get_cores()), ])
    subprocess.call(['make', 'install'])

elif command == "START" or command == "RUN":
    if len(sys.argv) < 3:
        print 'correct usage: \'python core.py start <name>\''
        print 'try \'python core.py help\' for more information'
        exit()
    
    build_name = selected_build(sys.argv[2])

    os.chdir(BUILDS_DIRECTORY + build_name + '/core_build/bin')
    subprocess.call(['rm', '-rf', 'storage'])
    subprocess.call(['rm', '-rf', 'app_info.dat'])
    subprocess.call(['rm', '-rf', 'SmartDeviceLinkCore.log'])
    subprocess.call(['./smartDeviceLinkCore'], env=dict(os.environ, LD_LIBRARY_PATH="."))

elif command == "SH":
    if len(sys.argv) < 3:
        print 'correct usage: \'python core.py sh <name>\''
        print 'try \'python core.py help\' for more information'
        exit()
    
    build_name = selected_build(sys.argv[2])

    subprocess.call([SHELL_NAME, '--working-directory=' + BUILDS_DIRECTORY + build_name])

elif command == "CD":
    if len(sys.argv) < 3:
        print 'correct usage: \'python core.py cd <name>\''
        print 'try \'python core.py help\' for more information'
        exit()
    
    build_name = selected_build(sys.argv[2])

    postfix = ''
    
    if '-s' in sys.argv:
        postfix = '/sdl_core'
    elif '-b' in sys.argv:
        postfix = '/core_build'

    print 'cd ' + BUILDS_DIRECTORY + build_name + postfix

elif command == "SCP":
    if len(sys.argv) < 3:
        print 'correct usage: \'python core.py scp <name>\''
        print 'try \'python core.py help\' for more information'
        exit()
    
    build_name = selected_build(sys.argv[2])

    print ''
    print cprint.OKGREEN + '\texecute this command on host:'
    print cprint.AQUA + '\t\tscp -r livio@jenkins.livio.io:' + BUILDS_DIRECTORY + build_name + '/core_build' + ('' if '-f' in sys.argv else '/bin') + ' ./' + build_name
    print ''

elif command == "LNAV":
    if len(sys.argv) < 3:
        print 'correct usage: \'python core.py lnav <name>\''
        print 'try \'python core.py help\' for more information'
        exit()
    
    build_name = selected_build(sys.argv[2])

    subprocess.call(['lnav', BUILDS_DIRECTORY + build_name + '/core_build/bin/SmartDeviceLinkCore.log'])

elif command == "PT":
    if len(sys.argv) < 3:
        print 'correct usage: \'python core.py pt <name>\''
        print 'try \'python core.py help\' for more information'
        exit()
    
    build_name = selected_build(sys.argv[2])

    subprocess.call(['vim', BUILDS_DIRECTORY + build_name + '/core_build/bin/sdl_preloaded_pt.json'])

elif command == "INI":
    if len(sys.argv) < 3:
        print 'correct usage: \'python core.py ini <name>\''
        print 'try \'python core.py help\' for more information'
        exit()
    
    build_name = selected_build(sys.argv[2])

    subprocess.call(['vim', BUILDS_DIRECTORY + build_name + '/core_build/bin/smartDeviceLink.ini'])

else:
    if command not in [ 'HELP', '?' ]:
        print 'Command \'' + command + '\' not recognized!'

    print ''

    print cprint.BOLD + 'python core.py list' + cprint.ENDC
    print '\t description:\n\t\t list all currently installed builds'
    print '\t optional parameters:'
    print '\t     -g    omit git info'
    print '\t     -s    omit size info'

    print ''

    print cprint.BOLD + 'python core.py create <name>' + cprint.ENDC
    print '\t description:\n\t\t clone, cmake and make a new build'
    print '\t required parameters:'
    print '\t     -b    specify a branch to build from remote'
    print '\t optional parameters:'
    print '\t     -t    build with tests'
    print '\t     -r    build in release mode'
    print '\t     -e    build with -DEXTENDED_POLICY=EXTERNAL_PROPRIETARY'
    print '\t     -h    build with -DEXTENDED_POLICY=HTTP'
    print '\t     -i    build with -DENABLE_IAP2EMULATION=ON'
    print '\t     -j    build fast with all cores the cpu has'

    print ''

    print cprint.BOLD + 'python core.py test <build>' + cprint.ENDC
    print '\t description:\n\t\t update atf to target a specific build for testing'
    print '\t note:\n\t\t build can be the number shown with list or the name of the build'

    print ''

    print cprint.BOLD + 'python core.py ut <build>' + cprint.ENDC
    print '\t description:\n\t\t run the unit tests on an existing build'
    print '\t note:\n\t\t build can be the number shown with list or the name of the build'

    print ''

    print cprint.BOLD + 'python core.py remove <build>' + cprint.ENDC
    print '\t description:\n\t\t delete a build from the disk'
    print '\t note:\n\t\t build can be the number shown with list or the name of the build'

    print ''

    print cprint.BOLD + 'python core.py update <build>' + cprint.ENDC
    print '\t description:\n\t\t fetch, pull, and re-make a build'
    print '\t note:\n\t\t build can be the number shown with list or the name of the build'
    print '\t optional parameters:'
    print '\t     -j    build fast with all cores the cpu has'

    print ''

    print cprint.BOLD + 'python core.py rebase <build> <branch>' + cprint.ENDC
    print '\t description:\n\t\t run a build'
    print '\t note:\n\t\t build can be the number shown with list or the name of the build'
    print '\t\t branch is the new branch to be checked out and built'
    print '\t optional parameters:'
    print '\t     -j    build fast with all cores the cpu has'

    print ''

    print cprint.BOLD + 'python core.py start <build>' + cprint.ENDC
    print '\t description:\n\t\t run a build'
    print '\t note:\n\t\t build can be the number shown with list or the name of the build'

    print ''

    print cprint.BOLD + 'python core.py cd <build>' + cprint.ENDC
    print '\t description:\n\t\t print the command to cd to the folder of a build'
    print '\t note:\n\t\t build can be the number shown with list or the name of the build'
    print '\t\t use like this: $(core cd 0)'
    print '\t optional parameters:'
    print '\t     -s    go directly to the source directory'
    print '\t     -b    go directly to the build directory'

    print ''

    print cprint.BOLD + 'python core.py scp <build>' + cprint.ENDC
    print '\t description:\n\t\t print the command to scp the bin/ folder of a build from this host'
    print '\t note:\n\t\t build can be the number shown with list or the name of the build'
    print '\t optional parameters:'
    print '\t     -f    grab full build folder'

    print ''

    print cprint.BOLD + 'python core.py lnav <build>' + cprint.ENDC
    print '\t description:\n\t\t open the log file of a build in lnav'
    print '\t note:\n\t\t build can be the number shown with list or the name of the build'

    print ''

    print cprint.BOLD + 'python core.py pt <build>' + cprint.ENDC
    print '\t description:\n\t\t open the preloaded policy table of a build in vim'
    print '\t note:\n\t\t build can be the number shown with list or the name of the build'

    print ''

    print cprint.BOLD + 'python core.py ini <build>' + cprint.ENDC
    print '\t description:\n\t\t open the ini config of a build in vim'
    print '\t note:\n\t\t build can be the number shown with list or the name of the build'

    print ''
