from abc import abstractmethod, abstractproperty, ABCMeta
from typing import Any, Iterable

class Synthesizer(metaclass=ABCMeta):
    
    @abstractmethod
    def synthesize_variable(self, variable_name: str) -> Any:
        raise NotImplementedError()

    @abstractmethod
    def synthesize_negation(self, literal_representation: Any) -> Any:
        raise NotImplementedError()

    @abstractmethod
    def synthesize_true(self) -> Any:
        raise NotImplementedError()

    @abstractmethod
    def synthesize_clause(self, literals: Iterable[Any]) -> Any:
        raise NotImplementedError()

    @abstractmethod
    def synthesize_cnf(self, clauses: Iterable[Any]) -> Any:
        raise NotImplementedError()


    
