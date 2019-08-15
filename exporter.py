import json
import os
import clang.cindex
from clang.cindex import CursorKind

from parser import Parser

PROJECT_PIGAIOS_DIR = '__declexporter__'


class Exporter:
    """Exporter of declarations

    Attributes:
        project_dir (str): a path to directory with source files
        declarations (list): declarations that are exported eventually
        config (dict): project configuration of declexporter
    """
    def __init__(self, project_dir):
        self.project_dir = project_dir
        self.declarations = []

        config_file = os.path.join(project_dir, PROJECT_PIGAIOS_DIR, 'project.json')
        with open(config_file) as f:
            self.config = json.load(f)

    def export(self):
        """Extracts declarations from each file and write them to the export-header file
        """
        files = self.config['FILES']

        for filename, args in files.items():
            filepath = os.path.join(self.project_dir, filename)

            if filename.endswith('.c') or filename.endswith('.h'):
                args_plus = args.extend(self.config['PROJECT']['cflags'])
            else:
                args_plus = args.extend(self.config['PROJECT']['cxxflags'])

            self.parse(filepath, args_plus)

        header_file = os.path.join(self.project_dir, self.config['PROJECT']['export-header'])
        with open(header_file, 'w') as f:
            dones = set()
            for def_type, def_name, def_src in self.declarations:
                item = str([def_type, def_name])
                is_redef = item in dones and def_type == "struct"
                if is_redef:
                    f.write("\n/** Redefined\n")

                pos = def_src.find("\n")
                if pos > -1:
                    f.write("\n")

                f.write("%s\n" % def_src)
                if pos > -1:
                    f.write("\n")

                if is_redef:
                    f.write("*/\n\n")

                dones.add(item)

    def parse(self, filename, args):
        """Parses the file with arguments

        Args:
            filename (str): an absolute path of the file
            args (str): arguments for clang parsing
        """
        index = clang.cindex.Index.create()
        tu = index.parse(filename, args=args)
        for element in tu.cursor.get_children():
            if element.kind == CursorKind.STRUCT_DECL:
                struct = Parser.parse_struct(element)

                if not struct:
                    continue

                struct_name, struct_src = struct
                self.declarations.append(["struct", struct_name, struct_src])
            elif element.kind == CursorKind.UNION_DECL:
                union = Parser.parse_union(element)

                if not union:
                    continue

                union_name, union_src = union
                self.declarations.append(["union", union_name, union_src])
            elif element.kind == CursorKind.ENUM_DECL:
                enum_name, enum_src = Parser.parse_enum(element)
                self.declarations.append(["enum", enum_name, enum_src])
            elif element.kind == CursorKind.TYPEDEF_DECL:
                typedef = Parser.parse_typedef(element)

                if not typedef:
                    continue

                typedef_name, typedef_src = typedef
                self.declarations.append(["typedef", typedef_name, typedef_src])
