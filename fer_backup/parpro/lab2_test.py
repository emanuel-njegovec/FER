from mpi4py import MPI
# import time
import sys

BOARD_WIDTH = 7  # default number of columns in a board
MAX_DEPTH = 7  # maximum depth of recursion


def check_winner(test_board, last_entered):  # method for determining if last entered column won the game
    last_row = len(test_board[last_entered]) - 1  # index of last entered row is one less than length of column
    check_lists = [test_board[last_entered]]
    # check_lists will be a collection of all possible combinations which could have a winning line
    # this includes the column itself
    row_list, diag_1, diag_2 = {}, {}, {}  # also the whole row and two diagonals
    var_x, var_y = last_row - last_entered, last_row + last_entered
    # variables for determining if position is on the same diagonal
    # diff of row and col indices (var_x) is for upwards diagonal
    # sum of row and col indices (var_y) is for downwards diagonal
    for col_index, col in enumerate(test_board):  # loop over board columns and their indices
        if last_row in col:  # if column has item in position of last entered row
            row_list[col_index] = col[last_row]  # add to row_list dict
    # using dict solves the problem of rows with missing items, ex. "= C = C C C P"
    # every item is stored in dict with their column index as the key
    # this is important in the win_cond function below
    for col in range(BOARD_WIDTH):  # for every column in board
        for row in range(last_row - 7, last_row + 7):  # rows in diagonal can be anywhere from 7 below to 7 above
            if row in test_board[col]:  # if column has item in row
                if row - col == var_x:  # if item is on the same upwards diagonal
                    diag_1[col] = test_board[col][row]  # add item to diagonal
                if row + col == var_y:  # if item is on the same downwards diagonal
                    diag_2[col] = test_board[col][row]  # add to diagonal
            # diagonals are also dict where key of item is column index
    # add row and two diagonals in check_lists
    check_lists.append(diag_1)
    check_lists.append(diag_2)
    check_lists.append(row_list)
    for cl in check_lists:  # for every possible winning line
        if len(cl) >= 4:  # if it is 4 or longer (need 4 to connect4)
            result = win_cond(cl)  # test it
            if result != "0":  # if result is other than '0' ('P' or 'C' has won)
                return result  # don't need to look anymore, send winning item/player ('P' or 'C')
    return "0"  # if no one had won, return '0'


def win_cond(test_line):
    # test_line is a dictionary with column indices as keys
    count = 1  # variable for counting consecutive items (1 for current item)
    for index in range(BOARD_WIDTH):  # loop through column indices
        if index > 0:  # if column is not first
            if (index - 1) in test_line and index in test_line:  # if line has items in both previous and curr columns
                if test_line[index - 1] == test_line[index]:  # if item in previous column equals one in current column
                    count += 1  # increment count
                    if count == 4:  # if count has reached 4, winning line has been found, game is over
                        return test_line[index]  # return winning item/player
                else:  # restart counting because different item is encountered
                    count = 1
            else:  # restart counting because test_line has no item in column
                count = 1
    return "0"  # if no one has won, return "0"

def evaluate(board, last_entered, curr_depth, max_depth):  # recursive method for evaluating move quality
    pot_win = check_winner(board, last_entered)  # check if last entered item won the game
    # evaluation favors computer, and returns positive and negative values accordingly
    if pot_win == "C":
        return 1
    elif pot_win == "P":
        return -1
    if curr_depth == max_depth-1:  # if depth has reached recursion maximum depth, return 0 (don't evaluate further)
        return 0
    curr_depth += 1
    curr_move = "C" if curr_depth % 2 == 0 else "P"  # depending on depth, current move/player is determined
    total = 0  # total sum of all 7 possible combinations from current (1 next move in each column)
    all_lost, all_won = True, True  # boolean variables for returning absolute wins and losses
    for col in range(BOARD_WIDTH):  # loop through all column indices
        board[col][len(board[col])] = curr_move  # make a temporary move
        result = evaluate(board, col, curr_depth, max_depth)  # evaluate its quality
        board[col].pop(len(board[col]) - 1, None)  # undo the move
        if result > -1:
            all_lost = False
        if result != 1:
            all_won = False
        # if a win by computer is possible, it will always select the winning move
        if result == 1 and curr_move == "C":
            return 1
        # if a loss from player is possible, consider that player always also selects the correct move
        if result == -1 and curr_move == "P":
            return -1
        total += result
    if all_won:
        return 1
    if all_lost:
        return -1
    return total / BOARD_WIDTH  # total quality of last_entered move is sum of all possible next moves qualities


def get_best_move(board):  # function for deciding what the next best move for the computer is
    dest_rank = 1  # initialize destination location to 1
    sent = []  # a list of destination ranks where tasks were sent
    values = [0.0] * BOARD_WIDTH  # list for determining column with highest play quality
    if size > 1:  # if there is more than 1 process, send tasks to it
        # first loop through every column that doesn't go to rank 0
        # for example, if size is 4
        # |0,4|  |1,5|  |2,6|  |3  |  -> columns
        # ‾‾0‾‾  ‾‾1‾‾  ‾‾2‾‾  ‾‾3‾‾  -> ranks
        # loop through tasks 1, 2, 3, 5, 6
        for i in range(1, BOARD_WIDTH):
            if dest_rank == 0:  # skip rank 0
                dest_rank = 1
                i += 1
                continue
            comm.send({"board": board, "column": i, "depth": 0}, dest=dest_rank, tag=0)  # send task to process
            sent.append(dest_rank)  # add dest_rank to list of destinations
            dest_rank += 1  # select next dest_rank

            if dest_rank == size:  # if dest_rank reached size of environment
                dest_rank = 0  # start again from 0
    # now loop through all board column indices which rank 0 calculates
    # in above given example it would columns 0 and 4
    for i in range(0, BOARD_WIDTH, size):
        board[i][len(board[i])] = "C"  # make a move
        # if this move is part of the surplus (in the above example 4 is a surplus column)
        if size > 1 and rank in overused and leftover != 0 and i >= BOARD_WIDTH - leftover:
            values[i] = divide_surplus(board, 0, "C")  # divide it end send parts to other tasks
        else:  # if move is not surplus, calculate its quality value here
            values[i] = evaluate(board, i, 0, MAX_DEPTH)
        board[i].pop(len(board[i]) - 1, None)  # undo the move
    st = MPI.Status()  # mpi status used to find message source
    while len(sent) > 0 and size > 1:  # while there are still destinations which haven't returned a value
        answer = comm.recv(source=MPI.ANY_SOURCE, tag=0, status=st)  # wait for message from any source
        values[answer["column"]] = answer["value"]  # set move quality value of calculated move
        sent.pop(sent.index(st.Get_source()))  # remove message source from list of pending sources
    value_string = ""
    for i in range(BOARD_WIDTH):  # loop through all move qualities
        value_string += str('%.3f' % values[i]) + " "
    print(value_string)  # output move values rounded to 3 decimal places separated by spaces
    return values.index(max(values))  # return index of column where next move is of highest quality


def divide_surplus(brd, dpth, itm):
    work_values = [0.0] * BOARD_WIDTH  # divide current move quality to number (7) of qualities of next moves
    if itm == "C":
        nxt = "P"
    else:
        nxt = "C"
    work_dest_rank = underused[0]  # initialize dest to first underused worker
    next_index = 1  # index for iterating through underused list
    work_sent = []  # list of destinations where help with surplus tasks is requested

    for surplus_part in range(BOARD_WIDTH):  # loop through divided surplus
        # surplus is divided into columns with qualities which are in equal parts calculated,
        # and sent to underused workers, (if there is one overused worker and 2 underused,
        # third of overused workers' surplus is calculated by worker,
        # and the other two thirds are sent to the 2 underused workers
        if surplus_part < BOARD_WIDTH - int(leftover*(BOARD_WIDTH/size)):
            # parts of the surplus that are sent are sent before the other parts are calculated,
            # so that the process doesn't waste time waiting for answers
            comm.send({"board": brd, "column": surplus_part, "depth": dpth + 1},
                      dest=work_dest_rank, tag=1)  # send task to underused worker with tag 1
            work_sent.append(work_dest_rank)  # add destination to list of sent destinations
            if len(underused) - 1 >= next_index:  # if there are more underused workers
                work_dest_rank = underused[next_index]  # select next destination
                next_index += 1  # increment index
            else:
                next_index = 1  # if all underused workers have been sent tasks
                work_dest_rank = underused[0]  # restart destination to first underused worker
        else:  # this is part of the unsent surplus that is calculated here
            brd[surplus_part][len(brd[surplus_part])] = nxt  # insert move
            work_values[surplus_part] = evaluate(brd, surplus_part, dpth + 1, MAX_DEPTH)
            # calculate its quality
            brd[surplus_part].pop(len(brd[surplus_part]) - 1, None)  # undo insertion
    w_st = MPI.Status()
    while len(work_sent) > 0:  # while there are underused workers who haven't returned values
        # receive calculated values from underused workers (now used correctly) with tag 1
        work_help = comm.recv(source=MPI.ANY_SOURCE, tag=1, status=w_st)
        work_values[work_help["column"]] = work_help["value"]  # add value to correct column
        work_sent.pop(work_sent.index(w_st.Get_source()))  # remove source from pending sources
    if -1 in work_values and nxt == "P":  # if there is a possible loss in next move, this state is also a loss
        return -1
    if 1 in work_values and nxt == "C":  # if there is a possible win in next move, and this state is also a win
        return 1
    # return move quality value by summing all next move quality values and dividing by number of next moves
    return sum(work_values)/BOARD_WIDTH


class Game:
    def __init__(self, width):
        self.board = []  # game board is a list of columns
        for col_index in range(width):
            self.board.append({})
        # [self.board.append({}) for col_index in range(width)]  # number of columns is the board width (default = 7)

    def enter(self, col, player):  # entering char ('P' or 'C') in the desired column
        self.board[col][len(self.board[col])] = player
        # dictionary length of selected column is used to determine position of item (always on top of last item in col)

    def __repr__(self):  # Board output format
        result = ""
        max_row = 7  # start with 7 rows
        for col in self.board:
            if len(col) > max_row:  # if a column has more rows, new max is that number
                max_row = len(col)
        for row in range(max_row - 1, -1, -1):  # for every row from max to 0
            for col in self.board:  # for every column
                if row in col:  # if col (dict) has item in row
                    result += col[row]  # add selected item ('P' or 'C')
                else:  # if not, location is empty
                    result += "="  # add empty sign ('=')
            result += "\n"
        return result


comm = MPI.COMM_WORLD  # initialize mpi environment
rank = comm.Get_rank()  # every process receives its own rank number
size = comm.size  # each process knows the size of the environment
if size < 1 or size > 8:  # size is only allowed to be in the selected interval
    if rank == 0:
        print("size must be [1-8]")
    exit(1)  # if size number is not in interval, terminate execution

overused = []  # list of processes which would have more tasks
underused = []  # list of processes which have less tasks and would be wasted when finished own work
# example for 4 worker processes
#
# |0,4|  |1,5|  |2,6|  |3  |   -> column indices which process gets
# ‾‾1‾‾  ‾‾2‾‾  ‾‾3‾‾  ‾‾4‾‾   -> ranks of worker processes
# over   over   over   under   -> list in which worker belongs
#
underused_num = BOARD_WIDTH % size  # calculated number of underused workers
leftover = BOARD_WIDTH % size  # number of workers which would have surplus tasks
for n in range(0, underused_num):  # loop through ranks of overused workers (from 1 to (first underused rank-1))
    overused.append(n)  # add worker with surplus to overused list
for n in range(underused_num, size):  # loop through ranks of underused workers (from first underused to end)
    underused.append(n)  # add worker without surplus to underused list
# if rank == 0:
#     print("underused", underused)
#     print("overused", overused)
#     sys.stdout.flush()


if rank == 0:  # main game logic is always on first process (with rank 0)
    game = Game(BOARD_WIDTH)  # instanciate a new Game object with default board width
    # print(game)
    while 1:  # loop game until someone wins
        # player turn ---------------------------------------
        while 1:  # loop until input inside allowed bounds (column indices)
            col_num = int(input())  # enter number from [0 - 6]
            if 0 <= col_num <= BOARD_WIDTH - 1:
                game.enter(int(col_num), "P")  # enter disc in selected column (height is not restricted)
                winner = check_winner(game.board, int(col_num))  # check if this move won the game
                if winner == "P":  # if it did, end the game
                    print(game)
                    sys.stdout.flush()
                    # print("Player", winner, "has won!")
                    exit(1)
                break
        # print(game)
        # sys.stdout.flush()
        # computer turn ---------------------------------------
        # start = time.time()
        move = get_best_move(game.board)  # computers next move is calculated inside get_best_move function
        # print(time.time()-start)
        # sys.stdout.flush()
        game.enter(move, "C")  # computer enters returned move
        winner = check_winner(game.board, move)  # check if this move won the game
        if not winner == "0":  # if it did, end the game
            print(game)
            sys.stdout.flush()
            # print("Player", winner, "has won!")
            exit(1)
        print(game)
        sys.stdout.flush()
        # repeat until finished ---------------------------------------

else:  # if rank is other than 0, the process is a worker
    work_st = MPI.Status()  # mpi status for finding task source
    while 1:  # forever wait for upcoming tasks
        work = comm.recv(source=MPI.ANY_SOURCE, tag=MPI.ANY_TAG, status=work_st)
        # dissect work task to current board, column of desired move quality, and current depth variables
        work_board = work["board"]
        work_col = work["column"]
        work_depth = work["depth"]
        # save source and tag of received message
        work_source = work_st.Get_source()
        work_tag = work_st.Get_tag()
        if work_tag == 0 and work_source == 0:  # determine current and next moves depending on tag of message
            curr_item = "C"
            next_item = "P"
        else:
            curr_item = "P"
            next_item = "C"
        work_board[work_col][len(work_board[work_col])] = curr_item  # make move to received (task desired) column
        # if task message tag is 0, it was sent from get_best_move function
        # if not, some other worker sent part of its surplus
        # if there is some leftover (surplus exists), and if column is part of the surplus
        # |0,4|  |1,5|  |2,6|  |3  |  -> in mentioned example, surplus would be columns 4, 5, 6
        # ‾‾1‾‾  ‾‾2‾‾  ‾‾3‾‾  ‾‾4‾‾
        if rank in overused and work_tag == 0 and leftover != 0 and work_col >= BOARD_WIDTH - leftover:
            # if current task is worker surplus, divide it and send some to underused workers
            value = divide_surplus(work_board, work_depth, curr_item)
        else:
            value = evaluate(work_board, work_col, work_depth, MAX_DEPTH)  # evaluate move quality value
        work_board[work_col].pop(len(work_board[work_col]) - 1, None)  # undo move
        # return calculated move quality value
        comm.send({"value": value, "column": work_col}, dest=work_source, tag=work_tag)
