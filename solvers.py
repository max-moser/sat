"""Module containing solvers for satisfiability problems"""


from .graph import ConflictNode, DecisionNode, ImplicationGraph
from .base import Atom, Clause, Literal
import networkx as nx
import logging


def canonize_clauses(clauses):
    """Create a canonical version of the clauses, where every same atom has the same reference"""

    variables = dict()
    new_clauses = list()

    # create a canonical version of each clause, i.e. use the same
    # object for each atom occurring in any clause, for easier housekeeping (side effects)
    for clause in clauses:
        clause_literals = list()

        for literal in clause.literals:
            atom = literal.atom
            if atom.name not in variables:
                variables[atom.name] = literal.atom

            # add the canonical version of the atom to the literals list
            canon_literal = Literal(variables[atom.name], literal.positive)
            clause_literals.append(canon_literal)

        clause = Clause(clause_literals)
        new_clauses.append(clause)

    return variables, new_clauses


class SatSolver:
    """The SAT solver takes any number of clauses and tries to find an interpretation that satisfies all of them."""

    def __init__(self):
        self.variables = dict()
        self.clauses = list()


    def solve(self, clauses):
        """Decide whether the given CNF formula is satisfiable or not"""

        variables, clauses = canonize_clauses(clauses)
        for var in variables.values():
            var.value = None

        self.variables = variables
        self.clauses = clauses
        return self.solve_internal()


    def solve_internal(self):
        """The function to override when implementing a SAT solver"""
        
        raise NotImplementedError()


    def get_assignment(self):
        """If the last run yielded a positive result for the SAT instance, return the witnessing assignment"""

        assignments = dict()
        for variable in self.variables.values():
            assignments[variable] = variable.value

        return assignments


class SimpleSatSolver(SatSolver):
    """SAT solver, based on the lecture Formal Methods in Computer Science at the Vienna University of Technology"""

    def __init__(self, decision_heuristic="simple"):
        self.__decide = self.decide_simple

        if decision_heuristic:
            heuristic = decision_heuristic.lower().strip()
            if heuristic == "dlis":
                self.__decide = self.decide_dlis
            elif heuristic == "manual":
                self.__decide = self.decide_manual

        def do_nothing(solver):
            pass

        # hooks before / after completion of `decide`, `bcp` and `resolve_conflict`
        self.pre_decide = do_nothing
        self.post_decide = do_nothing
        self.post_decide_true = do_nothing
        self.post_decide_false = do_nothing
        self.pre_bcp = do_nothing
        self.post_bcp = do_nothing
        self.post_bcp_true = do_nothing
        self.post_bcp_false = do_nothing
        self.pre_resolve_conflict = do_nothing
        self.post_resolve_conflict = do_nothing
        self.post_resolve_conflict_true = do_nothing
        self.post_resolve_conflict_false = do_nothing

        logging.info("created SimpleSatSolver using: %s" % self.decide.__name__)


    def solve(self, clauses):
        return super().solve(clauses)


    def solve_internal(self):
        """Decide whether the given CNF formula is satisfiable or not"""

        self.implication_graph = ImplicationGraph()
        self.decision_level = 0
        self.bcp()
        if not self.resolve_conflict():
            return False

        while True:
            self.decision_level += 1
            if not self.decide():
                return True

            while not self.bcp():
                if not self.resolve_conflict():
                    return False

    def decide(self):
        """Wrapper calling the hooks and actual decide function"""

        self.pre_decide(self)
        value = self.__decide()

        self.post_decide(self)
        if value:
            self.post_decide_true(self)
        else:
            self.post_decide_false(self)

        return value


    def decide_manual(self):
        """Decision procedure querying the user for input"""

        clauses = list(filter(lambda c: c.is_unresolved(), self.clauses))
        if not clauses:
            return False

        # find the variables without assigned values
        variables = set()
        for clause in clauses:
            for variable in filter(lambda v: not v.has_value(), clause):
                variables.add(variable.atom)

        print("unresolved clauses: %s" % ", ".join(map(lambda c: str(c), clauses)))
        var_names = ", ".join(map(lambda v: v.name, variables))
        ok = False
        while not ok:
            try:
                chosen = input("choose variable [%s]: " % var_names)
                chosen = chosen.strip()
                chosen_value = True

                # if a '!' was added as prefix, assign FALSE to the variable
                if chosen[0] == "!":
                    chosen_value = False
                    chosen = chosen[1:]

                var = next(filter(lambda v: v.name == chosen, variables), None)
                if var is None:
                    ok = False
                    print("could not find atom '%s'" % chosen)
                else:
                    ok = True

            except Exception as e:
                print("Error: %s" % e)
                ok = False

        var.value = chosen_value
        self.implication_graph.add_decision(var, chosen_value, self.decision_level)

        prefix = " " if chosen_value else "!"
        logging.info("dec: %s%s @ %s" % (prefix, var, self.decision_level))
        return True


    def decide_simple(self):
        """Simple decision procedure that sets the first undecided atom to true"""

        clause = next(filter(lambda c: c.is_unresolved(), self.clauses), None)
        if clause is None:
            return False

        # just use the first undecided variable and assign True to it
        variable = next(filter(lambda v: not v.has_value(), clause), None)
        variable.atom.value = True
        self.implication_graph.add_decision(variable.atom, True, self.decision_level)

        logging.info("dec:  %s @ %s" % (variable.atom, self.decision_level))
        return True


    def decide_dlis(self):
        """Choose the next variable and value, using the DLIS heuristic. Return False if all variables are assigned."""

        # DLIS heuristic for deciding on a variable / value
        pos_count = dict()
        neg_count = dict()
        count = 0
        
        # count the positive / negative occurrences of each (undecided) variable
        for clause in filter(lambda c: c.is_unresolved(), self.clauses):
            count += 1
            for literal in filter(lambda v: not v.has_value(), clause):
                atom = literal.atom
                if literal.atom not in pos_count:
                    pos_count[atom] = 0
                    neg_count[atom] = 0

                if literal.positive:
                    pos_count[atom] += 1
                else:
                    neg_count[atom] += 1

        if count == 0:
            return False
        
        # find the variable with the most occurrences
        max_pos = max(pos_count, key=lambda k: pos_count[k])
        max_neg = max(neg_count, key=lambda k: neg_count[k])
        chosen = max_pos if pos_count[max_pos] > neg_count[max_neg] else max_neg

        # decide on the value
        value = pos_count[chosen] > neg_count[chosen]
        chosen.value = value
        self.implication_graph.add_decision(chosen, value, self.decision_level)

        prefix = " " if value else "!"
        logging.info("dec: %s%s @ %s" % (prefix, chosen, self.decision_level))
        return True


    def bcp(self):
        """Repeatedly apply the unit rule. Return False if a conflict is reached."""

        self.pre_bcp(self)
        unit_clauses = filter(lambda c: c.is_unit(), self.clauses)
        unit_clause = next(unit_clauses, None)
        while unit_clause is not None:
            # since we have a unit clause, we know that there is exactly one unassigned literal
            literal = next(filter(lambda l: not l.has_value(), unit_clause.literals))
            literal.atom.value = literal.positive
            prefix = " " if literal.atom.value else "!"
            logging.info("bcp: %s%s @ %s; antecedent: %s" % (prefix, literal.atom, self.decision_level, unit_clause))

            # create a new decision node for the variable
            self.implication_graph.add_forced_decision(literal.atom, literal.positive, unit_clause, self.decision_level)

            for clause in filter(lambda c: c.is_unsatisfied(), self.clauses):

                # check if we have a conflict with any other clause
                # because we set the literal's value just before and we are leveraging side effects,
                # we can check for `clause.is_unsatisfied()`
                self.implication_graph.add_conflict(literal.atom, clause, self.decision_level)
                logging.info("bcp: conflict with %s" % clause)

                self.post_bcp(self)
                self.post_bcp_false(self)
                return False

            unit_clauses = filter(lambda c: c.is_unit(), self.clauses)
            unit_clause = next(unit_clauses, None)
        
        logging.info("bcp: ok")
        self.post_bcp(self)
        self.post_bcp_true(self)
        return True


    def resolve_conflict(self):
        """Backtrack until no conflict occurs anymore. Return False if this is impossible."""

        self.pre_resolve_conflict(self)
        if self.implication_graph.conflict_node is None:
            self.post_resolve_conflict(self)
            self.post_resolve_conflict_true(self)
            return True

        logging.info("res: %s" % self.implication_graph.conflict_node.variable)
        if self.decision_level <= 0:
            logging.info("res: conflict @ dl 0!")
            self.post_resolve_conflict(self)
            self.post_resolve_conflict_false(self)
            return False
        
        # find the first UIP
        first_uip = self.implication_graph.find_first_uip()

        # find the antecedents and decision levels in the conflict graph
        antecedents, sorted_decision_levels = self.implication_graph.get_conflict_information(first_uip)
        logging.info("res: decision levels: %s" % sorted_decision_levels)

        # determine the second-highest decision level
        if len(sorted_decision_levels) >= 2:
            decision_level = sorted_decision_levels[1]
        else:
            logging.info("res: no second-highest dl!")
            self.post_resolve_conflict(self)
            self.post_resolve_conflict_false(self)
            return False

        # reset the decision level and undo all intermediate decisions
        self.decision_level = decision_level
        self.implication_graph.clear_decisions(decision_level)

        # learn a clause by resolution of the antecedents
        learned_clause = Clause([])
        for antecedent in antecedents:
            learned_clause = learned_clause.resolve(antecedent)

        # delete the conflict node
        self.conflict_node = None
        self.clauses.append(learned_clause)

        logging.info("res: back to decision level %s" % decision_level)
        logging.info("res: learned clause %s" % learned_clause)

        self.post_resolve_conflict(self)
        self.post_resolve_conflict_true(self)
        return True
    

class BruteForceSatSolver(SatSolver):
    """A simple SAT solver which checks all possible truth assignment until a satisfying assignment is found."""

    def solve_internal(self):
        """Solve the given SAT instance by brute force"""

        iterator = iter(self.variables.values())
        var = next(iterator, None)
        return self.assign_next(var, iterator)


    def assign_next(self, variable, iterator):
        """Recursive function for creating all possible further assignments"""

        if variable is None and all(any(clause.literals) for clause in self.clauses):
            return self.clauses

        else:
            next_var = next(iterator, None)
            variable.value = True
            temp = self.assign_next(next_var, iterator)
            if temp is not None:
                return temp

            variable.value = False
            temp = self.assign_next(next_var, iterator)
            if temp is not None:
                return temp

            return None
