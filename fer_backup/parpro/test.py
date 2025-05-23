from enum import Enum
import random
from mpi4py import MPI
import time
import psutil


p = psutil.Process()
p.cpu_affinity([0, 1, 2, 3, 4, 5, 6, 7])


# mpiexec -n 8 python main.py

ROW_NUM = 6
COLUMN_NUM = 7

comm = MPI.COMM_WORLD
size = comm.Get_size()
rank = comm.Get_rank()

def change_turn(active_turn):
    if active_turn == "C":
        return "P"
    elif active_turn =="P":
        return "C"

def is_valid_input(matrix, x):
    return 0 <= x <= COLUMN_NUM - 1 and matrix[0][x] == "-"

def matrix_to_string(matrix):
    return "\n".join(" ".join(row) for row in matrix)

def string_to_matrix(string):
    return [row.split() for row in string.split('\n')]

def find_empty_row(matrix, column):
    for row in range(ROW_NUM - 1, -1, -1):
        if matrix[row][column] == "-":
            return row
    return -1

def calculate_child_matrices(matrix, active_turn):
    child_matrices = []

    for j in range(COLUMN_NUM):
        for i in range(ROW_NUM - 1, -1, -1):
            if matrix[i][j] == "-":
                matrix_copy = [row[:] for row in matrix]
                matrix_copy[i][j] = active_turn
                child_matrices.append(matrix_copy)

    return child_matrices

def check_winner(player_connected, computer_connected):
    if computer_connected == 4:
        return 1
    if player_connected == 4:
        return -1
    return 0

def check_diagonal(matrix, row, column, row_direction, column_direction):
    player_connected, computer_connected = 0, 0
    while 0 <= row < ROW_NUM and 0 <= column < COLUMN_NUM:
        if matrix[row][column] == "C":
            computer_connected += 1
            player_connected = 0
        elif matrix[row][column] == "P":
            player_connected += 1
            computer_connected = 0
        else:
            player_connected, computer_connected = 0, 0
        result = check_winner(player_connected, computer_connected)
        if result != 0:
            return result
        row += row_direction
        column += column_direction
    return 0

def calculate_matrix_quality_final(matrix):
    for i in range(ROW_NUM):
        player_connected, computer_connected = 0, 0
        for j in range(COLUMN_NUM):
            if matrix[i][j] == "C":
                computer_connected += 1
                player_connected = 0
            elif matrix[i][j] == "P":
                player_connected += 1
                computer_connected = 0
            else:
                player_connected, computer_connected = 0, 0

            result = check_winner(player_connected, computer_connected)
            if result != 0:
                return result

    for j in range(COLUMN_NUM):
        player_connected, computer_connected = 0, 0
        for i in range(ROW_NUM):
            if matrix[i][j] == "C":
                computer_connected += 1
                player_connected = 0
            elif matrix[i][j] == "P":
                player_connected += 1
                computer_connected = 0
            else:
                player_connected, computer_connected = 0, 0

            result = check_winner(player_connected, computer_connected)
            if result != 0:
                return result

    for i in range(ROW_NUM):
        for j in range(COLUMN_NUM):
            if i + 3 < ROW_NUM and j + 3 < COLUMN_NUM:
                result = check_diagonal(i, j, 1, 1)
                if result != 0:
                    return result
            if i - 3 >= 0 and j + 3 < COLUMN_NUM:
                result = check_diagonal(i, j, -1, 1)
                if result != 0:
                    return result

    return 0


def calculate_matrix_quality(matrix, active_turn, depth):
    child_matrices = calculate_child_matrices(matrix, active_turn)
    sum_of_child_matrices_qualities = 0
    num_of_child_matrices = len(child_matrices)

    for child_matrix in child_matrices:
        child_matrix_quality_final = calculate_matrix_quality_final(child_matrix)
        if depth == 0 or child_matrix_quality_final != 0:
            child_matrix_quality = child_matrix_quality_final
        else:
            child_matrix_quality = calculate_matrix_quality(child_matrix, change_turn(active_turn), depth - 1)

        if (active_turn == "C" and child_matrix_quality == 1) or (active_turn == "P" and child_matrix_quality == -1):
            return child_matrix_quality
        else:
            sum_of_child_matrices_qualities = sum_of_child_matrices_qualities + child_matrix_quality

    if num_of_child_matrices != 0:
        return sum_of_child_matrices_qualities / num_of_child_matrices

    return -1


def calculate_comp_move(matrix):
    start_time = time.time()

    child_matrices = calculate_child_matrices(matrix, "C")
    grandchild_matrices = []
    grandchild_to_child_matrix_mapping = {}

    for child_matrix in child_matrices:
        if calculate_matrix_quality_final(child_matrix) == 1:
            return child_matrix

        child_child_matrices = calculate_child_matrices(child_matrix, "P")

        if all(calculate_matrix_quality_final(grandchild_matrix) != -1 for grandchild_matrix in child_child_matrices):
            for grandchild_matrix in child_child_matrices:
                string_grandchild_matrix = matrix_to_string(grandchild_matrix)
                grandchild_matrices.append(string_grandchild_matrix)
                grandchild_to_child_matrix_mapping[string_grandchild_matrix] = child_matrix

    tasks_num = len(grandchild_matrices)
    if tasks_num == 0:
        return random.choice(child_matrices)

    worker_process_counter, sent_task_counter = 0, 0

    child_to_grandchild_matrix_quality_mapping = {matrix_to_string(child_matrix): [] for child_matrix in child_matrices}

    while worker_process_counter < size - 1 and sent_task_counter < tasks_num:
        comm.send(grandchild_matrices[sent_task_counter], dest=worker_process_counter + 1)
        sent_task_counter += 1
        worker_process_counter += 1

    worker_process_counter, received_task_counter = 0, 0

    while received_task_counter < tasks_num:
        if comm.Iprobe(source=worker_process_counter + 1):
            grandchild_matrix_quality, string_grandchild_matrix = comm.recv(source=worker_process_counter + 1)
            child_matrix = grandchild_to_child_matrix_mapping[string_grandchild_matrix]
            child_to_grandchild_matrix_quality_mapping[matrix_to_string(child_matrix)].append(grandchild_matrix_quality)

            received_task_counter += 1
            if sent_task_counter < tasks_num:
                comm.send(grandchild_matrices[sent_task_counter], dest=worker_process_counter + 1)
                sent_task_counter += 1

        worker_process_counter = (worker_process_counter + 1) % (size - 1)

    least_worst_grandchild_quality = -1
    least_worst_string_children = []

    for string_child_matrix, grandchildren_qualities in child_to_grandchild_matrix_quality_mapping:
        worst_grandchild_quality = min(grandchildren_qualities, default=0)
        if worst_grandchild_quality > least_worst_grandchild_quality:
            least_worst_grandchild_quality = worst_grandchild_quality
            least_worst_string_children = [string_child_matrix]
        elif worst_grandchild_quality == least_worst_grandchild_quality:
            least_worst_string_children.append(string_child_matrix)

    decided_string_child_matrix = random.choice(least_worst_string_children)
    decided_child_matrix = string_to_matrix(decided_string_child_matrix)

    elapsed_time = time.time - start_time
    print("Elapsed time: " + str(elapsed_time), flush=True)
    return decided_child_matrix


calculate_depth = 5   # minimum 5

game_matrix = []
for i in range(ROW_NUM):
    game_matrix.append([])
    for j in range(COLUMN_NUM):
        game_matrix[i].append("-")

if rank == 0:
    if size < 2:
        print("There are not enough processes. Please restart with more.", flush=True)
        quit()

    result = 0
    print(matrix_to_string(game_matrix), flush=True)

    while result == 0:
        print("Choose a column. ", flush=True)
        column = int(input()) - 1
        print("", flush=True)

        while not is_valid_input(game_matrix, column):
            print("Invalid column, choose another. ", flush=True)
            column = int(input()) - 1

        row = find_empty_row(game_matrix, column)

        game_matrix[row][column] = "P"
        print("You played", flush=True)
        print(matrix_to_string(game_matrix), flush=True)
        print("", flush=True)

        result = calculate_matrix_quality_final(game_matrix)
        if result == 1:
            print("You lost", flush=True)
            quit()
        elif result == -1:
            print("You won", flush=True)
            quit()

        game_matrix = calculate_comp_move(game_matrix)
        print("Computer played", flush=True)
        print(matrix_to_string(game_matrix), flush=True)
        print("", flush=True)

        result = calculate_matrix_quality_final(game_matrix)
        if result == 1:
            print("You lost", flush=True)
            quit()
        elif result == -1:
            print("You won", flush=True)
            quit()

else:
    while True:
        my_string_matrix = comm.recv(source=0)
        my_matrix = string_to_matrix(my_string_matrix)
        my_matrix_quality = calculate_matrix_quality(my_matrix, "C", calculate_depth - 2)
        comm.send((my_matrix_quality, matrix_to_string(my_matrix)), dest=0)