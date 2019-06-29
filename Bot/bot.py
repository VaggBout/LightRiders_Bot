import sys
from Bot.player import Player
from typing import List

PLAYER1, PLAYER2, EMPTY, BLOCKED = [0, 1, 2, 3]
S_PLAYER1, S_PLAYER2, S_EMPTY, S_BLOCKED, = ['0', '1', '.', 'x']

CHARTABLE = [(PLAYER1, S_PLAYER1), (PLAYER2, S_PLAYER2), (EMPTY, S_EMPTY), (BLOCKED, S_BLOCKED)]

DIRS = [
    ((-1, 0), "up"),
    ((0, 1), "right"),
    ((1, 0), "down"),
    ((0, -1), "left")
]


class Bot:
    def __init__(self):
        self.game = None
        self.last_move = None
        self.desired_depth = 3
        self.next_move = None
        self.score_options = {}

    def setup(self, game):
        self.game = game

    """
    returns the next possible position of the my bot based on the given direction
    """

    def next_pos(self, direction, pos=None):
        if direction == "up":
            if pos is None:
                return self.game.my_player().row - 1, self.game.my_player().col
            else:
                row, col = pos
                return row - 1, col
        elif direction == "down":
            if pos is None:
                return self.game.my_player().row + 1, self.game.my_player().col
            else:
                row, col = pos
                return row + 1, col
        elif direction == "left":
            if pos is None:
                return self.game.my_player().row, self.game.my_player().col - 1
            else:
                row, col = pos
                return row, col - 1
        elif direction == "right":
            if pos is None:
                return self.game.my_player().row, self.game.my_player().col + 1
            else:
                row, col = pos
                return row, col + 1

    """
    applies the flood fill algorithm for the given position
    """

    def flood_use(self, position):
        visited = []
        return self.flood_fill(position, visited)

    """
    flood fill algorithm implementation.
    Returns the count of legal boxes on our field for the given position
    """

    def flood_fill(self, position, visited):
        row, col = position
        # if we are out of bounds
        # or have already visited the current position
        # or can't visit this box
        if row < 0 or col < 0 or row > self.game.field_width - 1 or \
                        col > self.game.field_height - 1 or position in visited \
                or not self.game.field.is_legal_tuple(position, self.game.my_botid):
            return 0  # count is 0

        visited.append(position)  # mark current position as visited
        # get position count recursively from the current box till the end
        # or an illegal box
        return 1 + self.flood_fill((row - 1, col), visited) \
               + self.flood_fill((row + 1, col), visited) \
               + self.flood_fill((row, col - 1), visited) \
               + self.flood_fill((row, col + 1), visited)

    def do_turn(self):
        my_row = self.game.my_player().row
        my_col = self.game.my_player().col
        legal = self.game.field.legal_moves(self.game.my_botid, self.game.players)
        print(legal)

        if len(legal) == 0:
            desired_move = "pass"
        else:
            # remove useless tuples from legal var
            legal_dirs = []  # legal directions (legal moves w/o the tuples)
            for _, direction in legal:
                legal_dirs.append(direction)

            # if on first round
            # just head to the opposite direction of nearest wall
            if self.game.round == 0:
                # calculate distances from each wall
                dist_to_walls = {}
                dist_to_walls["up"] = my_row
                dist_to_walls["down"] = self.game.field_height - my_col
                dist_to_walls["left"] = my_col
                dist_to_walls["right"] = self.game.field_width - my_row

                # find max distance
                desired_move = max(dist_to_walls, key=dist_to_walls.get)

            # if not on first round
            else:
                # Remove unallowed moves (it seems that is_legal wasn't good enough)
                if self.last_move == "up":
                    try:
                        # legal_dirs.remove("up")
                        legal_dirs.remove("down")
                    except ValueError:
                        pass
                elif self.last_move == "down":
                    try:
                        # legal_dirs.remove("down")
                        legal_dirs.remove("up")
                    except ValueError:
                        pass
                elif self.last_move == "left":
                    try:
                        # legal_dirs.remove("left")
                        legal_dirs.remove("right")
                    except ValueError:
                        pass
                elif self.last_move == "right":
                    try:
                        # legal_dirs.remove("right")
                        legal_dirs.remove("left")
                    except ValueError:
                        pass

                # Check if any immediate neighbor square is illegal move and remove it
                my_id = self.game.my_botid
                if not self.game.field.is_legal_tuple((my_row - 1, my_col), my_id):
                    try:
                        legal_dirs.remove("up")
                    except ValueError:
                        pass
                if not self.game.field.is_legal_tuple((my_row + 1, my_col), my_id):
                    try:
                        legal_dirs.remove("down")
                    except ValueError:
                        pass
                if not self.game.field.is_legal_tuple((my_row, my_col - 1), my_id):
                    try:
                        legal_dirs.remove("left")
                    except ValueError:
                        pass
                if not self.game.field.is_legal_tuple((my_row, my_col + 1), my_id):
                    try:
                        legal_dirs.remove("right")
                    except ValueError:
                        pass

                if len(legal_dirs) == 1:
                    desired_move = legal_dirs[0]

                # Flood fill count in 2 directions to find max space and make the move
                # that leads there
                elif len(legal_dirs) == 2:
                    first_move = legal_dirs[0]
                    second_move = legal_dirs[1]
                    first_move_next = self.next_pos(first_move)
                    second_move_next = self.next_pos(second_move)
                    next_moves_counts = {}
                    next_moves_counts[first_move] = self.flood_use(first_move_next)
                    next_moves_counts[second_move] = self.flood_use(second_move_next)
                    # If equal use min max to calculate next moves
                    if next_moves_counts[first_move] == next_moves_counts[second_move]:
                        self.min_max(self.game, self.game.my_botid, self.game.players, self.game.field.desired_depth,
                                     -100000, 100000)
                        _, desired_move = self.next_move
                    else:
                        desired_move = max(next_moves_counts, key=next_moves_counts.get)

                # Flood fill count in 3 directions to find max space and make the move
                # that leads there
                elif len(legal_dirs) == 3:
                    first_move = legal_dirs[0]
                    second_move = legal_dirs[1]
                    third_move = legal_dirs[2]
                    first_move_next = self.next_pos(first_move)
                    second_move_next = self.next_pos(second_move)
                    third_move_next = self.next_pos(third_move)
                    next_moves_counts = {}
                    next_moves_counts[first_move] = self.flood_use(first_move_next)
                    next_moves_counts[second_move] = self.flood_use(second_move_next)
                    next_moves_counts[third_move] = self.flood_use(third_move_next)
                    if next_moves_counts[first_move] != next_moves_counts[second_move] or \
                                    next_moves_counts[first_move] != next_moves_counts[third_move] or \
                                    next_moves_counts[second_move] != next_moves_counts[third_move]:
                        desired_move = max(next_moves_counts, key=next_moves_counts.get)
                    else:
                        # If equal use min max to calculate next moves
                        self.min_max(self.game, self.game.my_botid, self.game.players, self.game.field.desired_depth, -100000, 100000)
                        print(self.game.field.next_move, file=sys.stderr)
                        print(self.next_move, file=sys.stderr)
                        _, desired_move = self.next_move
                else:  # this probably never comes up - not sure
                    desired_move = "pass"

        if desired_move == "pass":
            self.last_move = "pass"
            self.game.issue_order_pass()
        else:
            self.last_move = desired_move
            self.game.issue_order(desired_move)

    """
    MinMax algorithm with AB pruning implementation.
    Returns the best move for the given depth. 
    For desired_depth = 3 looks 3 moves ahead, for desired_depth =  5 looks 5 moves ahead etc.
    Score for moves is calculated using flood_fill.
    """

    def min_max(self, game, player_id: int, players: List[Player], depth: int, alpha: int, beta: int) -> int:
        legal_moves = self.game.field.legal_moves(player_id, players)
        if depth == 0 or len(legal_moves) == 0:
            return self.get_score(player_id, players)

        max_value = -1000000

        # order legal moves by near to middle
        # legal_moves.sort(key=lambda x: abs(x[0][0] - self.height) + abs(x[0][1] - self.width))
        # vs sort be near to enemy
        enemy = players[(player_id + 1) % 2]
        me = players[player_id]
        legal_moves.sort(key=lambda x: abs(me.row + x[0][0] - enemy.row) + abs(me.col + x[0][1] - enemy.col))

        while len(legal_moves) > 0:
            move = legal_moves.pop(0)
            self.make_move(game, players[player_id], player_id, move[0])
            value = -self.min_max(game, (player_id + 1) % 2, players, depth - 1, -beta, -alpha)
            self.make_move(game, players[player_id], player_id, move[0], reverse=True)

            if value > max_value:
                max_value = value

                if depth == self.desired_depth:
                    self.next_move = move

            if depth == self.desired_depth:
                self.score_options[move[1]] = value

            alpha = max(alpha, value)
            if alpha >= beta:
                break

        return max_value

    def make_move(self, game, chosen_player: Player, player_id: int, movement: tuple, reverse=False):

        cells_where_adjacency_changes = []
        for (o_row, o_col), _ in DIRS:
            cells_where_adjacency_changes.append((o_row + chosen_player.row, o_col + chosen_player.col))

        if not reverse:
            self.game.field.cell[chosen_player.row][chosen_player.col] = [BLOCKED]
        else:
            self.game.field.cell[chosen_player.row][chosen_player.col] = [EMPTY]
        # modify player object
        if not reverse:
            chosen_player.row += movement[0]
            chosen_player.col += movement[1]
        else:
            chosen_player.row -= movement[0]
            chosen_player.col -= movement[1]
        # modify field

        self.game.field.cell[chosen_player.row][chosen_player.col] = [PLAYER1] if player_id == game.my_botid else [PLAYER2]

        for (o_row, o_col), _ in DIRS:
            cells_where_adjacency_changes.append((o_row + chosen_player.row, o_col + chosen_player.col))

        # update all cells where adjacency has changed
        for cell in cells_where_adjacency_changes:
            self.game.field.get_adjacent(cell[0], cell[1], player_id, use_stored=False)

    """
    Calculates the score for each move using flood_fill algorithm 
    """

    def get_score(self, my_player_id: int, players: List[Player]) -> int:
        my_legal_moves = self.game.field.legal_moves(my_player_id, players)
        enemy_legal_moves = self.game.field.legal_moves((my_player_id + 1) % 2, players)
        my_score = 0
        enemy_score = 0

        for _, moves in my_legal_moves:
            next_move = self.next_pos(moves)
            my_score = my_score + self.flood_use(next_move)

        for _, moves in enemy_legal_moves:
            next_move = self.next_pos(moves)
            enemy_score = enemy_score + self.flood_use(next_move)
        # score*100 for better results
        return 100*(my_score - 2 * enemy_score)
