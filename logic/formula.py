from abc import abstractmethod, ABCMeta
from typing import Collection, Any, Union, Optional, Iterable
from .synthesizer import Synthesizer

class Formula(metaclass=ABCMeta):
    @abstractmethod
    def synthesize(self, synthesizer: Synthesizer) -> Any:
        pass

class Literal(Formula):

    def __neg__(self) -> 'Literal':
        return Negation(self)

    def __add__(self, other: Union['Literal', 'Disjunction']) -> 'Disjunction':
        as_dis = Disjunction([self])
        return as_dis + other

    def __mul__(self, other: Union['Literal', 'Disjunction', 'Conjunction']) -> 'Conjunction':
        as_dis = Disjunction([self])
        return as_dis * other

class Constant(Literal):

    def __init__(self, value: bool) -> None:
        super().__init__()
        self.__value = value

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

    def __init__(self, literals: Collection[Literal]) -> None:
        super().__init__()
        self.__literals = frozenset(literals)

    def __len__(self) -> int:
        return len(self.__literals)

    @property
    def literals(self) -> Collection[Literal]:
        return self.__literals

    def __add__(self, other: Union[Literal, 'Disjunction']) -> 'Disjunction':
        literals = set(self.literals)
        if isinstance(other, Literal):
            literals |= {other}
        elif isinstance(other, Disjunction):
            literals |= other.literals
        else:
            raise TypeError()
        return Disjunction(literals)

    def __mul__(self, other: Union[Literal, 'Disjunction', 'Conjunction']) -> 'Conjunction':
        as_con = Conjunction([self])
        return as_con * other

    def synthesize(self, synthesizer: Synthesizer) -> Any:
        return synthesizer.synthesize_disjunction(
            literal.synthesize(synthesizer) for literal in self.literals
        )

    def __str__(self) -> str:
        literals = [str(literal) for literal in self.literals]
        return "({})".format(" + ".join(literals))

    def __hash__(self) -> int:
        return hash(self.literals)

    def __eq__(self, other: 'Disjunction') -> bool:
        if isinstance(other, Disjunction):
            return self.literals == other.literals
        return False

class Conjunction(Formula):

    def __init__(self, clauses: Collection[Disjunction]) -> None:
        super().__init__()
        self.__clauses = frozenset(clauses)

    @property
    def clauses(self) -> Collection[Disjunction]:
        return self.__clauses

    def __len__(self) -> int:
        return len(self.__clauses)

    def synthesize(self, synthesizer: Synthesizer) -> Any:
        return synthesizer.synthesize_conjunction(
            clause.synthesize(synthesizer) for clause in self.__clauses
        )

    def __mul__(self, other: Union[Literal, Disjunction, 'Conjunction']) -> 'Conjunction':
        clauses = set(self.__clauses)
        if isinstance(other, Literal):
            clauses |= {Disjunction([other])}
        elif isinstance(other, Disjunction):
            clauses |= {other}
        elif isinstance(other, Conjunction):
            clauses |= set(other.__clauses)
        else:
            raise TypeError()

        return Conjunction(clauses)

    def __str__(self) -> str:
        clauses = [str(clause) for clause in self.clauses]
        return " * ".join(clauses)

    def __hash__(self) -> int:
        return hash(self.clauses)

    def __eq__(self, other: 'Formula') -> bool:
        if isinstance(other, Conjunction):
            return self.clauses == other.clauses
        return False