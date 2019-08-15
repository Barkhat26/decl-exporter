import os
from abc import ABCMeta, abstractmethod

PROJECT_PIGAIOS_DIR = '__declexporter__'


class BaseArgsGenerator:
    """Generates a map of filenames to such compile arguments as -I (include) and -D (defines)

    Attributes:
        project_path (str): an absolute path to project files
        project_pigaios_dir_path (str): an absolute path to directory where can be found results
            of pigaios working process
    """
    __metaclass__ = ABCMeta

    def __init__(self, project_path):
        self.project_path = os.path.abspath(project_path)
        
        self.project_pigaios_dir_path = os.path.join(self.project_path, PROJECT_PIGAIOS_DIR)
        if not os.path.exists(self.project_pigaios_dir_path):
            os.makedirs(self.project_pigaios_dir_path)

    @abstractmethod
    def generate(self):
        """Generate a dict of file:args and set class attribute "file_to_args" to the dict

        Returns:
            file_to_args (dict of str:list): a map of filenames to such compile arguments as
                -I (include) and -D (defines)
        """
        pass
