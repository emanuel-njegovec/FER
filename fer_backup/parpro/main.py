from enum import Enum
import random
from mpi4py import MPI
import time
import psutil


p = psutil.Process()
p.cpu_affinity([0, 1, 2, 3, 4, 5, 6, 7])


# mpiexec -n 8 python main.py


comm = MPI.COMM_WORLD
size = comm.Get_size()
rank = comm.Get_rank()
name = MPI.Get_processor_name()


class Move(Enum):
    EMPT = 1
    COMP = 2
    PLAY = 3


rows = 6
columns = 7

calculate_depth = 5   # minimum 5

do_deepest_print = False
do_deep_print = False


A = []
for i in range(rows):
    A.append([])
    for j in range(columns):
        A[i].append(Move.EMPT)


def deep_print(str, level):
    if level == 2 and do_deepest_print:
        print(str, flush=True)
    if level == 1 and do_deep_print:
        print(str, flush=True)
    if level == 0:
        print(str, flush=True)


def change_whose_move(whose_move):
    if whose_move == Move.COMP:
        return Move.PLAY
    elif whose_move == Move.PLAY:
        return Move.COMP


def is_valid_input(matrix, x):
    return 0 <= x <= columns - 1 and matrix[0][x] == Move.EMPT


def copy_matrix(matrix):
    matrix_copy = []
    for i in range(rows):
        matrix_copy.append([])
        for j in range(columns):
            matrix_copy[i].append(matrix[i][j])
    return matrix_copy


def matrix_to_string(matrix):
    string = ""
    for i in range(rows):
        for j in range(columns):
            if matrix[i][j] == Move.COMP:
                string = string + "C "
            elif matrix[i][j] == Move.PLAY:
                string = string + "P "
            else:
                string = string + "- "
        string = string + "\n"
    return string[:-1]


def string_to_matrix(string):
    string_rows = string.split('\n')
    matrix = []
    for string_row in string_rows:
        matrix_row = []
        string_row_elems = string_row.split()
        for string_row_elem in string_row_elems:
            if string_row_elem == "C":
                matrix_row.append(Move.COMP)
            elif string_row_elem == "P":
                matrix_row.append(Move.PLAY)
            else:
                matrix_row.append(Move.EMPT)
        matrix.append(matrix_row)
    return matrix


def are_matrices_the_same(matrix1, matrix2):
    for i in range(rows):
        for j in range(columns):
            if matrix1[i][j] != matrix2[i][j]:
                return False
    return True


def remove_duplicate_matrices(matrices):
    unique_matrices = []
    num_of_matrices = len(matrices)
    for i in range(num_of_matrices - 1):
        found_duplicate = False
        for j in range(num_of_matrices - 1 - i):
            index1 = i
            index2 = i + j + 1
            matrix1 = matrices[index1]
            matrix2 = matrices[index2]
            if are_matrices_the_same(matrix1, matrix2):
                found_duplicate = True
        if not found_duplicate:
            unique_matrices.append(matrix1)
    return unique_matrices


def find_empty_row(matrix, column):
    row = rows - 1
    while matrix[row][column] != Move.EMPT:
        row = row - 1
        if row == -1:
            return -1
    return row


def calculate_child_matrices(matrix, whose_move):

    child_matrices = []

    for j in range(columns):
        i = rows - 1
        changed = False
        while not changed and i >= 0:
            if matrix[i][j] == Move.EMPT:
                matrix_copy = copy_matrix(matrix)
                matrix_copy[i][j] = whose_move
                child_matrices.append(matrix_copy)
                changed = True
            i = i - 1

    return child_matrices


def calculate_matrix_quality_final(matrix):

    for i in range(rows):
        count_player = 0
        count_computer = 0
        for j in range(columns):
            if matrix[i][j] == Move.COMP:
                count_computer = count_computer + 1
                count_player = 0
                if count_computer == 4:
                    return 1
            elif matrix[i][j] == Move.PLAY:
                count_player = count_player + 1
                count_computer = 0
                if count_player == 4:
                    return -1
            else:
                count_player = 0
                count_computer = 0

    for j in range(columns):
        count_player = 0
        count_computer = 0
        for i in range(rows):
            if matrix[i][j] == Move.COMP:
                count_computer = count_computer + 1
                count_player = 0
                if count_computer == 4:
                    return 1
            elif matrix[i][j] == Move.PLAY:
                count_player = count_player + 1
                count_computer = 0
                if count_player == 4:
                    return -1
            else:
                count_player = 0
                count_computer = 0

    for i in range(rows):
        for j in range(columns):
            if matrix[i][j] == Move.COMP:
                if i + 1 < rows and j + 1 < columns and matrix[i + 1][j + 1] == Move.COMP:
                    if i + 2 < rows and j + 2 < columns and matrix[i + 2][j + 2] == Move.COMP:
                        if i + 3 < rows and j + 3 < columns and matrix[i + 3][j + 3] == Move.COMP:
                            return 1
            if matrix[i][j] == Move.PLAY:
                if i + 1 < rows and j + 1 < columns and matrix[i + 1][j + 1] == Move.PLAY:
                    if i + 2 < rows and j + 2 < columns and matrix[i + 2][j + 2] == Move.PLAY:
                        if i + 3 < rows and j + 3 < columns and matrix[i + 3][j + 3] == Move.PLAY:
                            return -1
            if matrix[i][j] == Move.COMP:
                if i - 1 > 0 and j + 1 < columns and matrix[i - 1][j + 1] == Move.COMP:
                    if i - 2 > 0 and j + 2 < columns and matrix[i - 2][j + 2] == Move.COMP:
                        if i - 3 > 0 and j + 3 < columns and matrix[i - 3][j + 3] == Move.COMP:
                            return 1
            if matrix[i][j] == Move.PLAY:
                if i - 1 > 0 and j + 1 < columns and matrix[i - 1][j + 1] == Move.PLAY:
                    if i - 2 > 0 and j + 2 < columns and matrix[i - 2][j + 2] == Move.PLAY:
                        if i - 3 > 0 and j + 3 < columns and matrix[i - 3][j + 3] == Move.PLAY:
                            return -1

    return 0


def calculate_matrix_quality(matrix, whose_move, depth):
    child_matrices = calculate_child_matrices(matrix, whose_move)
    sum_of_child_matrices_qualities = 0
    num_of_child_matrices = len(child_matrices)
    for child_matrix in child_matrices:
        child_matrix_quality_final = calculate_matrix_quality_final(child_matrix)
        if depth == 0 or child_matrix_quality_final != 0:
            child_matrix_quality = child_matrix_quality_final
        else:
            child_matrix_quality = calculate_matrix_quality(child_matrix, change_whose_move(whose_move), depth - 1)
        if whose_move == Move.COMP and child_matrix_quality == 1:
            return 1
        elif whose_move == Move.PLAY and child_matrix_quality == -1:
            return -1
        else:
            sum_of_child_matrices_qualities = sum_of_child_matrices_qualities + child_matrix_quality
    if num_of_child_matrices != 0:
        return sum_of_child_matrices_qualities / num_of_child_matrices
    else:
        return -1


def calculate_comp_move(matrix):

    start_time = time.time()

    child_matrices = calculate_child_matrices(matrix, Move.COMP)

    grandchild_matrices = []
    grandchild_to_child_matrix_mapping = {}
    for child_matrix in child_matrices:

        child_matrix_quality = calculate_matrix_quality_final(child_matrix)
        if child_matrix_quality == 1:
            deep_print("I found a child matrix where I win so I am not calculating any further.", 1)
            return child_matrix

        child_child_matrices = calculate_child_matrices(child_matrix, Move.PLAY)
        do_enter = True
        for grandchild_matrix in child_child_matrices:
            grandchild_matrix_quality = calculate_matrix_quality_final(grandchild_matrix)
            if grandchild_matrix_quality == -1:
                do_enter = False
        if do_enter:
            for grandchild_matrix in child_child_matrices:
                string_grandchild_matrix = matrix_to_string(grandchild_matrix)
                grandchild_matrices.append(string_grandchild_matrix)
                grandchild_to_child_matrix_mapping[string_grandchild_matrix] = child_matrix

    num_of_worker_processes = size - 1
    num_of_tasks = len(grandchild_matrices)

    if num_of_tasks == 0:
        deep_print("There is no grandchild matrix where you don't win so I am not calculating any further.", 1)
        decided_child_matrix = random.choice(child_matrices)
        return decided_child_matrix

    deep_print("Number of worker processes is " + str(num_of_worker_processes) + ".", 1)
    deep_print("Number of tasks is " + str(num_of_tasks) + ".", 1)

    worker_process_counter = 0
    sent_task_counter = 0

    while worker_process_counter < num_of_worker_processes and sent_task_counter < num_of_tasks:
        string_grandchild_matrix = grandchild_matrices[sent_task_counter]
        comm.send(string_grandchild_matrix, dest=worker_process_counter + 1)
        deep_print("Process 0 sent to process" + str(worker_process_counter + 1) + ".", 2)
        sent_task_counter = sent_task_counter + 1
        worker_process_counter = worker_process_counter + 1

    child_to_grandchild_matrix_quality_mapping = {}
    for child_matrix in child_matrices:
        child_to_grandchild_matrix_quality_mapping[matrix_to_string(child_matrix)] = []

    worker_process_counter = 0
    received_task_counter = 0

    while received_task_counter < num_of_tasks:

        if comm.Iprobe(source=worker_process_counter + 1):

            (grandchild_matrix_quality, string_grandchild_matrix) = comm.recv(source=worker_process_counter + 1)
            deep_print("Process 0 received from process " + str(worker_process_counter + 1) + ".", 2)
            child_matrix = grandchild_to_child_matrix_mapping[string_grandchild_matrix]
            string_child_matrix = matrix_to_string(child_matrix)
            child_to_grandchild_matrix_quality_mapping[string_child_matrix].append(grandchild_matrix_quality)

            received_task_counter = received_task_counter + 1
            deep_print("The workers have finished " + str(received_task_counter) + " tasks.", 1)

            if sent_task_counter < num_of_tasks:
                string_grandchild_matrix = grandchild_matrices[sent_task_counter]
                comm.send(string_grandchild_matrix, dest=worker_process_counter + 1)
                deep_print("Process 0 sent to process " + str(worker_process_counter + 1) + ".", 2)
                sent_task_counter = sent_task_counter + 1

        worker_process_counter = worker_process_counter + 1
        if worker_process_counter == num_of_worker_processes:
            worker_process_counter = 0

    deep_print("The workers have finished all tasks.", 1)

    least_worst_grandchild_quality = -1
    least_worst_string_children = []

    for string_child_matrix in child_to_grandchild_matrix_quality_mapping:
        grandchildren_qualities = child_to_grandchild_matrix_quality_mapping[string_child_matrix]
        if len(grandchildren_qualities) == 0:
            worst_grandchild_quality = 0
        else:
            worst_grandchild_quality = min(grandchildren_qualities)
        if worst_grandchild_quality > least_worst_grandchild_quality:
            least_worst_grandchild_quality = worst_grandchild_quality
            least_worst_string_children = [string_child_matrix]
        elif worst_grandchild_quality == least_worst_grandchild_quality:
            least_worst_string_children.append(string_child_matrix)

    decided_string_child_matrix = random.choice(least_worst_string_children)
    decided_child_matrix = string_to_matrix(decided_string_child_matrix)

    end_time = time.time()
    elapsed_time = end_time - start_time
    deep_print("Elapsed time: " + str(elapsed_time), 0)

    return decided_child_matrix


if rank == 0:

    if size < 2:
        deep_print("There are not enough processes. Please restart with more.", 0)
        quit()

    result = 0

    deep_print(matrix_to_string(A), 0)

    while result == 0:

        deep_print("Choose a column. ", 0)
        column = int(input()) - 1
        deep_print("", 0)

        while not is_valid_input(A, column):
            deep_print("Invalid column, choose another. ", 0)
            column = int(input()) - 1

        row = find_empty_row(A, column)

        A[row][column] = Move.PLAY
        deep_print("You played", 0)
        deep_print(matrix_to_string(A), 0)
        deep_print("", 0)

        deep_print("___________________________________________", 1)

        result = calculate_matrix_quality_final(A)
        if result == 1:
            deep_print("You lost :(", 0)
            quit()
        elif result == -1:
            deep_print("You won :)", 0)
            quit()

        A = calculate_comp_move(A)
        deep_print("Computer played", 0)
        deep_print(matrix_to_string(A), 0)
        deep_print("", 0)

        result = calculate_matrix_quality_final(A)
        if result == 1:
            deep_print("You lost :(", 0)
            quit()
        elif result == -1:
            deep_print("You won :)", 0)
            quit()

else:

    while True:

        my_string_matrix = comm.recv(source=0)

        my_matrix = string_to_matrix(my_string_matrix)

        my_matrix_quality = calculate_matrix_quality(my_matrix, Move.COMP, calculate_depth - 2)

        deep_print("Process " + str(rank) + " got this matrix: \n" + my_string_matrix + "\nand calculated quality " + str(my_matrix_quality) + ".", 1)

        comm.send((my_matrix_quality, matrix_to_string(my_matrix)), dest=0)


