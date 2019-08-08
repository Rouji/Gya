#!/usr/bin/env python3

from flask import Flask, render_template, safe_join, send_from_directory, abort
from os.path import isfile, isdir
from os import listdir
import hashlib
from subprocess import call

app = Flask(__name__)
app.config.from_pyfile('config.py')

def make_thumb(infile: str, outfile: str, size: str):
    '''infile and outfile assumed to be safe'''
    ext = infile.split('.')[-1].lower()
    if ext in app.config['VIDEO_EXT']:
        ext += '[0]'  # use first frame if video

    if size == 'small':
        px = 500
        q = 65
    elif size == 'big':
        px = 1500
        q = 80
    else:
        raise ValueError(f'"{size}" is not a valid size')
    call(['convert', infile, '-resize', '700^>', '-quality', str(q), '-strip', outfile])

@app.route('/')
def index():
    return 'hello this is a webpage'

@app.route('/<string:album>')
def album_index(album: str):
    files = listdir(safe_join(app.config['ALBUMS_BASE_DIR'], album))
    return render_template('album.html', album=album, files=files)

@app.route('/<string:album>/<string:file>')
def album_file(album: str, file: str):
    album_path = safe_join(app.config['ALBUMS_BASE_DIR'], album)
    if not isdir(album_path):
        abort(404)
    return send_from_directory(album_path, file)

@app.route('/thumb/<string:album>/<string:file>/<string:size>')
def thumbnail(album: str, file: str, size: str):
    orig_file = safe_join(app.config['ALBUMS_BASE_DIR'], album, file)
    print(orig_file)
    if not isfile(orig_file):
        abort(404)

    sha = hashlib.sha256()
    sha.update(orig_file.encode('utf-8'))
    sha.update(size.encode('utf-8'))
    cache_hex = sha.hexdigest()
    cache_file = safe_join(app.config['CACHE_DIR'], cache_hex)
    if not isfile(cache_file):
        make_thumb(orig_file, cache_file, size)

    return send_from_directory(app.config['CACHE_DIR'], cache_hex)

if __name__ == '__main__':
    app.run(debug=True)
