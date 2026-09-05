import os
import json
from pathlib import Path
from tools.paths import resolve_work_path, get_work_directory
from langchain.tools import tool

@tool
def list_files (path: str = ".") -> str:
    """
    Lists file and directories under a give path in the working directory.
    
    Args:
        path: Relative path to the list. Default to the working-directory root.
    """
    work_dir = get_work_directory ()
    
    try:
        base_path = resolve_work_path (path)
    except ValueError:
        return json.dumps ({"error": f"Path {path} escapes working directory"})
    
    if not base_path.exists ():
        return json.dumps ({"error" : f"Path {path!r} does not exist"})
    if not base_path.is_dir ():
        return json.dumps ({"error" : f"Path {path!r} is not a directory"})
    
    result: list[str] = []
    
    for root, dirs, files in os.walk (base_path):
        root_path = Path (root)
        rel_path = root_path.relative_to (work_dir)
        
        for dir_name in sorted (dirs):
            result.append (f"{(rel_path / dir_name).as_posix ()}/")
        
        for file_name in sorted (files):
            result.append (f"{(rel_path / file_name).as_posix ()}/")
    
    return json.dumps (result)