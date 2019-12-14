# DotGaper
A simple and easy-to-use application for visualizing and editing Graphviz
Dot files, running on `Python 3`. Behind the screens, it binds `PyQt5` and
`graphviz` together.

Current Version: `0.0.1`<br/>
Build Type: `beta`

### Requirements
* `PyQt5` (including `uic`)
* `graphviz`

### Installation
Installing `DotGaper` is quite easy. All you have to do is clone this
repository. Also make sure you have installed the `PyQt5` and `graphviz`
modules for `pip3`, which will allow this application to work.

_For future work, the goal is to make this available as an application on
either PyPI or as a bundled resource._

### Running `DotGaper`
When you've installed `DotGaper` as described above, you can just run the
`__main__.py` file or the root folder with `Python 3`.

### Known Bugs
* The _Graphviz Data Editor_ gets closed when the application is hidden
(minimized or on another workspace/desktop).
* Shortcuts work incredibly finicky.
  * Rendering with shortcuts when in the _Code Editor_ does not work.
  * Copying and Pasting via shortcuts don't work as expected. 
* Save indicator is not changed when a file was edited.
* Opening invalid file does the same as the _New_ action(s).

Did you run into another error or a bug? Please let me know via the
"_Issues_" page.

### Changelog
##### Version 0.1
* [0.0.1] Basic Editor (with Syntax Highlighting)
* [0.0.1] Line Highlighting + Line Numbers
* [0.0.1] Create a New File
* [0.0.1] Open an existing DOT-file
* [0.0.1] Save a file to all Graphviz extensions
* [0.0.1] Toggle the Editor
* [0.0.1] Render the DOT from the Editor

### Future Work
Below, I've listed all features I'd like to see in future versions. Feel
free to suggest new ideas and features via the "_Issues_" page.

##### Version 0.1
* [0.0.2] Solidly working Editor
* [0.0.2] Custom Icons + App Icon
* [0.0.3] Flexible Shortcut System
* [0.0.3] Recent files menu
* [0.0.4] Syntax error highlighting
  * _Maybe via parsing in ANTLR?_

##### Version 0.2
* [0.1.1] Custom user-options / preferences
  * Themes
  * Custom Shortcuts
* [0.1.2] Quick insert of special structures
  * Ability to create custom structures (i.e. code snippets)
* [0.1.3] Opening from as many file types as possible

##### Version 0.3
* Interactive view of DOT files
  * Similar to XDot
  * Onclick of node: edit features
  * Quick connections
  * Should make Editor only useful for advanced features
