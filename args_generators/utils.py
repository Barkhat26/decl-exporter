import os


def is_source_file(filename):
    """Checks if the file is source file
    
    Args:
        filename (str): checked filename
    
    Returns:
        (bool): is file source file
    """
    
    return filename.endswith('.h') or filename.endswith('.hpp') \
        or filename.endswith('.c') or filename.endswith('.cpp')


def path_endswith(path, trailer):
    """Checks if path has a trailer file

    Args:
        path (str): a path to a file
        trailer (str): a file or a file with its parent(s)

    Returns:
        (bool): has path a trailer file
    """
    path_parts = splitall(path)
    trailer_parts = splitall(trailer)
    return path_parts[-len(trailer_parts):] == trailer_parts


def splitall(path):
    """Splits a path

    Args:
        path (str): a path to file

    Returns:
        allparts (list): parts of splitted path
    """
    allparts = []
    while 1:
        parts = os.path.split(path)
        if parts[0] == path:  # sentinel for absolute paths
            allparts.insert(0, parts[0])
            break
        elif parts[1] == path:  # sentinel for relative paths
            allparts.insert(0, parts[1])
            break
        else:
            path = parts[0]
            allparts.insert(0, parts[1])
    return allparts
