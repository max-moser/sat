"""Basic classes for SAT solving"""

from __future__ import annotations
import itertools


class Atom:
    """An atom is basically a variable"""

    def __init__(self, name: str, value=None):
        self.name = name
        self.value = value

    def has_value(self):
        return self.value is not None

    def __repr__(self):
        return str(self.name)

    def __hash__(self):
        return hash(self.name)

    def __eq__(self, other):
        return self.name == other.name

    def __ne__(self, other):
        return not self == other

    def __bool__(self):
        return bool(self.value)


class Literal:
    """A literal is a positive or negative atom"""

    def __init__(self, atom: Atom, is_positive: bool):
        self.atom = atom
        self.positive = is_positive

    def has_value(self) -> bool:
        return self.atom.has_value()

    def __repr__(self):
        return repr(self.atom) if self.positive else "!%s" % self.atom

    def __bool__(self):
        return bool(self.atom) if self.positive else not bool(self.atom)

    def __eq__(self, other):
        return self.atom == other.atom and self.positive == other.positive

    def __ne__(self, other):
        return not self == other

    def __hash__(self):
        return hash(self.atom) * 43 + hash(self.positive)


class Clause:
    """A clause is a disjunct of literals"""

    def __init__(self, literals):
        self.literals = literals

    def is_satisfied(self) -> bool:
        """Check if any of the occurring literals is satisfied"""

        return any(filter(lambda l: l.has_value(), self.literals))

    def is_unsatisfied(self) -> bool:
        """Check if all of the occurring literals evaluate to false"""

        if not all(map(lambda l: l.has_value(), self.literals)):
            # if there are still unassigned variables in the clause,
            # then it cannot be unsatisfied yet
            return False

        return not any(self.literals)

    def is_unit(self) -> bool:
        """Check if there is exactly one undecided literal in the clause"""

        assigned_literals = [literal for literal in self.literals if literal.has_value()]
        if len(assigned_literals) == (len(self.literals) - 1):
            return not any(assigned_literals)
        
        return False

    def is_unresolved(self) -> bool:
        """Check if the clause is neither satisfied, unsatisfied nor unit"""

        return not self.is_satisfied() and not self.is_unsatisfied() and not self.is_unit()

    def resolve(self, other: Clause) -> Clause:
        """Use resolution on this clause with another clause and return the resolvent"""

        positive_literals = set()
        negative_literals = set()
        for literal in itertools.chain(self.literals, other.literals):
            if literal.positive:
                positive_literals.add(literal)
            else:
                negative_literals.add(literal)

        resolvent_literals = list(filter(lambda p: p.atom not in map(lambda n: n.atom, negative_literals), positive_literals))
        resolvent_literals.extend(list(filter(lambda n: n.atom not in map(lambda p: p.atom, positive_literals), negative_literals)))

        return Clause(resolvent_literals)

    def __repr__(self):
        representation = " v ".join(map(repr, self.literals))
        representation = "(%s)" % representation
        return representation

    def __bool__(self):
        return self.is_satisfied()

    def __iter__(self):
        return iter(self.literals)
    
    def __len__(self):
        return len(self.literals)

    def __hash__(self):
        return sum(map(hash, self.literals))
