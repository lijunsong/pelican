from flask import Flask
from flask import render_template
from flask import request
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

articles_generator = None


@app.template_filter('basename')
def get_basename(s):
    return os.path.basename(s)

@app.route('/')
def list_all_categories():
    global articles_generator
    return render_template("index.html", 
                           articles=articles_generator.dates,
                           categories=articles_generator.categories,
                           tags=articles_generator.tags)

"""
@app.route('/preview/<filename>')
def preview(filename):
    # TODO: check the writer. Writer should be the one construct the entire page from jinja template.
    global articles_generator
    articles = articles_generator.articles
    for article in articles:
        if os.path.basename(article.filename) == filename:
            with open(article.source_path) as f:
                origin = unicode(f.read(), "utf8")
            break

    return render_template("preview_file.html",
                           article=article, origin=origin)
"""
    
@app.route('/preview/<filename>', methods=['GET', 'POST'])
def preview(filename):
    global articles_generator
    articles = articles_generator.articles
    for article in articles:
        if os.path.basename(article.source_path) == filename:
            with open(article.source_path) as f:
                origin = unicode(f.read(), "utf8")
            break

    if request.method == 'POST':
        updated_content = request.form['editarea'].replace(u'\r\n', u'\n')
        if updated_content != origin:
            with open(article.source_path, 'w') as f:
                f.write(updated_content.encode('UTF-8'))
                origin = updated_content
                #TODO: UPDATE: article.content 

    return render_template("preview_file.html", origin=origin, article=article)

class UserSettings:
    def __init__(self, config_file, inputdir):
        self.config_file = os.path.abspath(os.path.expanduser(config_file))
        self.inputdir = os.path.abspath(os.path.expanduser(inputdir))
        self.settings = read_settings(self.config_file)
        self.settings['PATH'] = self.inputdir

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
    global articles_generator
    articles_generator = get_articles_info()
    app.run(host=HOST, port=PORT)
    

def get_articles_info():
    if len(sys.argv) < 3:
        print "usage: pelican-manager settings inputdir"
        sys.exit(1)
    user_settings = UserSettings(sys.argv[1], sys.argv[2])
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
    global articles_generator
    articles_generator = next(g for g in generators
                              if isinstance(g, ArticlesGenerator))

    return articles_generator

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print "usage: pelican-manager settings"
        sys.exit(1)
    config_file = sys.argv[1]
    settings = read_settings(config_file)
    # the settings now are dict

    #app.run(host=HOST, port=PORT)
