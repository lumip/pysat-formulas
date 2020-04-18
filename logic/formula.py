from abc import abstractmethod, ABCMeta
from typing import Collection, Any, Union, Optional, Iterable, Tuple
from functools import reduce
from .synthesizer import Synthesizer

class Formula(metaclass=ABCMeta):

    @staticmethod
    def from_copy(other: 'Formula') -> 'Formula':
        return other.from_copy(other)

    @abstractmethod
    def synthesize(self, synthesizer: Synthesizer) -> Any:
        raise NotImplementedError()

    @abstractmethod
    def tseytin_transform(self) -> Tuple['Literal', 'CNF']:
        raise NotImplementedError()

    def to_cnf(self) -> 'CNF':
        return self.tseytin_transform()[1]

    def __neg__(self) -> 'Formula':
        return FormulaNegation(self)

    def __repr__(self) -> str:
        return str(self)

    def __mul__(self, other: 'Formula') -> 'Conjunction':
        as_con = Conjunction([self])
        return as_con * other

    def __add__(self, other: 'Formula') -> 'Disjunction':
        as_dis = Disjunction([self])
        return as_dis + other

class Literal(Formula):

    def __init__(self, name: str) -> None:
        self.__name = name

    @property
    def name(self) -> str:
        return self.__name

    def __neg__(self) -> 'Literal':
        return LiteralNegation(self)

    def __add__(self, other: Union['Literal', 'Clause']) -> 'Clause':
        as_dis = Clause([self])
        return as_dis + other

    def __mul__(self, other: Union['Literal', 'Clause', 'CNF']) -> 'CNF':
        as_dis = Clause([self])
        return as_dis * other

    def to_cnf(self) -> 'CNF':
        return Clause([self]).to_cnf()

    def tseytin_transform(self) -> Tuple['Literal', 'CNF']:
        return self, CNF([])

class Constant(Literal):

    def __init__(self, value: bool) -> None:
        super().__init__(str(value))
        self.__value = value

    @staticmethod
    def from_copy(other: 'Constant') -> 'Constant':
        return Constant(other.value)

    @property
    def value(self) -> bool:
        return self.__value

    def synthesize(self, synthesizer: Synthesizer) -> Any:
        syn = synthesizer.synthesize_true()
        if not self.__value:
            syn = synthesizer.synthesize_negation(syn)
        return syn

    def __str__(self) -> str:
        return str(self.value)

    def __eq__(self, other) -> bool:
        if isinstance(other, Constant):
            return self.value == other.value
        elif isinstance(other, LiteralNegation):
            return other.__eq__(self)
        return False

    def __hash__(self) -> int:
        return hash(self.value)


class LiteralNegation(Literal):

    def __init__(self, literal: Literal) -> None:
        super().__init__(literal.name)
        self.__literal = literal

    @staticmethod
    def from_copy(other: 'LiteralNegation') -> 'LiteralNegation':
        return LiteralNegation(other.__literal)

    def synthesize(self, synthesizer: Synthesizer) -> Any:
        return synthesizer.synthesize_negation(
            self.__literal.synthesize(synthesizer)
        )

    def __str__(self) -> str:
        return "~{}".format(self.__literal)

    def __hash__(self) -> str:
        return -hash(self.__literal)

    def __neg__(self) -> Literal:
        return self.__literal

    def __eq__(self, other: Literal) -> bool:
        if isinstance(self.__literal, Constant):
            return self.__literal != other
        elif isinstance(other, LiteralNegation):
            return self.__literal == other.__literal
        return False
        

class Variable(Literal):
    def __init__(self, name: str) -> None:
        super().__init__(name)
        self.__name = name

    @staticmethod
    def from_copy(other: 'Variable') -> 'Variable':
        return Variable(other.name)

    def synthesize(self, synthesizer: Synthesizer) -> Any:
        return synthesizer.synthesize_variable(self.name)

    def __str__(self) -> str:
        return self.name

    def __hash__(self) -> int:
        return hash(self.name)

    def __eq__(self, other: Literal) -> None:
        if isinstance(other, Variable):
            return self.name == other.name
        return False


class Disjunction(Formula):

    def __init__(self, subformulae: Iterable[Formula]) -> None:
        super().__init__()
        self.__children = frozenset(subformulae)

    @staticmethod
    def from_copy(other: 'Disjunction') -> 'Disjunction':
        return Disjunction(other.subformulae)

    def __len__(self) -> int:
        return len(self.__children)

    @property
    def subformulae(self) -> Collection[Formula]:
        return self.__children

    def __add__(self, other: Formula) -> 'Disjunction':
        if isinstance(other, Disjunction):
            return Disjunction(self.subformulae | other.subformulae)    
        return Disjunction(self.subformulae | {other})

    def synthesize(self, synthesizer: Synthesizer) -> Any:
        raise NotImplementedError()

    def __str__(self) -> str:
        substrings = [str(formula) for formula in self.subformulae]
        return "({})".format(" + ".join(substrings))

    def __hash__(self) -> int:
        return hash(self.subformulae)

    def __eq__(self, other) -> bool:
        if isinstance(other, Disjunction):
            return self.subformulae == other.subformulae
        return False

    def tseytin_transform(self) -> Tuple['Literal', 'CNF']:
        s = Variable('__ts_dis_{}'.format(hash(self)))
        t_phis, cnfs = zip(*[phi.tseytin_transform() for phi in self.subformulae])
        cnf = CNF([Clause(t_phis) + -s])
        cnf = reduce(lambda x, t: x * (s + -t), t_phis, cnf)
        cnf = reduce(lambda x, y: x * y, cnfs, cnf)
        return s, cnf

class Clause(Disjunction):

    def __init__(self, literals: Iterable[Literal]) -> None:
        super().__init__(literals)

    @staticmethod
    def from_copy(other: 'Clause') -> 'Clause':
        return Clause(other.literals)

    @property
    def literals(self) -> Collection[Literal]:
        return self.subformulae

    def __add__(self, other: Union[Literal, 'Clause']) -> 'Clause':
        literals = set(self.literals)
        if isinstance(other, Literal):
            literals |= {other}
        elif isinstance(other, Clause):
            literals |= other.literals
        else:
            raise TypeError()
        return Clause(literals)

    def __mul__(self, other: Union[Literal, 'Clause', 'CNF']) -> 'CNF':
        as_con = CNF([self])
        return as_con * other

    def synthesize(self, synthesizer: Synthesizer) -> Any:
        return synthesizer.synthesize_clause(
            literal.synthesize(synthesizer) for literal in self.literals
        )

    def to_cnf(self) -> 'CNF':
        return CNF([self])


class Conjunction(Formula):

    def __init__(self, subformulae: Iterable[Formula]) -> None:
        super().__init__()
        self.__children = frozenset(subformulae)

    @staticmethod
    def from_copy(other: 'Conjunction') -> 'Conjunction':
        return Conjunction(other.subformulae)

    def __len__(self) -> int:
        return len(self.__children)

    @property
    def subformulae(self) -> Collection[Formula]:
        return self.__children

    def __add__(self, other: Formula) -> 'Disjunction':
        formula = Disjunction([self])
        return formula + other

    def __mul__(self, other: Formula) -> 'Conjunction':
        if isinstance(other, Conjunction):
            return Conjunction(self.subformulae | other.subformulae)
        return Conjunction(self.subformulae | {other})

    def synthesize(self, synthesizer: Synthesizer) -> Any:
        raise NotImplementedError()

    def __str__(self) -> str:
        substrings = [str(formula) for formula in self.subformulae]
        return "({})".format(" * ".join(substrings))

    def __hash__(self) -> int:
        return hash(self.subformulae)

    def __eq__(self, other) -> bool:
        if isinstance(other, Disjunction):
            return self.subformulae == other.subformulae
        return False

    def tseytin_transform(self) -> Tuple['Literal', 'CNF']:
        t_phis, cnfs = zip(*[phi.tseytin_transform() for phi in self.subformulae])
        s = Variable('__ts_con_{}'.format(hash(self)))

        cnf = reduce(lambda x, t: x + -t, t_phis, s) # s -> self
        cnf *= reduce(lambda x, t: x * (-s + t), t_phis) # self -> s

        cnf = reduce(lambda x, y: x * y, cnfs, cnf)
        assert(isinstance(cnf, CNF))
        return s, cnf

class CNF(Conjunction):

    def __init__(self, clauses: Iterable[Clause]) -> None:
        super().__init__(clauses)

    @staticmethod
    def from_copy(other: 'CNF') -> 'CNF':
        return CNF(other.clauses)

    @property
    def clauses(self) -> Collection[Clause]:
        return self.subformulae

    def __mul__(self, other: Union[Literal, Clause, 'CNF']) -> 'CNF':
        clauses = set(self.clauses)
        if isinstance(other, Literal):
            clauses |= {Clause([other])}
        elif isinstance(other, Clause):
            clauses |= {other}
        elif isinstance(other, CNF):
            clauses |= set(other.clauses)
        else:
            raise TypeError()

        return CNF(clauses)

    def synthesize(self, synthesizer: Synthesizer) -> Any:
        return synthesizer.synthesize_cnf(
            clause.synthesize(synthesizer) for clause in self.clauses
        )

    def to_cnf(self) -> 'CNF':
        return self


class FormulaNegation(Formula):

    def __init__(self, formula: Formula) -> None:
        super().__init__()
        self.__formula = formula

    @staticmethod
    def from_copy(other: 'FormulaNegation') -> 'FormulaNegation':
        return FormulaNegation(other.formula)

    @property
    def formula(self) -> Formula:
        return self.__formula

    def __neg__(self) -> Formula:
        return self.formula

    def synthesize(self, synthesizer: Synthesizer) -> Any:
        raise NotImplementedError()

    def tseytin_transform(self) -> Tuple[Literal, 'CNF']:
        t, cnfs = self.formula.tseytin_transform()

        s = Variable('__ts_{}'.format(hash(self)))
        cnf = CNF([
            -s + -t, s + t
        ])
        return reduce(lambda x, y: x * y, cnfs, cnf)

    def __str__(self) -> str:
        return "~{}".format(self.formula)

    def __hash__(self) -> str:
        return -hash(self.formula)

    def __eq__(self, other: Literal) -> bool:
        if isinstance(other, FormulaNegation):
            return self.formula == other.formula
        return False

class Implication(Formula):

    def __init__(self, lhs: Formula, rhs: Formula):
        super().__init__()
        self.__lhs = lhs
        self.__rhs = rhs

    @property
    def lhs(self) -> Formula:
        return self.__lhs

    @property
    def rhs(self) -> Formula:
        return self.__rhs

    def tseytin_transform(self) -> Tuple['Literal', 'CNF']:
        phi = -self.lhs + self.rhs
        return phi.tseytin_transform()

    def synthesize(self, synthesizer: Synthesizer) -> Any:
        raise NotImplementedError
        
    def __hash__(self) -> int:
        return 1213 * hash(self.lhs) + 229 * hash(self.rhs)

    def __eq__(self, other) -> bool:
        if isinstance(other, Implication):
            return self.lhs == other.lhs and self.rhs == other.rhs
        return False

    def __str__(self) -> str:
        return '({} -> {})'.format(str(self.lhs), str(self.rhs))

class Equivalence(Formula):

    def __init__(self, lhs: Formula, rhs: Formula):
        super().__init__()
        self.__lhs = lhs
        self.__rhs = rhs

    @property
    def lhs(self) -> Formula:
        return self.__lhs

    @property
    def rhs(self) -> Formula:
        return self.__rhs

    def tseytin_transform(self) -> Tuple['Literal', 'CNF']:
        phi = Implication(self.lhs, self.rhs) * Implication(self.rhs, self.lhs)
        return phi.tseytin_transform()

    def synthesize(self, synthesizer: Synthesizer) -> Any:
        raise NotImplementedError()
        
    def __hash__(self) -> int:
        return 421 * hash(frozenset({self.lhs, self.rhs}))

    def __eq__(self, other) -> bool:
        if isinstance(other, Implication):
            return (self.lhs == other.lhs and self.rhs == other.rhs) or (self.lhs == other.rhs and self.rhs == other.lhs)
        return False

    def __str__(self) -> str:
        return '({} <-> {})'.format(str(self.lhs), str(self.rhs))
    