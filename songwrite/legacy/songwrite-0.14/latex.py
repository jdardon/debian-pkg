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

from __future__ import nested_scopes
import os, sys, array, re, cStringIO as StringIO, tempfile
import string as string_module # not a guitar string !
import globdef, song, asciitab, lilypond, shutil

lang_iso2latex = { # Languages supported by LaTeX with Babel
  "fr" : "\usepackage[francais]{babel}",
  "en" : "\usepackage[american]{babel}",
  "it" : "\usepackage[italian]{babel}",
  "sv" : "\usepackage[swedish]{babel}",
  "es" : "\usepackage[spanish]{babel}",
  "pt" : "\usepackage[portuges]{babel}",
  "de" : "\usepackage[german]{babel}",
  }

def first_line(text):
  br = text.find("\n")
  if br == -1: return text
  return text[0 : br]


def latexify(_song, songbook = 0):
  "latexify(song) -> string -- Generates a LaTeX code from a song"
  latex = StringIO.StringIO()
  
  # Skip hidden view
  partitions = filter(lambda partition: partition.view.__class__.__name__ != "HiddenView", _song.partitions)
  
  # Use literal string r"..." because of the backslash !!!
  if songbook:
    latex.write(r"""
\addcontentsline{toc}{subsection}{%s}
\begin{center}\begin{LARGE} %s \end{LARGE}\end{center}
\begin{center}\begin{large} %s \end{large}\end{center}
\begin{center}\begin{large} %s \end{large}\end{center}

""" % (_song.title.encode("latin"), _song.title.encode("latin"), _song.authors.encode("latin"), _song.date().encode("latin")))
    
  else:
    latex.write(r"""
\documentclass[%s,10pt]{article}
\usepackage[T1]{fontenc}
\usepackage[latin1]{inputenc}
%%\usepackage[margin=1.2cm]{geometry}
\usepackage[lmargin=1.0cm,rmargin=2.0cm,tmargin=1.0cm,bmargin=2.0cm]{geometry}
\usepackage{graphicx}
%s

\begin{document}

\title {%s}
\author{%s}
\date  {%s}
\maketitle

""" % (globdef.config.PAGE_FORMAT, lang_iso2latex[_song.lang], _song.title.encode("latin"), _song.authors.encode("latin"), _song.date().encode("latin")))

  if lilypond.lily_version == 2.4: # Hack
    latex.write(r"""\input lily-ps-defs
""")
    
  
  latex.write(r"""
%s
""" % _song.comments.replace("\n", "\n\n").encode("latin"))
  latex.write(r"""
\begin{lilypond}
""")
  
  lilypond.lilypond(_song, latex)
  
  latex.write(r"""
\end{lilypond}
%%\vfill
~ \\
""")
  
  
  for partition in partitions:
    if   isinstance(partition, song.Lyrics2):
      latex.write(r"""
\begin{verse}
""")
      if partition.header: latex.write(r"""
\subsection*{%s}
""" % partition.header.encode("latin"))
      
      latex.write(partition.text.encode("latin").replace("_\t", "").replace("-\t", "").replace("\t", " ").replace("_", "").replace(" ,", ","))
      latex.write(r"""
\end{verse}
""")
      
    elif isinstance(partition, song.Lyrics):
      latex.write(r"""
\begin{sffamily}
%s
\end{sffamily}
\begin{verse}
""" % partition.header.encode("latin"))
      asciitab.lyrics2text(partition, latex, line_sep = "\n\n")
      latex.write(r"""
\end{verse}""")
      
  if songbook:
    pass
  else:
    latex.write(r"""
\end{document}
""")
  
  #print latex.getvalue()
  return latex.getvalue()


def export2lily(_song, file): open(file, "w").write(latexify(_song))

def export2ps(_song, file = None):
  file = re.escape(file)
  
  temp_dir = tempfile.mktemp()
  temp_lily = os.path.join(temp_dir, "gtab.lytex")
  temp_tex  = os.path.join(temp_dir, "gtab.tex")
  temp_dvi  = os.path.join(temp_dir, "gtab.dvi")
  
  os.mkdir(temp_dir)
  
  try:
    open(temp_lily, "w").write(latexify(_song))
    
    run_lily (temp_lily, temp_tex)
    run_latex(temp_tex , temp_dvi)
    run_dvips(temp_dvi , file)
    
  finally:
    try: shutil.rmtree(temp_dir) # Clean all temp files
    except: pass
    
def songbook2ps(songbook, file = None):
  file = re.escape(file)
  
  temp_dir = tempfile.mktemp()
  temp_lily = os.path.join(temp_dir, "gtab.lytex")
  temp_tex  = os.path.join(temp_dir, "gtab.tex")
  temp_dvi  = os.path.join(temp_dir, "gtab.dvi")
  
  os.mkdir(temp_dir)
  
  try:
    open(temp_lily, "w").write(songbook.latex())
    
    run_lily (temp_lily, temp_tex)
    run_latex(temp_tex , temp_dvi)
    run_latex(temp_tex , temp_dvi)
    run_dvips(temp_dvi , file)
    
  finally:
    try: shutil.rmtree(temp_dir) # Clean all temp files
    except: pass
    
def preview(_song, command):
  temp_ps = tempfile.mktemp(".ps")
  
  try:
    export2ps(_song, temp_ps)
    os.system("%s %s" % (command, temp_ps))
  finally:
    try: os.remove(temp_ps) # Clean ps temp file
    except: pass
  
def preview_songbook(_songbook, command):
  temp_ps = tempfile.mktemp(".ps")
  
  try:
    songbook2ps(_songbook, temp_ps)
    os.system("%s %s" % (command, temp_ps))
  finally:
    try: os.remove(temp_ps) # Clean ps temp file
    except: pass
  
def run_lily(file, output):
  command = "cd %s; lilypond-book -o %s %s" % (os.path.dirname(file), os.path.dirname(output), file)
  print
  print
  print "Running '%s'" % command
  os.system(command)
  
def run_latex(file, output):
  latex = open(file).read()
  if not r"\usepackage{graphicx}" in latex:
    print r"Warning, '\usepackage{graphicx}' is missing in latex code, i'll add it..."
    i = latex.find(r"\usepackage")
    latex = latex[:i] + r"\usepackage{graphicx}\n" + latex[i:]
    open(file, "w").write(latex)
    
  command = "cd %s; latex %s" % (os.path.dirname(file), os.path.basename(file))
  print
  print
  print "Running '%s'" % command
  os.system(command)

  os.rename(file[:-3] + "dvi", output)
  os.remove(file[:-3] + "aux")
  os.remove(file[:-3] + "log")
  
def run_dvips(file, output):
  command = "cd %s; dvips -o %s %s" % (os.path.dirname(file), output, file)
  print
  print
  print "Running '%s'" % command
  os.system(command)
  

def first_line(text):
  br = text.find("\n")
  if br == -1: return text
  return text[0 : br]


if __name__ == "__main__":
  import sys
  import cPickle as pickle
  
  _song = pickle.load(open(sys.argv[1]))
  
  print latexify(_song)

