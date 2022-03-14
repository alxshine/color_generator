import json
import click
from jinja2 import Environment, PackageLoader, select_autoescape
from typing import Dict
from pathlib import Path

# @click.group()
# def main():
#     pass


def parse_json(path: Path) -> Dict:
    with open(path, "r") as f:
        return json.load(f)


def parse_xresources(path: Path) -> Dict:
    with open(path, "r") as f:
        lines = f.readlines()

    prefixes = ["*."]

    def remove_prefixes(line: str) -> str:
        for prefix in prefixes:
            line = line.removeprefix(prefix)
        return line

    colorscheme = {}
    colors = {}

    # extract values from file
    matches = ["foreground", "background", "cursorColor", "color"]
    for line in lines:
        if line.startswith("!"):
            continue

        line = remove_prefixes(line)
        if any([match in line for match in matches]):
            name, value = (v.strip() for v in line.split(':'))
            if 'color' not in name:
                colorscheme[name] = value
                continue

            #color{num}
            index = int(name.removeprefix('color'))
            colors[index] = value

    # add color list to result dictionary
    colorscheme['colors'] = []
    for index in sorted(colors.keys()):
        colorscheme['colors'].append(colors[index])

    return colorscheme


@click.command()
@click.argument("colorscheme_path", type=click.Path(exists=True))
def generate(colorscheme_path: str):
    colorscheme_path = Path(colorscheme_path)
    extension = colorscheme_path.suffix.lower()
    if extension == ".xresources":
        colorscheme = parse_xresources(colorscheme_path)
    elif extension == ".json":
        colorscheme = parse_json(colorscheme_path)

    TEMPLATE_PATH = "templates/kitty.conf"

    colors = colorscheme["colors"]
    colors_indexed = dict(enumerate(colors))
    colorscheme['colors_indexed'] = colors_indexed

    env = Environment(
        loader=PackageLoader("color_generator"), autoescape=select_autoescape()
    )
    template = env.get_template("kitty.conf")
    print(template.render(colorscheme))


if __name__ == "__main__":
    generate()
