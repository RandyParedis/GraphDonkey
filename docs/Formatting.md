# Formatting and File/Folder Structure
This page is mainly for [contributers](../CONTRIBUTING.md) to this repository and
describes a set of rules that all files must follow. This ensures readability,
visibility and clarity of changes and/or features while at the same time providing
a clean and uniform overview of the whole project.

If you find inconsitencies against these rules, don't hesitate to 
[fix it](../CONTRIBUTING.md) or 
[let us know](https://github.com/RandyParedis/GraphDonkey/issues)!

### Indentation and File Endings
Probably an unpopular opinion, but we prefer tab indentation over space
indentation.

Each file must end with an empty line.

### Folder Structure
#### Directory Tree
There are 4 main directories:
* `docs`: The root for all documentation and wiki, except for the obvious
[README.md](../README.md), [CODE_OF_CONDUCT.md](../CODE_OF_CONDUCT.md) and
[CONTRIBUTING.md](../CONTRIBUTING.md)
* `main`: Contains the main application and code.
* `tests`: While `GraphDonkey` is not tested enough, the very few tests that
exist must be located here.
* `vendor`: All additional and external files can be found here. They are included
in the bundled executable. These include:
  * `icons`: The set of icons used, which is the submodule
  [qtango](https://github.com/ppinard/qtango) at this current point in time.
  * `plugins`: The set of plugins installed
  * `styles`: The styles used for the app. Any user-specific styles are located
  here as well.
  * `ui`: `GraphDonkey` makes use of the `uic` compiler from `Qt`. This folder
  contains all the `*.ui` files that are used to build the layout.

#### Python Modules
While it's not important how modules are created, we prefer not using folders that
only contain a single `__init__.py` file.

### MarkDown Files
In general, markdown files don't require any thought, but if you decide to add
some, it is expected that each line does not span over 100 characters.

### Python Files
#### Docstrings
Python files themselves must start with a docstring ```"""..."""```. The first 
line of this docstring must be a short description of the file, followed by an 
empty line, followed by a longer description thereof. They must be ended with an 
`Author` and a `Date` reference. These references are followed by a colon and then 
a tab, before they are given their values.

```
"""Short Description

This is my long description of this file. Notice how there is
preferred to have many short lines over few long ones. Each
such line should be approximately indented on both sides (for
as far that's possible).

Author: Some Name Here
Date:   MM/DD/YYYY
"""
```

Notice how the date format is in `MM/DD/YYYY`, where `MM` represents a month by
number (two values, Januari is `01`), `DD` represents a day in two digits and
`YYYY` represents the usual 4-digit year.

Exceptions can be made for empty python files, as long as there is a short
description as to why it's empty (see [\_\_init__.py](../__init__.py) for an
example).

#### Imports
Imports may take any number of forms. The only import that is required to be
formatted validly is the import of the [constant values](Contants.md).
```
from main.extra import Constants
```
