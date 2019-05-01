"""A module for solving SATISFIABILITY problems.

The algorithms used are based on the lecture "Formal Methods of Computer Science" at Vienna University of Technology.
"""

from .parsing import DimacsParser
from .solvers import SimpleSatSolver
from collections import defaultdict


test_instance_string = "1 2 0 -1 -2 0 3 4 0 -2 4 2 0 -3 -4 0"


def parse_dimacs(text):
    return DimacsParser().parse(text)


def get_default_solver(*args, **kwargs):
    return SimpleSatSolver(*args, **kwargs)


def test():
    clauses = parse_dimacs(test_instance_string)
    solver = get_default_solver()
    solver.solve(clauses)
    return solver.get_assignment()


if __name__ == "__main__":
    parser = DimacsParser()
    clauses = parser.parse(test_instance_string)

    print(" ^ ".join((repr(c) for c in clauses)))
    solver = SimpleSatSolver()

    sat = solver.solve(clauses)
    print("SAT:", bool(sat))
    if sat:
        print("witnessing assignment:")
        print("\t", sat)