import os
import re
import networkx as nx
from collections import OrderedDict
from args_generators.utils import is_source_file, path_endswith
from args_generators.base_args_generator import BaseArgsGenerator


class SimpleArgsGenerator(BaseArgsGenerator):
    """Generates a map of file to arguments for project that are build without any build system

       This generator may not works if you manually pass definitions as arguments (-D option)
    """

    def generate(self):
        print('[+] Retrieving files with their includes...')
        pie = ProjectIncludesExtractor(self.project_path)
        files_to_includes = pie.get_files_to_includes()

        print('[+] Retrieving files without parent...')
        files_without_parent = self._get_files_without_parent(files_to_includes)

        print('[+] Retrieving project include dirs...')
        pide = ProjectIncludeDirsExtractor(self.project_path)
        include_dirs = pide.get_project_include_dirs(files_to_includes)

        print('[+] Generating files with -I arguments...')
        file_to_args = {}
        for f in files_without_parent:
            file_to_args[f] = ['-I{}'.format(pi) for pi in include_dirs]
        
        file_to_args = OrderedDict(sorted(file_to_args.items(), key=lambda x: x[0]))
        return file_to_args

    @staticmethod
    def _get_files_without_parent(files_to_includes):
        """Gets files that are not found in #iclude statements
    
        Args: 
            files_to_includes (dict of str:list): files with their included files
    
        Returns:
            files_without_parents (list of str): files that are not found in #iclude statements
        """
    
        g = nx.DiGraph()
        
        for file, includes in files_to_includes.items():
            g.add_node(file)
            for include in includes:
                g.add_node(include)
                g.add_edge(file, include)
        
        files_without_parent = [n for n in g.nodes if len(list(g.predecessors(n))) == 0]
        files_without_parent.sort()
        return files_without_parent


class ProjectIncludesExtractor:
    def __init__(self, project_path):
        self.project_path = project_path

    def get_files_to_includes(self):
        """Gets files with their included files
    
        Returns:
            files_to_includes (dict of str:list): files with their included files
        """
    
        files_to_includes = {}
        for root, _, files in os.walk(self.project_path, topdown=False):
            for name in files:
                if is_source_file(name):
                    filepath = os.path.abspath(os.path.join(root, name))
                    relpath = os.path.relpath(filepath, self.project_path)
    
                    result = self._extract_includes(filepath)
                    if result:
                        files_to_includes[relpath] = result
                    else:
                        files_to_includes[relpath] = []
        return files_to_includes

    def _extract_includes(self, filepath):
        """Extracts included files from header file
        
        Args:
            filepath (str): path of header file
            
        Returns:
            (list): array of included files
            
            if header file doesn't contain #include statements then returns None
        """
    
        includes = []
        with open(filepath) as f:
            for line in f:
                included_file = self._extract_included_file(line.rstrip())
                if not included_file:
                    continue
                    
                includes.append(included_file)
        
        if len(includes) > 0:
            return includes
        else:
            return None

    @staticmethod
    def _extract_included_file(string):
        """Extracts name (path/name) of included file
            in #include statement
            
        Args:
            string (str): line of header file
            
        Returns:
            included_file (str): text between "" or <>
            
            if string parameter doesn't contain #include statment
            then returns None
        """
    
        pattern = r'^#\ *include ["<](?P<included_file>(\w+[\/\\])*\w+(.h)?)[">]$'
        result = re.search(pattern, string)
        if result:
            included_file = result.group('included_file')
            
            # CL.exe (Microsoft) allow backslashes in #include statements
            # but for convinient further processing we replace backslashes with slashes
            if '\\' in included_file: 
                included_file = included_file.replace('\\', '/')
                
            return included_file
        else:
            return None
    

class ProjectIncludeDirsExtractor:
    def __init__(self, project_path):
        self.project_path = project_path

    def get_project_include_dirs(self, files_to_includes):
        """Gets includes with directories where they can be found
    
        Args:
            files_to_includes (dict of str:list): files with their included files
            
        Returns:
            include_dirs (list of str): paths of include directories where
                the include can be found
        """
    
        includes = self._extract_includes(files_to_includes)
        include_dirs = self._traverse_dirs(includes)
    
        return include_dirs

    def _traverse_dirs(self, includes):
        """Traverses project directories to find directories where
            includes can be found
    
        Args:
            includes (list of str): list of includes which can be found in
                project files in #include statements
    
        Returns:
            include_dirs (list of str): paths of include directories where
                the include can be found
    
        """
    
        include_dirs = []
        
        project_files = self._get_project_files()
        
        for include in includes:
            filepath = self._find_in_project_dir(include, project_files)
            if filepath:
                include_dir = filepath[:filepath.find(include)-1]
                if include_dir not in include_dirs:
                    include_dirs.append(include_dir)

        return include_dirs

    @staticmethod
    def _find_in_project_dir(include, project_files):
        """Search project files for include. If not found returns None
    
        Args:
            include (str): search include
            project_files (list of str): list of files used to search for a include
    
        Returns:
            pf (str): path of a file that matches include
        """
    
        for pf in project_files:
            if path_endswith(pf, include):
                return pf

    def _get_project_files(self):
        """Gets project files (only source and headers)
    
        Args:
    
        Returns:
            project_files (list of str): list of project files
        """
    
        project_files = []
        for root, _, files in os.walk(self.project_path, topdown=False):
            for name in files:
                filepath = os.path.abspath(os.path.join(root, name))
                if filepath.endswith('.h') or filepath.endswith('.hpp'):
                    project_files.append(filepath)
    
        return project_files

    @staticmethod
    def _extract_includes(data):
        """Extract only includes from dict of filepath: includes
            
        Args:
            data (dict of str:list): dict of filepath: includes
        
        Returns:
            includes (list): unique array of includes
        """
        all_includes = []
        for _, file_includes in data.items():
            for fi in file_includes:
                if fi not in all_includes:
                    all_includes.append(fi)
                    
        return all_includes
