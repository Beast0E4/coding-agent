from langchain.tools import tool
from tools.text import prepare_file_content
from tools.paths import resolve_work_path

@tool
def edit_file (path: str, old_str: str, new_str: str) -> str:
    """
    Replace the `old_str` with the `new_str` in the file at `path`
    
    Language agnostic: .js, .java, .py and other text files all use exact substric replace
    Pass an empty `old_str` to create new file (same as `write_file`)
    Both strings must use real new lines and not the two character sequence backslash-n
    
    Args:
        path: Relative path of the file to edit (e.g. "README.md")
        old_str: The text to replace (e.g. "Hello World!"). Empty string creates a new file
        new_str: The text to replace with (e.g. "Hello Universe!)
    """
    if not path or old_str == new_str:
        return "Error: Invalid input"
    
    old_str = prepare_file_content (path, old_str)
    new_str = prepare_file_content (path, new_str)
    
    try:
        file_path = resolve_work_path (path)
    except ValueError as err:
        return f"Error: Path escapes the working directory: {err}"
    
    if old_str == "":
        file_path.parent.mkdir (parents=True, exist_ok=True)
        file_path.write_text (old_str, encoding="utf-8")
        return f"New file {path!r} created successfully"
    
    try:
        old_content = file_path.read_text (encoding="utf-8")
    except Exception as err:
        return f"Error: Failed to read file {path!r}: {err}"
    
    if old_str not in old_content:
        return f"Error: {path!r} does not contain {old_str!r}"
    
    new_content = old_content.replace (old_str, new_str)
    file_path.write_text (new_content, encoding="utf-8")
    
    return f"Replaced {old_str!r} with {new_str!r} in {path!r}"