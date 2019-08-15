import json
import os
from collections import OrderedDict
import subprocess

from args_generators import MakefileArgsGenerator, SimpleArgsGenerator

PROJECT_PIGAIOS_DIR = '__declexporter__'


class ProjectCreator:
    """Creator for project file

    Attributes:
        project_dir (str): a path to project directory
        build_system (str): a build system that is used for the project (if is used)
    """
    def __init__(self, project_dir, build_system):
        self.project_dir = project_dir
        self.build_system = build_system

    def create_project_file(self):
        """Creates a project file
        """
        config = OrderedDict()

        config['GENERAL'] = {
            'clang-includes': self._resolve_clang_includes(),
        }
        config['GENERAL'] = OrderedDict(sorted((config['GENERAL']).items(), key=lambda x: x[0]))

        # Add the project specific configuration section
        base_path = os.path.basename(self.project_dir)
        config['PROJECT'] = {
            "cflags": " -xc",
            "cxxflags": "-xc++",
            "export-header": "{}-exported.h".format(os.path.join(PROJECT_PIGAIOS_DIR, base_path)),
        }
        config['PROJECT'] = OrderedDict(sorted((config['PROJECT']).items(), key=lambda x: x[0]))

        # And now add all discovered source files
        if self.build_system == 'Makefile':
            ag = MakefileArgsGenerator(self.project_dir)
        else:
            ag = SimpleArgsGenerator(self.project_dir)

        file_to_args = ag.generate()

        config['FILES'] = file_to_args

        project_file = os.path.join(self.project_dir, PROJECT_PIGAIOS_DIR, 'project.json')
        with open(project_file, 'w') as f:
            json.dump(config, f, indent=4)

    @staticmethod
    def _resolve_clang_includes():
        """Resolves clang include directories

        Returns:
            includes (list of str): list of clang include directories
        """
        cmd = 'echo | clang -E -Wp,-v -'
        proc = subprocess.Popen(cmd, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT)
        stdout = proc.stdout.read()

        stdout = stdout.decode()

        lines = stdout.split('\n')
        begin = False
        includes = []

        for line in lines:
            if line == '#include <...> search starts here:':
                begin = True
                continue

            if line == 'End of search list.':
                break

            if begin:
                includes.append(line.strip())

        return includes
