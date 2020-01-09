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
on the plugin system, please leave it [here](
https://github.com/RandyParedis/GraphDonkey/issues), so it can be reviewed by
other users and developers.

## What can be done with plugins?
Within the scope of the `GraphDonkey` app, a plugin is either a rendering
engine (complete with possible preferences), a file reference (including syntax
and semantic checking) or both. In fact, for generality, it contains a _set_
of file references and a _set_ of engines.

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
numbers and websites that contain more info.

For instance, the bundled `graphviz` plugin has the following docstring:
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

#### imports
All import statements used in your plugin must assume the project root is the
root of the repo. For instance:
```
# Imports the constants from the main project
from main.extra import Constants

# Import the all objects from the Engine module in the myplugin plugin
from vendor.plugins.myplugin.Engine import *
```
