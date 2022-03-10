import json
import click
from jinja2 import Environment, PackageLoader, select_autoescape

# @click.group()
# def main():
#     pass


@click.command()
@click.argument("colorscheme_path", type=click.Path(exists=True))
def generate(colorscheme_path: str):
    TEMPLATE_PATH = "templates/kitty.conf"

    with open(colorscheme_path, "r") as f:
        colorscheme = json.load(f)

    foreground = colorscheme["foreground"]
    background = colorscheme["background"]
    colors = colorscheme["color"]
    colors = dict(enumerate(colors))

    env = Environment(
        loader=PackageLoader("color_generator"), autoescape=select_autoescape()
    )
    template = env.get_template("kitty.conf")
    print(template.render(foreground=foreground,background=background,colors=colors)) 

if __name__ == "__main__":
    generate()
