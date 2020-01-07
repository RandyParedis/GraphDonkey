# Pseudocode / Flowcharts
One of the new filetypes possible in the editor is _pseudocode_. Pseudocode is
no complex new language, but a set of basic keywords (that are used by all major
languages these days) joined together with natural language for upmost
readability. This allows pseudocode to be readable and understandable by anyone
and makes it possible to implement it easily in any language.

_Flowcharts_ are a graphical representation of programs and algorithms. They
make it easier for code to be understood. Using a very clean and streamlined
graphical representation, one can easily identify how the code works.

Because `GraphDonkey` is first and foremost a texteditor/IDE and flowcharts
aren't, the decision was made to generate flowcharts from pseudocode, seeing as
they both represent the same, albeit it visual for flowcharts and textual for
pseudocode.

Within this file, the different functionalities of the pseudocode/flowchart
system are explored and explained, so users can quickly find how to do certain
things. But beforehand, it is important to note that pseudocode is based on
**natural language** and therefore does not necessarily follow a specific
syntax or structure. This is why `GraphDonkey` uses a structured form of
pseudocode, based on the most common practices. All keywords are evaluated
in a case-insensitive manner.

As always, if you have any questions, issues and/or ideas concerning this
part of the editor, don't hesitate to [let me know](
https://github.com/RandyParedis/GraphDonkey/issues). You can also take a look
at all issues that were labeled with `filetypes`.

With the AST-visulization feature added in v0.1.3, you can also take a peek at
the parse tree that is built and maybe deduce some issues there.

## Documentation
### Comments
It is good practice to comment all code you are using. This is not only for
your own sake, but also the other people that read your code, especially
pseudocode. With that in mind, you would be recommended to use `C`-style
comments in the editor. They are either single lines, preceded with two slashes
(`//`), or multilines, encapsulated as usual (`/*...*/`).

This syntax will also be used to provide additional explanation with code
examples in the rest of this file.

### States and Operations
#### States
A _state_ is a standalone instance, shown inside of a single node. The simplest
example of this is a single word (later referred to as a _name_). This can be
typed without any further ado, as long as it only consists of letters,
underscores and numbers (as long as they are not the first character), which
is the main syntax used by most programming languages for variable names.

A state may also be any kind of numeric value, following the main dot syntax
thereof:
```
-.0001569
.12
16
-99.9999
163.
00023
```

It becomes more complex once you require multiple words, grouped together as
one, multiple lines, or special characters. This can be obtained via the
usage of _strings_. A string is any sequence of characters, encapsulated in
single quotes (`'...'`), double quotes (`"..."`) or backticks (`` `...` ``).
Strings may span multiple lines.

Within these strings, POSIX newline characters (`\n`) or HTML line breaks
(`<br/>`) may be used to create states with multiple lines. On top of that, you
may use [Graphviz HTML-like syntax](
https://graphviz.gitlab.io/_pages/doc/info/shapes.html#html) inside of these
strings to format your text. You don't have to type the encapsulating angle
brackets (`<...>`) for this to work.

Note that the quotes will be removed in the actual flowchart, but they can be
embedded in other quotes, or added by preceding them with a backslash (`\`).
(All other escape sequences are ignored.)

States may be followed with a semicolon (`;`), as is common in `Basic`-based
programming languages, but this is not required.

#### Operations
Before I continue, it is important to denote the following: any formula,
equation or computation is **not** evaluated. It's left up to the user to decide
if certain equations make sense or not. The syntax I am describing here is some
basic syntactic sugar that prevents the necessity to place everything in
strings and is encouraged to be used, but not required.

States can be extended to _assignments_, where a name is assigned
to an _operation_ via making use of the allowed assignment operators. Simple
assignments can be made using the equals sign (`=`) and mathematical definitions
can be set using a colon-equals (`:=`).
```
name_a = "some string";     // name_A is set to hold the string "some string"
name_b = 4.36;              // Numbers may be used as well
name_c := 16.4;             // Mathematical definition
name_d = "another example"  // Semicolons are optional
```

As shown above, the most simple operation is a single state, but it does not
have to be. You may use mathematical operators between the states of an
operation. These operators include addition (`+`), subtraction (`-`),
multiplication (`*`), division (`/`), exponentials (`^`), the dot operator
(`.`), similarity (`~`) and modulo division (`%` or `mod`). Additionally, all
these _operators_ (besides the `mod`-word itself) can be used in an assignment
for self-assignment.

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
name_g := "interesting" + 9 / `test` mod -.236    // also valid
```

As you may see in the final example, _assignments_ may be chained and do not
have to make sense. To increase readability, you may use the parentheses
(`(...)`), the bracktes (`[...]`) and/or the braces (`{...}`) to encapsulate the
operations themselves.

### Input / Output
Most software outputs or shows results of a computation or the execution of an
algorithm. This is considered the _output_. Often, this output is determined
by some user interaction via some _input_. This is represented in flowcharts
via the use of parallelogram nodes. To use them, you can simply type `input` or
`output`, followed by an optional state and (again) and optional semicolon.

As you can see in the result, both `input` and `output` are displayed in bold
and if you add additional information, a colon was added behind the keyword and
the information is printed behind it. Note that both keywords are
case-insensitive.

```
input "Wait for key press..."   // Shows "input: Wait for key press..."
Output "Key was pressed";       // Shows "Output: Key was pressed"
OUTPUT                          // Shows "OUTPUT" in bold
```

Because of this styling, if you're using strings, they may be html-like strings,
w.r.t. the [graphviz documentation](
https://graphviz.gitlab.io/_pages/doc/info/shapes.html#html) (note that you do
not have to encapsulate them with the less than and greater than signs
(`<...>`)).

### Tests / Conditional Statements
Not all code has a single flow from a start to an end. There can be branches
and conditional executions. As is common in most programming languages, they
can be introduced with the usage of an `if`-`then`-`else`-statement.

In flowcharts, such a condition is represented with a diamond shape from where
two arrows (labeled `Yes` and `No`) leave. Let's give an example:

```
If "some statement is considered to be true" THEN;  // semicolon is optional
    // Do something for this condition
    output "this statement was true!"
Fi;  // End the if-block, may also be 'end' or 'end if', semicolon is optional
```

The condition that is evaluated can not only be a state, but it may be a
comparison of multiple states. Different comparisons include less than (`<`),
greater than (`>`), less than or equals (`<=`), greater than or equals (`>=`),
equals (`==`), not equals (`!=` or `<>`), and (`and` or `&&`), or
(`or` or `||`), containment (`in`) and identity (`===` or `is`). Similar to the
operations, groups of comparisons may be encapsulated with parentheses, brackets
and/or braces.

Additionally, an `if` may be followed by an `else` to show alternatives:
```
if (statement1 <> statement2) then
    output "They are not equal!"
else
    output "They are equal!"
end if
```

More alternatives can be obtained via chaining `if`s together:
```
if {myvar is 1} then        // Encapsulation with braces
    output "myvar = 1"
elif myvar is 2 then        // Python Style
    output "myvar = 2"
else if myvar < 10 then     // Generic Style
    output "myvar < 10"
else
    output myvar
end
```

### Loops
Often, we do not only use branches in flowchart, but also iterative processes.
This means the same set of statements is called over and over again. This is
shown visually with an arrow back to a previous node and textually with the
usage of _loops_.

The `while` loop is the most common loop of them all (and technically
every loop out there can be reduced/expanded to this kind of loop). It is
technically a simple `if`-`then`-statement, but instead of continueing after
the block was completed, we return to the original condition. Instead of an
else, the loop is broken.

```
while x > 12 ? Do;
    dec x
dOne;  // All keywords are case-insensitive, allowing this
```

Occasionally, it might be useful to use a `while true` or infinite loop, also
known as a _gameloop_. These can be done by omitting the `while` keyword and
the condition:
```
do;
    "Executing game loop"
done;
```

Loops do not always have to be broken when the condition fails, but may be
altered mid-execution (even though some may believe this is bad practice). This
can be done with the `break` and `continue` statements that are often part of
programming languages. `Continue` will force the execution to jump to the next
test statement and `break` will forcibly break out of the loop and jump to the
next statement to execute (after the loop). Note that these may only be used
inside of loops.

### Special Statements
#### Return
You may have spotted that all flowcharts are deeply connected, i.e. all branches
join together once more at some point in time. This is not always the case with
code. To end the current flowchart at a specific point in time, make use of the
`return`-statement. When used standalone, a new `end` node is created and the
rest of the current branch is ignored (similar to a `break`).

When followed by a state, the label of the newly generated node will be that of
this state.

#### Preprocessor Statements
Some properties of the flowchart are hardcoded, which is bad-practice in my
honest opinion. This is why there are some so-called _preprocessor_ statements
possible. Note that "preprocessor" does not denote that the file is executed 
twice (as is done by `C` and `C++` compilers), but that these must be located
at the top of the file, so they can be processed before all the other
statements.

They have a simple structure: a percentage sign (`%`) followed by a 
case-insensitive name, followed by an equals sign (`=`) or a colon (`:`),
followed by a string or a name. They allow users to define some additional
functionalities for their graphs. Please be aware that the percentage sign must
be at the beginning of a line. They may be ended with a semicolon.

Invalid preprocessor statements are ignored for now and the valid ones are:
```
// The label for the edges of a condition when it is considered true
% True: "Yes"

// The label for the edges of a condition when it is considered false
% FALSE: "No";

// The graphviz graph splines attribute, usually either 'polyline' or 'ortho'
% splines: "polyline"

// The value of the start node. When the value is a name and either 'no', 'off'
//   or 'false' (case-insensitive), no special start node will be shown.
% start: "start"
```
