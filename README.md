# core_py

[sdl_core](https://github.com/smartdevicelink/sdl_core) management script written in python, most used features:

- creating builds
- switching atf target
- shortcuts to manage core configuration

to get started, just update the following path variables in core.py:

- `BUILDS_DIRECTORY`: where all core builds will be stored
- `ATF_DIRECTORY`: should point to installed and built version of [sdl_atf](https://github.com/smartdevicelink/sdl_atf) (only necessary for `test` command)

```
python core.py list
	 aliases:
		q
	 description:
		 list all currently installed builds
	 optional parameters:
	   -s    omit size info
	   -g    omit git info

python core.py create <name>
	 aliases:
		build
	 description:
		 clone, cmake and make a new build
	 note:
		 name of the build to be created
	 required parameters:
	   -b    specify a branch to build from remote
	 optional parameters:
	   -t    build with tests
	   -r    build in release mode
	   -e    build with -DEXTENDED_POLICY=EXTERNAL_PROPRIETARY
	   -h    build with -DEXTENDED_POLICY=HTTP
	   -i    build with -DENABLE_IAP2EMULATION=ON
	   -j    build fast with all cores the cpu has

python core.py cmake
	 description:
		 run a cmake command using ../sdl_core
	 optional parameters:
	   -t    build with tests
	   -r    build in release mode
	   -e    build with -DEXTENDED_POLICY=EXTERNAL_PROPRIETARY
	   -h    build with -DEXTENDED_POLICY=HTTP
	   -i    build with -DENABLE_IAP2EMULATION=ON

python core.py make
	 description:
		 cmake and then make
	 optional parameters:
	   -j    build fast with all cores the cpu has
	   -t    build with tests
	   -r    build in release mode
	   -e    build with -DEXTENDED_POLICY=EXTERNAL_PROPRIETARY
	   -h    build with -DEXTENDED_POLICY=HTTP
	   -i    build with -DENABLE_IAP2EMULATION=ON

python core.py ut <build>
	 description:
		 run the unit tests on an existing build
	 note:
		 build can be the number shown with list or the name of the build

python core.py test <build>
	 aliases:
		atf
	 description:
		 update atf to target a specific build for testing
	 note:
		 build can be the number shown with list or the name of the build

python core.py remove <build>
	 aliases:
		rm, delete, del
	 description:
		 delete a build from the disk
	 note:
		 build can be the number shown with list or the name of the build

python core.py rebase <build>
	 description:
		 stash changes, checkout another branch, pop changes and build
	 note:
		 build can be the number shown with list or the name of the build
	 optional parameters:
	   -j    build fast with all cores the cpu has

python core.py update <build>
	 description:
		 fetch, pull, and re-make a build
	 note:
		 build can be the number shown with list or the name of the build
	 optional parameters:
	   -j    build fast with all cores the cpu has
	   -f    do make install even if git pull says already up to date

python core.py start <build>
	 aliases:
		run
	 description:
		 run a build
	 note:
		 build can be the number shown with list or the name of the build
	 optional parameters:
	   -k    keep context (don't delete storage, app_info.dat, log)

python core.py cd <build>
	 description:
		 print the command to change directory to a build folder
	 note:
		 build can be the number shown with list or the name of the build
		 use like this: $(core cd 0)
	 optional parameters:
	   -s    go directly to the source directory
	   -b    go directly to the build directory

python core.py scp <build>
	 description:
		 print the command to scp the bin/ folder of a build from this host
	 note:
		 build can be the number shown with list or the name of the build
	 optional parameters:
	   -f    grab full build folder

python core.py lnav <build>
	 description:
		 open the log file of a build in lnav
	 note:
		 build can be the number shown with list or the name of the build

python core.py pt <build>
	 description:
		 open the preloaded policy table of a build in vim
	 note:
		 build can be the number shown with list or the name of the build

python core.py ini <build>
	 description:
		 open the ini config of a build in vim
	 note:
		 build can be the number shown with list or the name of the build

python core.py style
	 description:
		 check style of a build
	 optional parameters:
	   -f    fix style of a build

python core.py ps
	 description:
		 list the ps output matching smartDeviceLinkCore
	 optional parameters:
	   -a    display instances from all users

python core.py help
	 aliases:
		?
	 description:
		 learn how to use this script
```

If there is any functionality you would like to see added to this script please make an issue or PR!
