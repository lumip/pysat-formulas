from logic.formula import Variable, Constant, CNF, Clause, Implication, Equivalence, Conjunction, Disjunction, LiteralNegation
from logic.int_formula import IntVariable, EqConstTerm, EqVarTerm
from logic.pysatsynthesizer import PySATSynthesizer
from pysat.solvers import Lingeling, Glucose3, Minisat22
from math import sqrt

def create_variables(size=9):
    return [
        [IntVariable('cell_{}_{}'.format(y, x), min=1, max=size) for x in range(size)]
        for y in range(size)
    ]

def restrict_rows_and_cols(variables):
    size = len(variables)
    phi = Conjunction([])
    def restrict_row(row):
        coords = [(row, i) for i in range(size)]
        return create_restrictions(variables, coords)
    def restrict_col(col):
        coords = [(i, col) for i in range(size)]
        return create_restrictions(variables, coords)

    for i in range(size):
        phi *= restrict_row(i) * restrict_col(i)

    return phi

def create_restrictions(variables, coord_map):
    phi = Conjunction([])
    for i in range(len(coord_map)):
        x = coord_map[i]
        for j in range(i):
            y = coord_map[j]
            phi *= -Disjunction([EqVarTerm(variables[x[0]][x[1]], variables[y[0]][y[1]])])
    return phi

def restrict_squares(variables):
    size = len(variables)
    square_size = int(sqrt(size))
    assert(square_size**2 == size)

    def restrict_square(block_x, block_y):
        offset = block_x * square_size, block_y * square_size
        coords = [(i + offset[0], j + offset[1]) for i in range(square_size) for j in range(square_size)]
        return create_restrictions(variables, coords)

    phi = Conjunction([])
    for x in range(square_size):
        for y in range(square_size):
            phi *= restrict_square(x, y)
    return phi


def extract_specs(variables):
    cnf = CNF([])
    for y in range(len(variables)):
        for x in range(len(variables[y])):
            cnf *= variables[y][x].get_specification()
    return cnf

def get_assumptions(variables, sudoku):
    size = len(variables)
    assert(size == len(variables))

    literals = []
    for y in range(size):
        for x in range(size):
            if sudoku[y][x] > 0:
                literals.append(EqConstTerm(variables[y][x], sudoku[y][x]))
    return literals

def form_sudoku(literals, size=9):
    sudoku = [[0 for i in range(size)] for j in range(size)]
    for literal in literals:
        split = literal.name.split('==')
        assert(len(split) == 2)
        name = split[0]
        value = int(split[1])

        split = name.split('_')
        assert(len(split) == 3)
        y = int(split[1])
        x = int(split[2])

        sudoku[y][x] = value

    return sudoku

def print_sudoku(sudoku):
    for i in range(len(sudoku)):
        print(', '.join(str(v) for v in sudoku[i]))

def validate(solution):
    size = len(solution)
    square_size = int(sqrt(size))
    assert(square_size**2 == size)

    def validate(coord_map):
        bins = [0] * size
        for i in range(size):
            c = coord_map[i]
            bins[solution[c[0]][c[1]] - 1] += 1
        for i in range(size):
            if bins[i] != 1:
                return False
        return True

    def validate_row(row):
        coords = [(row, i) for i in range(size)]
        return validate(coords)
    def validate_col(col):
        coords = [(i, col) for i in range(size)]
        return validate(coords)
    def validate_square(square_x, square_y):
        offset = square_x * square_size, square_y * square_size
        coords = [(i + offset[0], j + offset[1]) for i in range(square_size) for j in range(square_size)]
        return validate(coords)

    validated = True
    for i in range(size):
        validated = validated and validate_row(i) and validate_col(i)
    for x in range(square_size):
        for y in range(square_size):
            validated = validated and validate_square(x, y)
    return validated

def same_as_target(solution, target):
    validated = True
    size = len(solution)
    for y in range(size):
        for x in range(size):
            validated = validated and solution[y][x] == target[y][x]
    return validated

sudoku = [
    [1, 2, 0, 0],
    [0, 0, 1, 0],
    [0, 0, 0, 3],
    [2, 0, 0, 1]
]

target_solution = [
    [1, 2, 3, 4],
    [3, 4, 1, 2],
    [4, 1, 2, 3],
    [2, 3, 4, 1]
]

sudoku = [
    [2, 0, 0, 6, 9, 0, 8, 0, 1],
    [0, 0, 0, 0, 0, 3, 6, 0, 0],
    [0, 1, 3, 8, 0, 2, 5, 4, 0],
    [7, 0, 5, 0, 8, 0, 3, 9, 6],
    [8, 3, 0, 4, 0, 0, 0, 0, 0],
    [1, 0, 6, 0, 0, 5, 0, 0, 0],
    [3, 7, 0, 9, 0, 6, 0, 1, 0],
    [0, 2, 9, 1, 0, 8, 0, 0, 0],
    [5, 6, 0, 3, 0, 0, 0, 2, 0]
]

target_solution = [
    [2, 5, 7, 6, 9, 4, 8, 3, 1],
    [9, 8, 4, 5, 1, 3, 6, 7, 2],
    [6, 1, 3, 8, 7, 2, 5, 4, 9],
    [7, 4, 5, 2, 8, 1, 3, 9, 6],
    [8, 3, 2, 4, 6, 9, 1, 5, 7],
    [1, 9, 6, 7, 3, 5, 2, 8, 4],
    [3, 7, 8, 9, 2, 6, 4, 1, 5],
    [4, 2, 9, 1, 5, 8, 7, 6, 3],
    [5, 6, 1, 3, 4, 7, 9, 2, 8]
]


if __name__ == '__main__':
    size = len(sudoku)
    variables = create_variables(size)

    print("##### to solve #####")
    print_sudoku(sudoku)
    print("")


    formula = Conjunction([])
    formula *= restrict_rows_and_cols(variables)
    formula *= restrict_squares(variables)
    formula *= extract_specs(variables)

    print("all subformulae")
    for f in formula.subformulae:
        print(f)

    synthesizer = PySATSynthesizer()

    print("now transforming")
    root, formula = formula.tseytin_transform()
    formula = root * formula

    print("now synthesizing")
    cnf = formula.synthesize(synthesizer)
    print("now solving")
    
    print(synthesizer.get_known_variables())
    with Minisat22(bootstrap_with=cnf) as l:
        if l.solve(assumptions=synthesizer.get_assumptions(get_assumptions(variables, sudoku))) == False:
            print("unsatisfiable")
        else:
            print("satisfiable")
            solution = synthesizer.translate(l.get_model())
            # filtering out negative literals, i.e., all values our integer variables are not assigned
            solution = [lit for lit in solution if not isinstance(lit, LiteralNegation)]
            assert(len(solution) == size**2)
            
            solution = form_sudoku(solution, size)
            print("##### found solution ######")
            print_sudoku(solution)
            print("solution is valid: {}".format(validate(solution)))
            print("solution is the same as target: {}".format(same_as_target(solution, target_solution)))
            print("solver found {} solutions".format(len([l.enum_models()])))
