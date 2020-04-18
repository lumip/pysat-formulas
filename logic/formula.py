from abc import abstractmethod, ABCMeta
from typing import Collection, Any, Union, Optional, Iterable
from .synthesizer import Synthesizer

class Formula(metaclass=ABCMeta):

    @staticmethod
    def from_copy(other: 'Formula') -> 'Formula':
        return other.from_copy(other)

    @abstractmethod
    def synthesize(self, synthesizer: Synthesizer) -> Any:
        raise NotImplementedError()

    @abstractmethod
    def to_cnf(self) -> 'CNF':
        raise NotImplementedError()

class Literal(Formula):

    def __neg__(self) -> 'Literal':
        return Negation(self)

    def __add__(self, other: Union['Literal', 'Clause']) -> 'Clause':
        as_dis = Clause([self])
        return as_dis + other

    def __mul__(self, other: Union['Literal', 'Clause', 'CNF']) -> 'CNF':
        as_dis = Clause([self])
        return as_dis * other

    def to_cnf(self) -> 'CNF':
        return Clause([self]).to_cnf()

class Constant(Literal):

    def __init__(self, value: bool) -> None:
        super().__init__()
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
        elif isinstance(other, Negation):
            return other.__eq__(self)
        return False

    def __hash__(self) -> int:
        return hash(self.value)

class Negation(Literal):

    def __init__(self, literal: Literal) -> None:
        super().__init__()
        self.__literal = literal

    @staticmethod
    def from_copy(other: 'Negation') -> 'Negation':
        return Negation(other.__literal)

    def synthesize(self, synthesizer: Synthesizer) -> Any:
        return synthesizer.synthesize_negation(
            self.__literal.synthesize(synthesizer)
        )

    def __str__(self) -> str:
        return "~{}".format(self.__literal)

    def __hash__(self) -> str:
        return -hash(self.__literal)

    def __eq__(self, other: Literal) -> bool:
        if isinstance(self.__literal, Constant):
            return self.__literal != other
        elif isinstance(other, Negation):
            return self.__literal == other.__literal
        return False

class Variable(Literal):
    def __init__(self, name: str) -> None:
        super().__init__()
        self.__name = name

    @staticmethod
    def from_copy(other: 'Variable') -> 'Variable':
        return Variable(other.name)

    @property
    def name(self) -> str:
        return self.__name

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

    def __init__(self, subformulae: Collection[Formula]) -> None:
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

    def __mul__(self, other: Formula) -> 'Conjunction':
        formula = Conjunction([self])
        return formula * other

    def synthesize(self, synthesizer: Synthesizer) -> Any:
        raise NotImplementedError()

    def to_cnf(self, synthesizer: Synthesizer) -> 'CNF':
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

class Clause(Disjunction):

    def __init__(self, literals: Collection[Literal]) -> None:
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

    def __init__(self, subformulae: Collection[Formula]) -> None:
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

    def to_cnf(self, synthesizer: Synthesizer) -> 'CNF':
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


class CNF(Conjunction):

    def __init__(self, clauses: Collection[Clause]) -> None:
        super().__init__(clauses)

    @staticmethod
    def from_copy(other: 'CNF') -> 'CNF':
        return CNF(other.clauses)

    @property
    def clauses(self) -> Collection[Clause]:
        return self.subformulae

    def synthesize(self, synthesizer: Synthesizer) -> Any:
        return synthesizer.synthesize_cnf(
            clause.synthesize(synthesizer) for clause in self.clauses
        )

    def to_cnf(self) -> 'CNF':
        return self

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
