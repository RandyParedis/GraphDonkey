# GraphDonkey
A simple and easy-to-use application for visualizing and editing Graphviz
Dot files, running on `Python 3`. It is based on the idea of `xdot`, combined 
with a texteditor that can live-update the images. Behind the screens, it 
binds `PyQt5` and `graphviz` together.

The idea behind this piece of software sprung from the necessity of creating a
lot of images of finite state automata. In the past, you needed to  have a
texteditor, Graphviz-viewer and a terminal open at all times. Not anymore!

`GraphDonkey`, originally called `DotGaper`, solves this issue by combining these
applications into one.

**Current Version:** `0.0.2`<br/>
**Build Type:** `beta` (_unstable_)<br/>
**Author:** Randy Paredis

### Requirements
_See also `requirements.txt`._
* `PyQt5` (including `uic`)
* `graphviz`

### Installation
Installing `GraphDonkey` is quite easy. All you have to do is clone this
repository. Also make sure you have installed the `PyQt5` and `graphviz`
modules for `pip3`, which will allow this application to work.

_For future work, the goal is to make this available as an application on
either PyPI or as a bundled resource._

### Running `GraphDonkey`
When you've installed `GraphDonkey` as described above, you can just run
the `__main__.py` file or the root folder with `Python 3`.

Did you run into another error or a bug?
[Please let me know!](https://github.com/RandyParedis/GraphDonkey/issues)

### Copyright
* Icons for the GUI were made by [GlyphLab](https://glyphlab.com/).
(https://www.iconfinder.com/iconsets/common-toolbar)
* The `GraphDonkey` icon itself was custom-made by me. If you want to use it
elsewhere, you **must** reference this project.

### Changelog
* [0.0.2] Added Custom Icons + App Icon
* [0.0.2] Added flexible shortcut system
* [0.0.2] Editor now works solidly
* [0.0.1] Added ability to render the DOT from the Editor
* [0.0.1] Added Save functionality
  * Save a file to all Graphviz extensions
* [0.0.1] Added Open funtionality
  * From all DOT-file (text) extensions
* [0.0.1] Added New File functionality
* [0.0.1] Added Editor Line Highlighting + Line Numbers
* [0.0.1] Added Basic Editor (with Syntax Highlighting)

### Future Work
Below, I've listed all features I'd like to see in future versions.
[Feel free to suggest new ideas and features!](
https://github.com/RandyParedis/GraphDonkey/issues)

* [0.0.2] Add tests
* [0.0.2] Make app available via PyPI or as a downloadable app
  * i.e. standalone
* [0.0.3] Recent files menu
* [0.0.3] Syntax error highlighting
  * _Maybe via parsing in ANTLR?_
* [0.0.3] Automatic check for updates
* [0.1.0] Enable Github Pages
* [0.1.1] Custom user-options / preferences
  * Themes
  * Custom Shortcuts
* [0.1.2] Quick insert of special structures
  * Ability to create custom structures (i.e. code snippets)
* [0.1.3] Opening from as many file types as possible
* [0.1.3] Efficient Auto-Render
* [0.1.3] Additional configuration possibilities for graphviz
* [0.2.0] Interactive view of DOT files
  * Similar to XDot
  * Onclick of node: edit features
  * Quick connections
  * Should make Editor only useful for advanced features
* [0.2.1] Multiple Languages
* [0.2.1] Add Python scripting engine for live-showing of graph updates
  * This will allow container algorithms to be checked visually
  * Defaultly via 'open'?
  * Toggling of modes
  * How? Run python script and use all captured output as input for
graphviz.
