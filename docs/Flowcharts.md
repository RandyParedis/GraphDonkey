# Pseudocode / Flowcharts
One of the new filetypes possible in the editor is _pseudocode_. Pseudocode is no
complex new language, but a set of basic keywords (that are used by all major
languages these days) joined together with natural language for upmost
readability. This allows pseudocode to be readable and understandable by anyone
and makes it possible to implement it easily in any language.

_Flowcharts_ are a graphical representation of programs and algorithms. They make
it easier for code to be understood. Using a very clean and streamlined graphical
representation, one can easily identify how the code works.

Because `GraphDonkey` is first and foremost a texteditor/IDE and flowcharts
aren't, the decision was made to generate flowcharts from pseudocode, seeing as
they both represent the same, albeit it visual for flowcharts and textual for
pseudocode.

Within this file, the different functionalities of the pseudocode/flowchart
system are explored and explained, so users can quickly find how to do certain
things. But beforehand, it is important to note that pseudocode is based on
**natural language** and therefore does not necessarily follow a specific syntax
or structure. This is why `GraphDonkey` uses a structured form of pseudocode,
based on the most common syntaxes.

As always, if you have any questions, issues and/or ideas concerning this part
of the editor, don't hesitate to [let me know](
https://github.com/RandyParedis/GraphDonkey/issues). You can also take a look at
all issues that were labeled with `filetypes`.

## Documentation
### Comments
It is good practice to comment all code you are using. This is not only for
your own sake, but also the other people that read your code, especially
pseudocode. With that in mind, you would be recommended to use `C`-style comments
in the editor. They are either single lines, preceded with two slashes (`//`), or
multilines, encapsulated as usual (`/*...*/`).

### States and Operations
A _state_ is a standalone instance. This can be either a single word (called a
_name_), or a group of words (called a string), encapsulated in single quotes
(`'...'`), double quotes (`"..."`) or backticks (`` `...` ``). Within these
strings, POSIX newline characters (`\n`) may be used to create states with
multiple lines. Note that the quotes will be removed in the actual flowchart, but
they can be embedded in other quotes.

States may be followed with a semicolon (`;`), as is common in `Basic`-based
programming languages.

Additionally, states can be extended to _assignments_, where a name is assigned
to another state via making use of the allowed assignment operators. Simple
assignments can be made using the equals sign (`=`) and mathematical definitions
can be set using a colon-equals (`:=`).
```
name_a = "some string";     // name_A is set to hold the string "some string"
name_b = 4.36;              // Numbers may be used as well
name_c := 16.4;             // Mathematical definition
name_d = "another example"  // Semicolons are optional
```

Not only can you _assign_ a single value, but you can use mathematical equations
and operators for your goals. These operators include addition (`+`), subtraction
(`-`), multiplication (`*`), division (`/`), exponentials (`^`) and modulo
(`%` or `mod`). Note that these are not evaluated on execution, but rather
transformed to a string before being displayed. Additionally, all these 
_operators_ (besides the `mod`-word itself) can be followed by an equals sign to
be used as a self-assignment.

Within the mindset of self-assignments, you can also use the incrementors 
(`inc`, `increment` or `++`) or decrementors (`dec`, `decrement` or `--`) before
a state as a special statement. (The `++` and the `--` may also be placed behind
the state instead.)
```
name_a += 5.16
name_b -= -79
name_c %= "it does not have to make sense"
name_d ^= name_c
inc name_a
decrement name_e
name_f ++
name_g := "interesting" += 9 /= `test` mod -.236    // also valid
```

As you may see in the final example, _assignments_ may be chained.

### Input / Output
### Tests / Conditional statements
### Loops
### Special states
* break/continue
* Return

### Preprocessor
