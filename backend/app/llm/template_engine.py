"""Jinja2 Prompt Template Engine."""
import os
from jinja2 import Environment, FileSystemLoader

PROMPTS_DIR = os.path.join(os.path.dirname(__file__), "prompts")

_jinja_env = Environment(
    loader=FileSystemLoader(PROMPTS_DIR),
    autoescape=False,
    trim_blocks=True,
    lstrip_blocks=True,
)


def render_prompt(template_name: str, **context) -> str:
    """Render a prompt template with given variable context."""
    template = _jinja_env.get_template(template_name)
    return template.render(**context)
