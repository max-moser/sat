"""Classes for the implication graph"""

from .base import Atom, Literal, Clause
from typing import List, Set, Tuple
import networkx as nx


class DecisionNode:
    """A node in the implication graph, denoting a decision"""

    def __init__(self, variable, value, decision_level):
        self.variable = variable
        self.value = value
        self.decision_level = decision_level

    def __repr__(self):
        prefix = " " if self.value else "!"
        return "[Decision: %s%s @ %s]" % (prefix, self.variable, self.decision_level)

    def __str__(self):
        return repr(self)

    def __hash__(self):
        return hash(self.variable) * 137 + hash(self.decision_level) * 151 + hash(self.value)


class ConflictNode:
    """A node in the implication graph, denoting a conflict"""

    def __init__(self, variable, decision_level):
        self.variable = variable
        self.decision_level = decision_level

    def __repr__(self):
        return "[Conflict: %s @ %s]" % (self.variable, self.decision_level)

    def __str__(self):
        return repr(self)

    def __hash__(self):
        return hash(self.variable) * 157 + hash(self.decision_level)


class ImplicationGraph:
    """The implication graph, used by SAT solvers"""

    def __init__(self):
        self.graph = nx.DiGraph()
        self.decisions = []
        self.conflict_node = None


    def add_decision(self, atom: Atom, value: bool, decision_level: int) -> None:
        """Add a decision node for a freely chosen decision"""

        decision_node = DecisionNode(atom, value, decision_level)
        self.decisions.append(decision_node)
        self.graph.add_node(decision_node)


    def add_forced_decision(self, atom: Atom, value: bool, antecedent: Clause, decision_level: int) -> None:
        """Add a decision node for a decision forced in BCP"""

        decision_node = DecisionNode(atom, value, decision_level)
        self.graph.add_node(decision_node)

        for literal in filter(lambda l: l.atom != atom, antecedent):
            # for each already fixed variable in the clause (i.e. each one except for the current variable)
            # find the vertex in the implication graph where the decision has been made
            previous_decision = next(filter(lambda n: n.variable == literal.atom, self.graph.nodes()))
        
            # and add an edge from the predecessor to the current node, labelled with the antecedent
            self.graph.add_edge(previous_decision, decision_node, antecedent=antecedent)
        

    def add_conflict(self, atom: Atom, clause: Clause, decision_level: int) -> None:
        """Add a conflict node arising from the given atom and clause"""

        conflict_node = ConflictNode(atom, decision_level)
        self.conflict_node = conflict_node
        self.graph.add_node(conflict_node)

        for literal in clause:
            previous_decision = next(filter(lambda n: n.variable == literal.atom, self.graph.nodes()))
            self.graph.add_edge(previous_decision, conflict_node, antecedent=clause)


    def find_uips(self) -> List[DecisionNode]:
        """Find all UIPs for the latest conflict"""

        if self.conflict_node is None:
            return None
        
        if not self.decisions:
            return None

        # UIPs are the points through which all possible paths from the current decision lead
        paths = nx.all_simple_paths(self.graph, self.decisions[-1], self.conflict_node)
        common_nodes = list(filter(lambda n: n != self.conflict_node, next(paths)))
        for path in paths:
            common_nodes = list(filter(lambda n: n in common_nodes, path))

        return common_nodes


    def find_first_uip(self) -> DecisionNode:
        """Find the first UIP for the latest conflict"""

        uips = self.find_uips()
        if uips:
            return uips[-1]

        return None


    def get_conflict_information(self, first_uip: DecisionNode) -> Tuple[Set[Clause], List[int]]:
        """Find the (sorted) decision levels involved in the latest conflict"""

        antecedents = set()
        decision_levels = set()

        successors = successors = self.graph.successors(first_uip)
        edge_data = nx.get_edge_attributes(self.graph, "antecedent")

        # find the antecedents in the conflict graph
        for successor in successors:
            decision_levels.add(successor.decision_level)

            for predecessor_edge in self.graph.in_edges(successor):
                antecedents.add(edge_data[predecessor_edge])
                decision_levels.add(predecessor_edge[0].decision_level)

        # sort the involved decision levels
        sorted_decision_levels = sorted(decision_levels, reverse=True)

        return antecedents, sorted_decision_levels
        

    def clear_decisions(self, last_decision_level_to_keep: int) -> None:
        """"Clear all nodes in the implication graph with a higher decision level than the one specified"""

        while len(self.decisions) > last_decision_level_to_keep:
            self.decisions.pop()

        nodes_to_delete = set()
        for node in self.graph.nodes():
            if node.decision_level > last_decision_level_to_keep:
                nodes_to_delete.add(node)
                node.variable.value = None

        for node in nodes_to_delete:
            self.graph.remove_node(node)
