"""Module for parsing first-order logic CNF formulas"""

from .base import Atom, Clause, Literal
import re


class DimacsParser:
    """A parser for parsing DIMACS-formatted list of clauses"""

    def __init__(self):
        pass

    def parse(self, text):
        """Parse the specified DIMACS-formatted file into clauses"""

        pattern = r"(-?\d+)"
        clauses = list()
        clause = list()
        atoms = dict()

        for match in re.findall(pattern, text):
            result = int(match)
            if result == 0:
                clause = Clause(clause)
                clauses.append(clause)
                clause = list()

            else:
                name = str(abs(result))
                pos = result > 0
                if name not in atoms:
                    atoms[name] = Atom(name)

                literal = Literal(atoms[name], pos)
                clause.append(literal)

        return clauses
