# GraphDonkey

<img align="left" width="180" height="180" src="vendor/icons/graphdonkey.svg">

`GraphDonkey` is an easy-to-use texteditor that allows for visualizing textual
notations. If you have a language that can be expressed visually, there is a high
chance `GraphDonkey` has got you covered!

Ever gotten tired of the overly complicated use of multiple tools for visualizing
and developing languages, models, graphs...? Not anymore! That's all in the past
with `GraphDonkey`.

Simply type your text in the editor, enjoy its user-friendly features and see your
code come to life in the visualizer.

**Latest Release Version:** _Jack-in-a-Box_ (`v0.2.0`)<br/>
**Executable OS:** Only `Linux` at this point in time
(maybe Mac as well, but cannot confirm)<br/>
**Author:** Randy Paredis

### Features
There are a lot of features `GraphDonkey` has to offer, all of them for your
ease of use! Let's list some of them:
* See all your languages as they were meant to be seen with the highly
customizable syntax highlighter!
* You've written an error and don't know where? No longer! Because `GraphDonkey`
is able to display both syntactical and semantical errors, so you can detect the
issues in an instant!
* Ever gotten tired of moving your mousecursor while working with a GUI? I know I
have. The superflexible shortcut system allows you to assign a shortcut to
any possible functionality.
* We all like to take a look under the hood, see what's going on in the bare bones
of the tools you're using. Now you can! The builtin AST viewer allows custom
language makers to immediately have a good overview of what's going on. In fact,
if something is not working and you're pretty sure what you're doing, you might
find an issue this way.
* Not a fan of light themes? No problem! Under "_Preferences > Theme and Colors_"
you can change all the colors and styles that are used in the editor. What's that
you say? You don't want to go through the bothersome task of hand-picking colors
until they fit? You don't have to! `GraphDonkey` comes bundled with five patiently
selected, visually appealing themes, based on the ones you know and love from
other editors. And it doesn't have to end there! You can adapt themes or create
completely new ones and save them for future use or share with the community.
* `GraphDonkey` comes bundled with a clean and simple snippet system, for saving
your favorite codes for future use, combined with an autocompletion system, in
case you've forgotten what to type.
* Adding your own (domain specific) languages was never this easy! Use the builtin
[lark][lark] parser to create your grammars without needing to bother about
anything else!
* Export your graphs and visualizations with the press of a button! No more need
for remembering the right commands!
* ... and so much more!

Does that tickle your fancy? Yes? Excellent! What are you waiting for? Get
`GraphDonkey` now!

Wait... did you say no? There is so much more left to see and discover that you
cannot possibly know that! So go ahead and get `GraphDonkey`, I'm convinced you'll
be amazed!

### Bundled with
By default, `GraphDonkey` comes bundled with:
* The [Graphviz][gv] rendering engine to bring your graphs to life, complete with a
full grammar checker for the `Graphviz dot` language.
* A [Flowchart / Pseudocode](wiki/Flowcharts.md) language that not only allows you
to type clean and understandable pseudocode, but also see it visualized as a
flowchart.

### Want to Learn More?
Take a look at the [wiki](wiki/Home.md) and allow `GraphDonkey` to do the donkey
work for you!

### Copyright
It's important to list your sources if you're working on a project. One does not
have to reinvent the wheel, but rather list the blueprint that was used in
creating it.
* Icons for the GUI came from the [qtango GitHub project](
https://github.com/ppinard/qtango)
* The `GraphDonkey` icon, themes and source code were custom-made by me. If you
want to use it elsewhere, you **must** reference this project.
[See also the license.](LICENSE)


[lark]: https://github.com/lark-parser/lark
[gv]: https://www.graphviz.org/
