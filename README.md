# decl-exporter
declexporter is a tool for exporting of declarations from source code projects in c/c++. It was inspired by Pigaios export headers features.

At the moment, the tool only works for source code projects built using make (Makefile) and for projects built without any build system.

## Requirements
This project requires the installation of the CLang's Python bindings. This project works only on Linux. ou can install in Debian based Linux distros the dependencies with the following command:
```
$ sudo apt-get install clang python-clang-5.0 libclang-5.0-dev
```
Besides you need to install python packages from requirement.txt file in root directory:
```
$ pip install -r requirements.txt
```

Also in order to work with Makefile source code projects you need to install [compiledb](https://github.com/nickdiego/compiledb)

## Using declexporter.py
At the first, create a project file:
```
$ python declexporter.py --project-dir <path/to/dir> -create
```
If make build system is used for project you can specify by --build-system option, like that:
```
$ python declexporter.py --project-dir <path/to/dir> --build-system Makefile -create
```

When project file is created (by default it can be found at \_\_declexporter__/project.json) you can export all declarations:
```
$ python declexporter.py --project-dir <path/to/dir> -export
```
All exported declarations can be found at \_\_declexporter__/<name_of_project_directory>-exported.h.
