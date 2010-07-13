# SongWrite
# Copyright (C) 2001-2004 Jean-Baptiste LAMY -- jibalamy@free.fr
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

import os, os.path, codecs
import globdef, latex, stemml

def relpath(base, path):
  base = os.path.normpath(os.path.abspath(base))
  path = os.path.normpath(os.path.abspath(path))
  
  while 1:
    i = base.find(os.sep)
    if base[:i] == path[:path.find(os.sep)]:
      base = base[i + 1:]
      path = path[i + 1:]
    else: break
    
  return os.curdir + os.sep + (os.pardir + os.sep) * base.count(os.sep) + path


class SongRef:
  def __init__(self, songbook, filename, title):
    self.songbook = songbook
    self.filename = filename
    self.title = title
    
  def get_song(self):
    if self.songbook:
      song = stemml.parse(os.path.join(os.path.dirname(self.songbook.filename), self.filename))
      if self.title != song.title:
        self.title = song.title
        self.songbook.save()
    else:
      song = stemml.parse(self.filename)
      
    self.__class__ = song.__class__
    self.__dict__.update(song.__dict__)
    return self
  
  def __unicode__(self): return self.title
  
  
class Songbook:
  def __init__(self, filename = "", title = u"", authors = u"", comments = u""):
    self.title             = title
    self.authors           = authors
    self.comments          = comments
    self.songs             = []
    self.version           = 0.12
    self.filename          = filename
    
  def add_song(self, filename, title = None):
    if not title: title = stemml.parse(os.path.join(os.path.dirname(self.filename), filename)).title
    self.songs.append(SongRef(self, filename, title))
    
  def on_add_song(self, filename):
    filename = relpath(self.filename, filename)
    self.add_song(filename)
    self.save()
    
  def del_song(self, index_or_song):
    if isinstance(index_or_song, int): del self.songs[index_or_song]
    else:                              self.songs.remove(index_or_song)
    
  def on_del_song(self, index_or_song):
    self.del_song(index_or_song)
    self.save()
    
  def preview_print(self):
    import latex
    
    latex.preview_songbook(self, globdef.config.PREVIEW_COMMAND)
    
  def __unicode__(self): return self.title
  
  def latex(self):
    import latex
    
    latexes = []
    lang    = None
    
    for song in self.songs:
      if isinstance(song, SongRef): song = stemml.parse(os.path.join(os.path.dirname(self.filename), song.filename))
      latexes.append(latex.latexify(song, 1))
      if not lang: lang = song.lang
      
    return r"""
\documentclass[%s,10pt]{article}
\usepackage[T1]{fontenc}
\usepackage[latin1]{inputenc}
\usepackage[lmargin=1.0cm,rmargin=2.0cm,tmargin=1.0cm,bmargin=2.0cm]{geometry}
%s

\begin{document}

\title {%s}
\author{%s}
\date  {}
\maketitle
\vfill
%s
\tableofcontents
\pagebreak

%s


\end{document}
""" % (globdef.config.PAGE_FORMAT,
       latex.lang_iso2latex[lang],
       self.title.encode("latin"),
       self.authors.encode("latin"),
       self.comments.encode("latin"),
       r"""
\pagebreak
""".join(latexes),
       )
  
  def __xml__(self, xml = None):
    from song import VERSION
    from xml.sax.saxutils import escape
    
    if not xml:
      from cStringIO import StringIO
      import codecs
      _xml = StringIO()
      xml  = codecs.lookup("utf8")[3](_xml)
      
    xml.write("""<?xml version="1.0" encoding="utf-8"?>

<songbook version="%s">
\t<title>%s</title>
\t<authors>%s</authors>
\t<comments>%s</comments>
""" % (VERSION, escape(self.title), escape(self.authors), escape(self.comments)))
    
    for song in self.songs:
      if isinstance(song.filename, str): f = song.filename.decode("latin")
      else:                              f = song.filename
      if os.path.isabs(f): f = relpath(self.filename, f)
      xml.write('\t<songfile title="%s" filename="%s"/>\n' % (song.title, f))
      
    xml.write('</songbook>')
    
    xml.flush()
    return xml
  
  def save(self):
    self.__xml__(codecs.lookup("utf8")[3](open(self.filename, "w")))
    
