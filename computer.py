"""The computer opponent: a greedy player that values the scoring cards."""
from casino import Move, State, legal_moves


def worth(card: str) -> float:
    """How much a card is worth to whoever holds it in their pile."""
    points = 1.0
    if card == "10D":
        points += 2
    if card == "2S":
        points += 1
    if card.startswith("A"):
        points += 1
    if card.endswith("S"):
        points += 0.5
    return points


def choose_move(state: State) -> Move:
    moves = legal_moves(state)
    last_card = sum(map(len, state.hands)) + len(state.talon) == 1

    def rate(move: Move) -> float:
        if move.table:
            gain = sum(worth(c) for c in move.hand | move.table)
            sweep = set(state.table) == set(move.table) and not last_card
            return gain + (3 if sweep else 0)
        # placing: give away as little as possible
        return -sum(worth(c) for c in move.hand) - 10

    return max(moves, key=lambda m: (rate(m), sorted(m.hand), sorted(m.table)))
