import os
import argparse

from project_creator import ProjectCreator
from exporter import Exporter


if __name__ == '__main__':
    default_project_dir = os.getcwd()

    parser = argparse.ArgumentParser()
    parser.add_argument('-export', help='Export definitions into common header file', action='store_true')
    parser.add_argument('-create', help='Create a project file', action='store_true')
    parser.add_argument('--build-system', help='Build system that is used for project', dest='build_system',
                        default=None)
    parser.add_argument('--project-dir', help='A project directory for analysis', dest='project_dir',
                        default=default_project_dir)
    args = parser.parse_args()

    if args.create:
        pc = ProjectCreator(args.project_dir, args.build_system)
        pc.create_project_file()
    elif args.export:
        exporter = Exporter(args.project_dir)
        exporter.export()
