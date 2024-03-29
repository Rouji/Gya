#!/usr/bin/env python3

from flask import Flask, render_template, safe_join, send_from_directory, abort
from os.path import isfile, isdir
from os import listdir, remove
import hashlib
from subprocess import call

app = Flask(__name__)
app.config.from_pyfile('config.py')

def make_thumb(infile: str, outfile: str, size: str):
    '''infile and outfile assumed to be safe'''
    ext = infile.split('.')[-1].lower()
    if ext in app.config['VIDEO_EXT']:
        infile += '[0]'  # use first frame if video

    if size == 'small':
        px = app.config.get('THUMB_S_PX') or 500
        q = app.config.get('THUMB_S_Q') or 50
    elif size == 'big':
        px = app.config.get('THUMB_B_PX') or 1800
        q = app.config.get('THUMB_B_Q') or 75
    else:
        raise ValueError(f'"{size}" is not a valid size')
    call([
        'convert',
        '-strip',
        '-interlace', 'Plane',
        infile,
        '-auto-orient',
        '-resize', f'{px}^>',
        '-quality', str(q),
        outfile
    ])

@app.route('/')
def index():
    dirs = sorted([
        d for d
        in listdir(app.config['ALBUMS_BASE_DIR'])
        if isdir(safe_join(app.config['ALBUMS_BASE_DIR'],d))
    ])
    return render_template('index.html', dirs=dirs)

@app.route('/<string:album>')
def album_index(album: str):
    try:
        files = sorted(listdir(safe_join(app.config['ALBUMS_BASE_DIR'], album)))
    except FileNotFoundError as ex:
        abort(404)
    return render_template('album.html', album=album, files=files, video_ext=app.config['VIDEO_EXT'])

@app.route('/<string:album>/<string:file>')
def album_file(album: str, file: str):
    album_path = safe_join(app.config['ALBUMS_BASE_DIR'], album)
    if not isdir(album_path):
        abort(404)
    return send_from_directory(album_path, file)

@app.route('/play.svg')
def playsvg():
    return send_from_directory(app.root_path, 'play.svg')

@app.route('/thumb/<string:album>/<string:file>/<string:size>')
def thumbnail(album: str, file: str, size: str):
    size, ext = size.split('.')
    if ext not in ['jpg', 'webp']:
        abort(404)
    orig_file = safe_join(app.config['ALBUMS_BASE_DIR'], album, file)

    sha = hashlib.sha256()
    sha.update(orig_file.encode('utf-8'))
    sha.update(size.encode('utf-8'))
    cache_hex = sha.hexdigest()
    cache_file = safe_join(app.config['CACHE_DIR'], cache_hex) + '.' + ext

    if not isfile(orig_file):
        if isfile(cache_file):
            remove(cache_file)
        abort(404)

    if not isfile(cache_file):
        make_thumb(orig_file, cache_file, size)

    return send_from_directory(app.config['CACHE_DIR'], cache_hex + '.' + ext)

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
