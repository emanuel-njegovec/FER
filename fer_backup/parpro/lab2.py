from mpi4py import MPI

class Board:
    def __init__(self, width, height, max_depth):
        self.width = width
        self.height = height
        self.board = [[0 for _ in range(width)] for _ in range(height)]
        self.max_depth = max_depth

    def print_board(self):
        for row in self.board:
            print(" ".join(str(cell) for cell in row))
        print()

    def set_value(self, col, value):
        if col < 0 or col >= self.width:
            raise ValueError("Column index out of bounds")
        for row in reversed(self.board):
            if row[col] == 0:
                row[col] = value
                return
        raise ValueError("Column is full")

    def check_horizontal(self, row, col, value):
        count = 0
        for c in range(self.width):
            if self.board[row][c] == value:
                count += 1
                if count == 4:
                    return True
            else:
                count = 0
        return False

    def check_vertical(self, col, value):
        count = 0
        for r in range(self.height):
            if self.board[r][col] == value:
                count += 1
                if count == 4:
                    return True
            else:
                count = 0
        return False

    def check_diagonal(self, row, col, value):
        count = 0
        for r in range(self.height):
            for c in range(self.width):
                if self.board[r][c] == value:
                    count += 1
                    if count == 4:
                        return True
                else:
                    count = 0
        count = 0
        for r in range(self.height):
            for c in range(self.width):
                if self.board[r][c] == value:
                    count += 1
                    if count == 4:
                        return True
                else:
                    count = 0
        return False

    def check_winner(self, col):
        for row in range(self.height):
            if self.board[row][col] != 0:
                value = self.board[row][col]
                if self.check_horizontal(row, col, value):
                    return True
                if self.check_vertical(col, value):
                    return True
                if self.check_diagonal(row, col, value):
                    return True
        return False

    def get_possible_moves(self):
        possible_moves = []
        for col in range(self.width):
            if self.board[0][col] == 0:
                possible_moves.append(col)
        return possible_moves

    def evaluate(self, col, player, depth):
        win = self.check_winner(col)
        if win and player == 'C':
            return 1
        elif win and player == 'P':
            return -1
        elif depth == self.max_depth - 1:
            return 0
        depth += 1
        score = 0
        for move in self.get_possible_moves():
            self.set_value(move, player)
            if player == 'C':
                score += self.evaluate(move, 'P', depth + 1)
            else:
                score += self.evaluate(move, 'C', depth + 1)
            self.undo_move(move)
        return score / self.width


    def best_move(self):
        moves = self.get_possible_moves()
        qualities = []
        for move in moves:
            done = self.play_move(move, 'C')
            if done:
                return move
            qualities.append(self.evaluate(move, 'C', 0))
            self.undo_move(move)
        return moves[qualities.index(max(qualities))]

    def play_move(self, col, value):
        try:
            self.set_value(col, value)
            winner = self.check_winner(col)
            if winner:
                print(f"Player {value} wins!")
                return True
        except ValueError as e:
            print(e)

    def undo_move(self, col):
        for row in range(self.height):
            if self.board[row][col] != 0:
                self.board[row][col] = 0
                break

    def play(self):
        self.print_board()
        while True:
            col = int(input("Enter column (0-6): "))
            if col < 0 or col >= self.width:
                print("Invalid column. Try again.")
                continue
            player = 'P'
            done = self.play_move(col, player)
            self.print_board()
            if done:
                break
            print()
            comp_move = self.best_move()
            player = 'C'
            done = self.play_move(comp_move, player)
            self.print_board()
            if done:
                break

comm = MPI.COMM_WORLD
rank = comm.Get_rank()
size = comm.Get_size()

if rank == 0:
    width = 7
    height = 6
    game = Board(width, height, 2)
    game.play()