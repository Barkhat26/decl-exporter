import subprocess
import os
import json
from collections import OrderedDict
from args_generators.utils import is_source_file
from args_generators.base_args_generator import BaseArgsGenerator


class MakefileArgsGenerator(BaseArgsGenerator):
    """Generates a map of file to arguments for project that are build with make build system
    """

    def generate(self):
        print('[+] Generating compile_commands.json file...')
        self._generate_compile_commands_file()

        filepath = os.path.join(self.project_pigaios_dir_path, 'compile_commands.json')
        with open(filepath) as f:
            compile_commands = json.load(f)
      
        file_to_args = {}
    
        print('[+] Generating a map of files to arguments...')
        for cc in compile_commands:
            filename = cc['file']
            if not is_source_file(filename):
                continue
        
            args_filtered = [arg for arg in cc['arguments'] if arg.startswith('-I') or arg.startswith('-D')]
            file_to_args[filename] = args_filtered
        
        file_to_args = OrderedDict(sorted(file_to_args.items(), key=lambda x: x[0]))
        return file_to_args

    def _generate_compile_commands_file(self):
        """Generates compile_commands.json by calling external program "compiledb".
           compile_commands.json file is saved in pigaios project directory (by default __pigaios__/)
        """
        old_dir = os.getcwd()
        os.chdir(self.project_path)
        output_filepath = os.path.join(self.project_pigaios_dir_path, 'compile_commands.json')
        cmd = 'compiledb -n -o {} make'.format(output_filepath)
        process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
        process.communicate()
        os.chdir(old_dir)
