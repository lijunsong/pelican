from flask import Flask
from flask import render_template
import os
import sys

import six
import logging

from pelican.settings import read_settings
from pelican.readers import Readers
from pelican.generators import (ArticlesGenerator, PagesGenerator,
                                StaticGenerator, SourceFileGenerator,
                                TemplatePagesGenerator)

app = Flask(__name__)
app.debug = True

HOST = '0.0.0.0'
PORT = 8000

logger = logging.getLogger(__name__)

categories = None

@app.route('/')
def list_all_categories():
    global categories
    return render_template("list_categories.html", categories=categories)

class UserSettings:
    def __init__(self, config_file, inputdir):
        self.config_file = os.path.abspath(os.path.expanduser(config_file))
        self.inputdir = os.path.abspath(os.path.expanduser(inputdir))
        self.settings = read_settings(self.config_file)
        self.settings['PATH'] = self.inputdir
        self.cats, self.files = self._nest_dir_list(inputdir)

    #TODO: store static file and articles
    def _nest_dir_list(self, directory):
        dirs = []
        files = []
        for root, ds, fs in os.walk(directory):
            cur_dir = os.path.basename(root)
            if cur_dir in self.settings['STATIC_PATHS'] or cur_dir == directory:
                continue
            dirs.append(root)
            for f in fs:
                files.append(os.path.join(root, f))
        return (dirs, files)


sys.argv.append("~/git/homepage/configure/notes_conf_local.py")
sys.argv.append("~/git/homepage/notes")

def main():
    global categories
    articles_generator = get_articles_info()
    categories = articles_generator.categories
    print categories
    app.run(host=HOST, port=PORT)
    

def get_articles_info():
    if len(sys.argv) < 3:
        print "usage: pelican-manager settings inputdir"
        sys.exit(1)
    user_settings = UserSettings(sys.argv[1], sys.argv[2])
# TODO: construct cat->files dict. write template show category name and files in that category    
    cls = user_settings.settings['PELICAN_CLASS']
    if isinstance(cls, six.string_types):
        module, cls_name = cls.rsplit('.', 1)
        module = __import__(module)
        cls = getattr(module, cls_name)
    pelican = cls(user_settings.settings)

    context = pelican.settings.copy()
    context['filenames'] = {}
    context['localsiteurl'] = pelican.settings['SITEURL']
    generators = [
        cls(
            context=context,
            settings=pelican.settings,
            path=pelican.path,
            theme=pelican.theme,
            output_path=pelican.output_path
        ) for cls in pelican.get_generator_classes()
    ]

    for p in generators:
        if hasattr(p, 'generate_context'):
            p.generate_context()

    """writer = pelican.get_writer()

    for p in generators:
        if hasattr(p, 'generate_output'):
            p.generate_output(writer)
    """
    articles_generator = next(g for g in generators
                              if isinstance(g, ArticlesGenerator))

    return articles_generator



#app.run(host=HOST, port=PORT)

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print "usage: pelican-manager settings"
        sys.exit(1)
    config_file = sys.argv[1]
    settings = read_settings(config_file)
    # the settings now are dict

    #app.run(host=HOST, port=PORT)
