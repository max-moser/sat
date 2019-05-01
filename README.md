# Simple SAT Solving Framework

This project was inspired by the lecture **Formal Methods in Computer Science** at the *Vienna University of Technology*.  
It provides an implementation of the SAT solving procedure introduced in the lecture.

The SAT instances (set of clauses) can be either set programmatically or parsed from a string in `DIMACS` format.

The aim of this project is to help with developing a better understanding of SAT solvers and their workings.  
Of course, pure Python is hardly a good choice for heavily CPU-bound tasks such as solving SAT problems.  
However, since this project is only intended for solving small instances, it should suffice.

## Requirements

`networkx`


## Basic Usage

The following code snippet shows 

~~~
import logging
import sat

# set the logging level for the module
logging.basicConfig(level = logging.INFO)

# provide a string in DIMACS format and parse the instance
# (x1 v x2) ^ (!x1 v !x2)
dimacs_string = "1 2 0 -1 -2 0"
instance = sat.parse_dimacs(dimacs_string)

# create an instance of the SAT solver
solver = sat.SimpleSatSolver("manual")

# set some hooks
solver.pre_bcp = lambda s: print("Doing Boolean Constraint Propagation!")
solver.post_bcp = lambda s: print("Boolean Constraint Propagation is done for now.")

# let the solver run and check if the instance is SAT
is_sat = solver.solve(instance)

if is_sat:
    # get the witnessing truth assignment as dictionary: STR -> BOOL
    # keys are the atom names, values are the assigned truth values
    assignment = solver.get_assignment()
    print(assignment)
~~~

## SimpleSatSolver

The `SimpleSatSolver` class takes a string as argument in its constructor.
This string specifies the heuristic strategy used for variable and value selection.  
It can be one of:

* `simple`: The lexicographically next atom will be used and its value will be set to `True`
* `dlis`: The **Dynamic Largest Individual Sum** heuristic is used
* `manual`: The user will be queried for a decision


## Drawing the Implication Graph

Since the implication graph is based on `networkx`, the graph can be drawn relatively easily using `networkx` and `matplotlib`.

The following code snippet shows how the implication graph can be drawn, using the solver's hooks.

~~~
import matplotlib.pyplot as plt
import networkx as nx

def draw_graph(solver):
    # fetch the graph from the solver
    graph = solver.implication_graph.graph

    # create a spring layout and draw the graph, with its labels
    spring_layout = nx.spring_layout(graph)
    nx.draw(graph, pos=spring_layout)
    nx.draw_networkx_labels(graph, pos=spring_layout)
    nx.draw_networkx_edge_labels(graph, pos=spring_layout)

    # show the created drawing
    plt.show()

# register a hook for drawing the graph
solver.pre_resolve_conflict = draw_graph
~~~
