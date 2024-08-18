import argparse

from . import app, document

def parse_cmdline():
    parser = argparse.ArgumentParser()
    parser.add_argument('path', help='File to load')
    return parser.parse_args()

def main():
    options = parse_cmdline()
    doc = document.TextDocument(options.path)
    app.App(doc).run()
