// The DOT language grammar as found online on:
//      https://graphviz.gitlab.io/_pages/doc/info/lang.html

start: graph
graph: STRICT? (GRAPH|DIGRAPH) ID? "{" stmt_list "}"
stmt_list: (stmt ";"? stmt_list)?
stmt: node_stmt | edge_stmt | attr_stmt | (ID "=" ID) | subgraph
attr_stmt: (GRAPH | NODE | EDGE) attr_list
attr_list: "[" a_list? "]" attr_list?
a_list: ID "=" ID (";" | ",")? a_list?
edge_stmt: (node_id | subgraph) edge_rhs attr_list?
edge_rhs: edgeop (node_id | subgraph) edge_rhs?
edgeop: DIOP | UNOP
node_stmt: node_id attr_list?
node_id: ID port?
port: (":" ID (":" compass_pt)?) | (":" compass_pt)
subgraph: ("subgraph" ID?)? "{" stmt_list "}"
compass_pt: "n" | "ne" | "e" | "se" | "s" | "sw" | "w" | "nw" | "c" | "_"


// case-independant keywords
NODE: "node"i
EDGE: "edge"i
GRAPH: "graph"i
DIGRAPH: "digraph"i
SUBGRAPH: "subgraph"i
STRICT: "strict"i

// distinguish between validity afterwards
DIOP: "->"
UNOP: "--"


NAME: /[a-zA-Z_][a-zA-Z0-9_]*/
NUMERAL: /[-]?(.[0-9]+|[0-9]+(.[0-9]*)?)/
STRING: /"[^"\\]*(?:\\.[^"\\]*)*"/
HTML: /<.*?>/

ID: NAME | NUMERAL | STRING | HTML
COMMENT_PRE: /^#[^\n]*/
COMMENT_SNG: "//" /[^\n]/*
COMMENT_MLT: "/*" /[^\n]|\n/* "*/"

%ignore /\s/+
%ignore COMMENT_PRE
%ignore COMMENT_SNG
%ignore COMMENT_MLT
