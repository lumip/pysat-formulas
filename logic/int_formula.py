from typing import Optional, Iterable, Any, Tuple
from .formula import Formula, Literal, CNF, Clause, Implication, Conjunction, Disjunction, Equivalence, Variable
from .synthesizer import Synthesizer


class IntVariable:

    def __init__(self, name: str, max: int, min: Optional[int]=0) -> None:
        self.__name = name
        self.__max = max
        self.__min = min

    @property
    def min(self) -> int:
        return self.__min

    @property
    def max(self) -> int:
        return self.__max

    @property
    def name(self) -> str:
        return self.__name

    def __str__(self) -> str:
        return self.name

    def __hash__(self) -> int:
        return hash(self.name)

    def __eq__(self, other) -> bool:
        if isinstance(other, IntVariable):
            return self.name == other.name
        return False

    # def tseytin_transform(self) -> Tuple[Literal, CNF]:
    #     values_syn = (EqConstTerm(self, v) for v in range(self.min, self.max + 1))
        
    #     def no_other_means_one(x: Literal, ys: Iterable[Literal]) -> CNF:
    #         formula = CNF([])
    #         for y in ys:
    #             formula *= (-y + -x)
    #         return formula

    #     def only_one(xs: Iterable[Literal]) -> CNF:
    #         xs = frozenset(xs)
    #         formula = CNF([])
    #         for x in xs:
    #             ys = [y for y in xs if y != x]
    #             formula *= no_other_means_one(x, ys)
    #         formula *= Clause(xs)
    #         return formula

    #     formula = only_one(values_syn)
    #     return formula

    def get_specification(self) -> CNF:
        values_syn = (EqConstTerm(self, v) for v in range(self.min, self.max + 1))
        
        def no_other_means_one(x: Literal, ys: Iterable[Literal]) -> CNF:
            formula = CNF([])
            for y in ys:
                formula *= (-y + -x)
            return formula

        def only_one(xs: Iterable[Literal]) -> CNF:
            xs = frozenset(xs)
            formula = CNF([])
            for x in xs:
                ys = [y for y in xs if y != x]
                formula *= no_other_means_one(x, ys)
            formula *= Clause(xs)
            return formula

        formula = only_one(values_syn)
        return formula

class EqConstTerm(Literal):

    def __init__(self, var: IntVariable, val: int) -> None:
        super().__init__("{}=={}".format(var.name, val))
        self.__var = var
        self.__val = val

    @property
    def variable(self) -> IntVariable:
        return self.__var

    @property
    def value(self) -> int:
        return self.__val

    def synthesize(self, synthesizer: Synthesizer) -> Any:
        return Variable.from_copy(self).synthesize(synthesizer)

    def __str__(self) -> str:
        return "{}=={}".format(self.variable.name, self.value)

    def __hash__(self) -> int:
        return 13 * hash(self.variable) + 23 * hash(self.value)

    def __eq__(self, other) -> bool:
        if isinstance(other, EqConstTerm):
            return self.value == other.value and self.variable == other.variable
        return False


class EqVarTerm(Literal):

    def __init__(self, lhs: IntVariable, rhs: IntVariable) -> None:
        super().__init__('{}=={}'.format(str(lhs), str(rhs)))
        self.__lhs = lhs
        self.__rhs = rhs

    @property
    def lhs(self) -> IntVariable:
        return self.__lhs

    @property
    def rhs(self) -> IntVariable:
        return self.__rhs

    def tseytin_transform(self) -> Tuple[Literal, CNF]:
        ilb = max(self.lhs.min, self.rhs.min)
        iub = min(self.lhs.max, self.rhs.max) + 1

        formula = Disjunction(
            (EqConstTerm(self.lhs, c) * EqConstTerm(self.rhs, c)) for c in range(ilb, iub)
        )
        return formula.tseytin_transform()

    def synthesize(self, synthesizer: Synthesizer) -> Any:
        raise NotImplementedError()
    
    def __str__(self) -> str:
        return "{}=={}".format(self.lhs.name, self.rhs.name)

    def __hash__(self) -> int:
        return 383 * hash(frozenset({self.lhs, self.rhs}))

    def __eq__(self, other) -> bool:
        if isinstance(other, EqVarTerm):
            return (self.lhs == other.lhs and self.rhs == other.rhs) or (self.lhs == other.rhs and self.rhs == other.lhs)
        return False
