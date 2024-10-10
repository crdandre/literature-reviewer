import sys
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.markdown import Markdown
from literature_reviewer.agents.components.agent_pydantic_models import *

def print_ascii_art(ascii_art):
    console = Console()
    if ascii_art:
        colored_art = Text(ascii_art)
        colored_art.stylize("cyan")
        console.print(colored_art)

def print_latest_entry(entry):
    console = Console(file=sys.stderr)
    console.print()
    title = f"{entry.agent_name} - {entry.heading} | {entry.timestamp} | {entry.model}"
    
    if entry.content_structure:
        try:
            model_class = globals()[entry.content_structure]
            parsed_content = model_class.parse_raw(entry.content)
            content = parsed_content.as_rich()
        except (KeyError, ValueError) as e:
            content = Text(f"Error formatting content: {str(e)}", style="red")
    else:
        content = Markdown(entry.content)
    
    main_panel = Panel(
        content,
        title=title,
        border_style="blue",
        padding=(1, 1)
    )
    
    console.print(main_panel)
