from typing import Any, List, Collection, Iterable, Union, Dict, Optional
from .synthesizer import Synthesizer
from .formula import Clause, CNF, Literal, Constant, Variable

class PySATSynthesizer(Synthesizer):

    def __init__(self):
        super().__init__()
        self.__constant_true_id = 1
        self.__variable_id_offset = 2
        self.__variables_to_id = {  }
        self.__ids_to_variables = [ ]

    def synthesize_variable(self, variable_name: str) -> int:
        if variable_name not in self.__variables_to_id:
            list_idx = len(self.__ids_to_variables)
            self.__ids_to_variables.append(variable_name)
            self.__variables_to_id[variable_name] = list_idx + self.__variable_id_offset
        return self.__variables_to_id[variable_name]

    def synthesize_negation(self, literal_representation: int) -> int:
        return -literal_representation

    def synthesize_true(self) -> int:
        return self.__constant_true_id
    
    def synthesize_clause(self, literals: Iterable[int]) -> List[int]:
        return [literal for literal in literals]

    def synthesize_cnf(self, clauses: Iterable[List[int]]) -> List[List[int]]:
        formula = []
        for clause in clauses:
            formula.append(clause)
        return formula

    # def translate(self, var_id: int) -> str:
    #     if var_id == self.__constant_true_id:
    #         return 'True'
    #     return self.__ids_to_variables[var_id-self.__variable_id_offset]

    def translate(self, var_ids: Iterable[int]) -> Collection[Literal]:
        def translate_single(var_id: int) -> Literal:
            negate = var_id < 0
            var_id = -var_id if negate else var_id

            # if var_id == self.__constant_true_id:
            #     return Constant(False) if negate else Constant(True)
            var = Variable(self.__ids_to_variables[var_id - self.__variable_id_offset])
            return -var if negate else var
            
        return [translate_single(idx) for idx in var_ids if abs(idx) >= self.__variable_id_offset]

    # def get_assumptions(self, assignments=None: Dict[Union[str, Variable], bool]) -> List[int]:
    #     assumptions = [self.__constant_true_id]
    #     assumptions += [
    #         for (var, val) in ((var.name if isinstance(var, Variable) else var, val) for var, val in assignments)
    #     ]

    def get_assumptions(self, assignments: Optional[Iterable[Literal]]=None) -> List[int]:
        assumptions = [self.__constant_true_id]
        if assignments is not None:
            assumptions += [
                literal.synthesize(self) for literal in assignments
            ]
        return assumptions

    def get_known_variables(self) -> Collection[str]:
        return [name for name in self.__ids_to_variables]

    def synthesize(self, formula: Union[Literal, Clause, CNF]) -> Collection[Collection[int]]:
        if isinstance(formula, Literal):
            formula = Clause([formula])
        if isinstance(formula, Clause):
            formula = CNF([formula])
        return formula.synthesize(self)
