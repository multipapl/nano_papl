from pathlib import Path
import re

def parse_markdown_prompts(file_path):
    """
    Parses a markdown file for prompt sections.
    Format:
    ### Title
    Prompt text...
    """
    p = Path(file_path)
    if not p.exists(): return []
    content = p.read_text(encoding="utf-8")
    sections = re.split(r'(?:^|\n)###\s+', content)
    parsed = []
    for section in sections[1:]:
        lines = section.strip().split('\n')
        # Sanitize title for filename usage
        title = re.sub(r'[\\/*?:"<>|]', "", lines[0].strip().replace(" ", "_"))
        body = "\n".join(lines[1:]).strip()
        if body: parsed.append({"title": title, "prompt": body})
    return parsed
