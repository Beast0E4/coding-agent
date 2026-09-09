from tools.edit_file import edit_file
from tools.read_file import read_file
from tools.write_file import write_file
from tools.list_files import list_files
from tools.run_shell_command import run_shell_command

ALL_TOOLS = [
    write_file,
    edit_file,
    read_file,
    list_files,
    run_shell_command
]

def tool_catalog () -> list[dict[str, str]]:
     """
     Name + Description of all tools
     """
     
     return [{"name": tool.name, "description": tool.description} for tool in ALL_TOOLS]