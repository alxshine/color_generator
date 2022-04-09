import json
import click
from jinja2 import Environment, PackageLoader, select_autoescape
from typing import Dict
from pathlib import Path
import configparser
import os


def remove_prefix(s: str, prefix: str):
    return s[len(prefix) :] if s.startswith(prefix) else s


@click.group()
def main():
    pass


class Color:
    @classmethod
    def from_html_string(self, html_code: str):
        html_code = remove_prefix(html_code, "#")

        r = int(html_code[0:2], 16)
        g = int(html_code[2:4], 16)
        b = int(html_code[4:6], 16)
        a = int(html_code[6:8], 16) if len(html_code) > 6 else 255
        return Color(r, g, b, a)

    def __init__(self, r: int, g: int, b: int, a: int = 255):
        assert r >= 0 and r <= 255
        assert g >= 0 and g <= 255
        assert b >= 0 and b <= 255
        assert a >= 0 and a <= 255
        self.r = r
        self.g = g
        self.b = b
        self.a = a

    def __repr__(self) -> str:
        return self.to_html_string()

    def to_html_string(
        self, include_pound: bool = True, include_alpha: bool = False
    ) -> str:
        ret = "#" if include_pound else ""
        ret += f"{self.r:02x}{self.g:02x}{self.b:02x}"
        if include_alpha:
            ret += f"{self.a:02x}"
        return ret

    def to_tuple(self, include_alpha: bool = False) -> str:
        ret = f"{self.r},{self.g},{self.b}"
        if include_alpha:
            ret += f",{self.a}"

        return ret


def parse_json(path: Path) -> Dict:
    with open(path, "r") as f:
        return json.load(f)


def parse_xresources(path: Path) -> Dict:
    with open(path, "r") as f:
        lines = f.readlines()

    prefixes = ["*."]

    def remove_prefixes(line: str) -> str:
        for prefix in prefixes:
            line = remove_prefix(line, prefix)
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
            name, value = (v.strip() for v in line.split(":"))
            if "color" not in name:
                colorscheme[name] = value
                continue

            # color{num}
            index = int(remove_prefix(name, "color"))
            colors[index] = value

    # add color list to result dictionary
    colorscheme["colors"] = []
    for index in sorted(colors.keys()):
        colorscheme["colors"].append(colors[index])

    return colorscheme


def generate_colorscheme(colorscheme_path: str, template: str):
    colorscheme_path = Path(colorscheme_path)
    extension = colorscheme_path.suffix.lower()
    if extension == ".xresources":
        raw_colorscheme = parse_xresources(colorscheme_path)
    elif extension == ".json":
        raw_colorscheme = parse_json(colorscheme_path)
    else:
        raise ValueError(f"path {colorscheme_path} has unknown extension")

    colors = raw_colorscheme["colors"]
    colors_indexed = dict(enumerate(colors))
    raw_colorscheme["colors_indexed"] = colors_indexed

    colorscheme = {}
    for key, raw_value in raw_colorscheme.items():
        if isinstance(raw_value, str):
            value = Color.from_html_string(raw_value)
        elif isinstance(raw_value, list):
            value = [Color.from_html_string(item) for item in raw_value]
        elif isinstance(raw_value, dict):
            value = {k: Color.from_html_string(v) for k, v in raw_value.items()}
        else:
            raise ValueError(f"{raw_value} is of unknown type {type(raw_value)}")

        colorscheme[key] = value

    env = Environment(
        loader=PackageLoader("color_generator"), autoescape=select_autoescape()
    )
    template = env.get_template(template)

    return template.render(colorscheme)


@main.command()
@click.argument("colorscheme_path", type=click.Path(exists=True))
@click.argument("template", type=str)
def generate(colorscheme_path: str, template: str):
    print(generate_colorscheme(colorscheme_path, template))


@main.command()
@click.argument("colorscheme_path", type=str)
def inject(colorscheme_path: str):
    config = configparser.ConfigParser()
    config.read("config.ini")

    for section in config.sections():
        template = config[section]["template"]
        output_string = generate_colorscheme(colorscheme_path, template)

        target = os.path.expanduser(config[section]["target"])
        with open(target, "w") as output_file:
            output_file.write(output_string)


if __name__ == "__main__":
    main()
