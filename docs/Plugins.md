# Plugins

Software should not be a mess of hardcoded features. In fact, it grows and
changes over time. On top of that, some users of the software might ought it
important for very specific features to be part of a bigger whole.

This is usually done with _plugins_ or _addons_.

Because not everyone might be on board with the Graphviz rendering engine
(there are many others out there), or people want to provide easy support for
their custom domain specific language (DSL) in GraphDonkey, the decision was
made to embed a plugin system.

The goal was to make this as extensive and expandable as possible, while
maintaining a good base for future releases. If you have any issues or thoughts
on the plugin system, please leave it [here][1], so it can be reviewed by
other users and developers.

## What can be done with plugins?
Within the scope of the `GraphDonkey` app, a plugin is either a rendering
engine (complete with possible preferences), a file reference (including syntax
and semantic checking) or both. In fact, for generality, it contains a _set_
of file references and a _set_ of engines.

## General System Workflow
To demonstrate how plugins are used and how all information that's mentioned below
will be combined together, take a look at this schematic representation:
...



## Plugin File Structure
A plugin has a root folder that must be located in the `vendor/plugins`
directory. Each such folder contains a number of documents that are necessary
for the plugin to work. There must be **at least** an `__init__.py` file that
contains the plugin details as defined below. Note that you don't have to have
a python interpreter for your plugin to work with the `GraphDonkey` executable!
Isn't that amazing?

Experienced programmers might be aware that python allows you to execute any
command. This makes it so the plugins don't necessarily have to be written in
python, as long as they're linked correctly. On the other hand, this can be a
massive security risk. **Do not use plugins that come from untrusted sources!**
I am not responsible for any malicious plugins that exist out there. When in
doubt ask an experienced user from the community to take a look at it.

### \_\_init__.py
This file is the only required file in a plugin folder. Theoretically, it is
not necessary for other files to exist, but may help in clarity. This file
has the following parts (usually denoted in the order they are listed here):

#### \_\_doc__
The docstring at the beginning of your file allows you to name your plugin,
give a description and denote authorship/copyright at the same time.

The text on the first line is seen as the plugin name, which is followed by any
number of empty lines, before the description starts. Usually, you end this
description with a set of quick references, like copyright, dates, version
numbers and websites that contain more info or documentation. Finally, you may end
with as many empty lines as you like.

The existance of such a docstring is required for the plugins to flawlessly work
together. Please be aware that the name of a plugin must be **unique** between all
enabled plugins in the system.

For instance, the bundled `Graphviz` plugin has the following docstring:
```
"""Graphviz

Render graphs in Graphviz/Dot format.

Graphviz is open source graph visualization software. Graph visualization is a way of
representing structural information as diagrams of abstract graphs and networks. It has
important applications in networking, bioinformatics,  software engineering, database
and web design, machine learning, and in visual interfaces for other technical domains.

Website:    https://www.graphviz.org/
Author:     Randy Paredis
"""
```

#### Imports
Often, one may require additional information for a plugin to work. Maybe, a [set of
predefined constants](Contants.md) might help in developing your plugin.

All import statements used in your plugin must assume the project root is the
root of the repo. For instance:
```
# Imports the constants from the main project
from main.extra import Constants

# Import the all objects from the Engine module in the myplugin plugin
from vendor.plugins.myplugin.Engine import *
```

#### TYPES
With an optional `TYPES` variable, a set of DSLs can be identified. This includes
syntax highlighting, syntax checking, semantics checking and much more.

`TYPES` is a dictionary of dictionaries. Each internal dictionary has a unique
file type name and a set of values w.r.t. the DSL defined by the given file type
name. Let's call such an internal dictionary a _DSL description_. There are multiple
DSL descriptions possible for each plugin.

A DSL description consists of the following keys:
* `extensions`: A list of extensions that can be opened with this DSL. If multiple
DSL use the same extensions, the first loaded DSL will be selected upon opening
a file of that type. Technically, this field is optional, but it's encouraged to
use it anyways.
* `grammar`: Optionally provide a [lark](https://github.com/lark-parser/lark)
grammar file to use for syntax analysis of the file and building of an AST. The
base path for this file is the plugin's root directory.
* `parser`: The [lark](https://github.com/lark-parser/lark) parser to use
(as a string), can be one of `early`, `lalr` or `cyk`. Defaults to `early`.
* `semantics`: A classname that can be used to do semantic analysis of a parse
tree. This class must ideally inherit from `main.editor.Parser.CheckVisitor`. We
refer to [this class' documentation](../main/editor/Parser.py) and the bundled
`vendor.plugins.graphviz.CheckDot` class for more information.
* `highlighting`: A list of highlighting rules, ordened to their importance (i.e.
rule 1 will be applied first, next rule 2, afterwards rule 3...). Such a rule is
identified with another dictionary containing the following keys.
    * `format`: The highlighting format to use, which are linked to the
    user preferences. This can be one of the following (see also the
    "_Theme and Colors_" preferences in the app):
        * `keyword`: For showing keywords in your language.
        * `attribute`: For specifying attributes or sub-keywords.
        * `number`: For identifying numbers in your code.
        * `string`: For indicating strings in your DSL.
        * `html`: For indicating HTML-like strings.
        * `comment`: For comments.
        * `hash`: For preprocessing macro's and/or hashes used in code. Can also
        be used as a special kind of comment.
        * `error`: For underlining a certain word with an error line. While
        possible, this value should be considered bad practice.
    * `regex`: Optional, but when omitted the `start` and `end` keys need to be
    present. Indicates the regex to use. This is either a pattern string (see
    below), or yet another dictionary.
        * `pattern`: The pattern string to use. This is a 
        [`QRegExp`](https://doc.qt.io/archives/qt-4.8/qregexp.html) pattern, as
        defined in the `Qt` documentation.
        * `caseInsensitive`: Optional. When `True`, the pattern will be checked
        case-insensitively.
    * `start`: Must be present if `regex` is absent. Used to indicate multiline
    highlights. Accepts the same as the `regex` key and indicates the start of
    your multiline match.
    * `end`: Must be present if `regex` is absent. Used to indicate multiline
    highlights. Accepts the same as the `regex` key and indicates the end of
    your multiline match.
    * `exclude`: When `start` and `end` are present, this regex indicates which
    pattern to ignore in a multiline match. Accepts the same as the `regex` key.
* `converter`: A mapping (dictionary) of an engine name (see below) to a function
representing the input for the engine. This allows multiple engines to be used for
the same DSL. The function has two parameters `text` and `tree` and must return a
string that can be used as an input for the engine. `text` represents the text
inside the editor window and `tree` is the AST thereof.<br/>
(Hint: the AST can be seen in the editor via "_View_ > _View Parse Tree_")<br/>
If your DSL has its own rendering engine that accepts the language as-is (without
looking through the AST), `lambda x, T: x` is enough for this function. When this
value is undefined, or the function returns `None`, no rendering is performed.
    
Below, you can find a working example, taken from the `graphviz` plugin:
```
TYPES = {
    "Graphviz": {
        "extensions": ["canon", "dot", "gv", "xdot", "xdot1.2", "xdot1.4"],
        "grammar": "graphviz.lark",         # Defined in the current directory
        "parser": "lalr",
        "semantics": CheckDotVisitor,       # This name is imported
        "highlighting": [
            {
                "regex": {
                    # In the file, there is a 'keywords' list of all keywords defined,
                    #  which are joined together in one big 'OR' operation.
                    "pattern": "\\b(%s)\\b" % "|".join(["(%s)" % x for x in keywords]),
                    "caseInsensitive": True
                },
                "format": "keyword"
            },
            ...
            {
                "regex": "\\b-?(\\.[0-9]+|[0-9]+(\\.[0-9]*)?)\\b",
                "format": "number"
            },
            ...
            {
                "start": "/\\*",
                "end": "\\*/",
                "format": "comment"
            }
        ],
        "converter": {
            "Graphviz": lambda x, T: x
        }
    }
}
```

#### ENGINES
Engines allow users to render in a specific way. Without this property, all DSLs
must be converted to a single uniform file reference, which in its turn can be
rendered flawlessly, but this cannot always be done. Some users swear by
`graphviz`, while others praise `PlantUML` instead. Long story short, this adds
more flexibility to the overall system.

This property is not required and therefore it can be ignored if you have no
desire for a custom rendering engine.

Let's take a quick look at an example, extracted from the `graphviz` plugin.
```
ENGINES = {
    "Graphviz": {
        "convert": convert,
        "preferences": {
            "file": "preferences.ui",
            "class": GraphvizSettings
        },
        "export": {
            "extensions": ['fig', 'jpeg', 'pdf', 'tk', 'eps', 'cmapx_np', 'jpe', 'ps', 'ismap', 'x11', 'dot_json', 'gd',
                           'plain', 'vmlz', 'xlib', 'pic', 'plain-ext', 'pov', 'vml', 'json0', 'cmapx', 'jpg', 'svg',
                           'wbmp', 'vrml', 'xdot_json', 'gd2', 'png', 'gif', 'imap_np', 'svgz', 'ps2', 'cmap', 'json',
                           'mp', 'imap'],
            "exporter": export
        }
    }
}
```

As you can see, `ENGINES` is constructed in a similar fashion to the `TYPES`
object. This allows for users to assign multiple engines within the same plugin.
Each engine is identified by a unique name that is refered to by the `converter`
key in the DSL descriptions defined in the `TYPES` object.

Each engine itself is specified with the following keys:
* `convert`: A function that takes a string as input and returns binary data as a
result. If this binary data is a valid `svg` file, it is rendered as such. If it's
another image type [that's recognized by Qt][2], it is rendered as a plain image.
This key is required.
* `preferences`: If you desire to have custom user-defineable settings in your
engine, you may use this key to indicate this. More information is given below.
* `export`: Your engine can allow for the exporting to numerous other file types
that can't necessarily be rendered, or to images if you want your user to be able
to save the images that your engine generates. This field allows for such export
possibilities.<br><br>
_Note that this method is not foolproof/perfect, especially if the rendering of
your images require some additional settings. Therefore this might be something
that gets a massive overhaul in a future version. If you have any thoughts on the
matter, please leave them [here][1]._<br><br>
Nevertheless, the `export` key is a dictionary that contains the following items:
  * `extensions`: A list containing all the file extensions you support exporting
  to. At the moment, a user can only export w.r.t. the currently selected engine.
  * `exporter`: A required function that takes `text` and `extension` as
  attributes and returns the binary data to write to a file, or `None`. The latter
  can be used as a shorthand to identify you cannot export to that file under the
  current circumstances. It will not throw an error (unless you tell it to) and
  instead fail silently. If it returns empty (binary) data, it will be assumed
  that `None` was returned. Otherwise, the core will successfully write away your
  file.

#### Preferences / Configuration
You may access the values from the _Preferences_ window for your own purpose. It is,
however discouraged to update and adapt them during execution. The set of
preferences, or (more specifically) the configuration list, can be obtained via
the following code:
```
from main.extra.IOHandler import IOHandler
Config = IOHandler.get_preferences() 
```
The `Config` object is a singleton of type
[`QSettings`](https://doc.qt.io/qt-5/qsettings.html).

If you desire to have your own preferences as an option in the plugin, you can do
so. Each engine section can hold the optional `preferences` key, which must hold
a `class` and a `file` key. The `file` refers to the ui file that's used in the UI
(assuming the plugin directory is the root directory) and describes a `QGroupBox`.
The `class` refers to a specific class, inheriting from the `main.plugins.Settings`
class and takes a `pathname` and `parent` as constructor arguments.

This subclass has a `preferences` member that refers to the `Config` singleton, as
described above and two member functions: `rectify` and `apply`. `rectify` needs to
set values from the `preferences` to the UI and `apply` does the opposite; it takes
values from the UI and stores them in the `preferences`. The preferences to be
added must be of the form `plugin/<plugin name>/<key>`, where `<plugin name>`
stands for your plugin name and `<key>` stands for the value you're actually
assigning.

Remember to add default values in the `rectify` method!

For more info, take a look at the `Settings` class in the bundled
`vendor.plugins.graphviz.Settings` module.


[1]: https://github.com/RandyParedis/GraphDonkey/issues
[2]: https://doc.qt.io/qt-5/qimage.html#reading-and-writing-image-files
