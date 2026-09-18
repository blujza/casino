"""Hungarian two-player Cassino with a 52-card French deck.

A card is a string: rank, then suit ("10D", "AS", "QH").
Ranks: A 2 3 4 5 6 7 8 9 10 J Q K (worth 1..13). Suits: S H D C.

Rules as the module plays them:

* Each round both players get three cards; the four table cards are dealt once.
* On your turn you either place one card on the table, or capture: play one
  or more cards from your hand and take table cards that can be split into
  groups that each add up to the played cards' total.
* Taking every table card is a sweep (one point), except with the last card
  of the deal. After a sweep the opponent moves twice in a row.
* When both hands are empty the last player to capture draws three cards,
  deals the opponent three, and leads. The table stays as it is.
* At the end of the deal the remaining table cards go to the last capturer.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from functools import lru_cache
from itertools import combinations
from typing import NamedTuple, Sequence

RANKS = ("A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K")
SUITS = "SHDC"
DECK = tuple(rank + suit for suit in SUITS for rank in RANKS)

_VALUES = {rank: number for number, rank in enumerate(RANKS, 1)}


def value(card: str) -> int:
    return _VALUES[card[:-1]]


class Move(NamedTuple):
    """Cards played from the hand, and cards taken from the table."""

    hand: frozenset
    table: frozenset


@dataclass(frozen=True)
class State:
    hands: tuple
    table: tuple
    talon: tuple
    piles: tuple = ((), ())
    sweeps: tuple = (0, 0)
    player: int = 0
    last_capturer: int | None = None
    again: bool = False  # the player to move gets a second move after this one


def new_deal(deck: Sequence[str], first: int = 0) -> State:
    if sorted(deck) != sorted(DECK):
        raise ValueError("the deck must hold each of the 52 cards exactly once")
    deck = tuple(deck)
    hands = [(), ()]
    hands[first] = deck[0:3]
    hands[1 - first] = deck[3:6]
    return State(tuple(hands), deck[6:10], deck[10:], player=first)


def deal_over(state: State) -> bool:
    return not (state.hands[0] or state.hands[1] or state.talon or state.table)


@lru_cache(maxsize=None)
def _splits(values: tuple, target: int) -> bool:
    """Can these values be divided into groups that each add up to target?"""
    if not values:
        return True
    if sum(values) % target:
        return False
    first, rest = values[0], values[1:]
    for size in range(len(rest) + 1):
        for chosen in combinations(range(len(rest)), size):
            if first + sum(rest[i] for i in chosen) == target:
                remaining = tuple(v for i, v in enumerate(rest) if i not in chosen)
                if _splits(remaining, target):
                    return True
    return False


def _captures(taken: Sequence[str], target: int) -> bool:
    return _splits(tuple(sorted(value(c) for c in taken)), target)


def legal_moves(state: State) -> list[Move]:
    if deal_over(state):
        return []
    hand = state.hands[state.player]
    moves = [Move(frozenset({card}), frozenset()) for card in hand]
    for size in range(1, len(hand) + 1):
        for held in combinations(hand, size):
            target = sum(value(c) for c in held)
            candidates = [c for c in state.table if value(c) <= target]
            for count in range(1, len(candidates) + 1):
                for taken in combinations(candidates, count):
                    if _captures(taken, target):
                        moves.append(Move(frozenset(held), frozenset(taken)))
    return moves


def _check(state: State, move: Move) -> None:
    if deal_over(state):
        raise ValueError("the deal is over")
    hand = state.hands[state.player]
    if not move.hand or not move.hand <= set(hand):
        raise ValueError("you can only play cards from your hand")
    if not move.table:
        if len(move.hand) != 1:
            raise ValueError("place one card at a time")
        return
    if not move.table <= set(state.table):
        raise ValueError("you can only take cards from the table")
    if not _captures(tuple(move.table), sum(value(c) for c in move.hand)):
        raise ValueError("the cards taken must add up to the cards played")


def _replace(pair: tuple, index: int, item) -> tuple:
    return tuple(item if i == index else x for i, x in enumerate(pair))


def play(state: State, move: Move) -> State:
    _check(state, move)
    me, other = state.player, 1 - state.player

    played = tuple(c for c in state.hands[me] if c in move.hand)
    hands = _replace(state.hands, me, tuple(c for c in state.hands[me] if c not in move.hand))
    table, piles, last = state.table, state.piles, state.last_capturer
    if move.table:
        taken = tuple(c for c in table if c in move.table)
        table = tuple(c for c in table if c not in move.table)
        piles = _replace(piles, me, piles[me] + played + taken)
        last = me
    else:
        table = table + played

    talon, sweeps = state.talon, state.sweeps
    finished = not (hands[0] or hands[1] or talon)
    sweep = bool(move.table) and not table and not finished
    if sweep:
        sweeps = _replace(sweeps, me, sweeps[me] + 1)

    again = False
    if sweep:
        nxt, again = other, True
    elif state.again and hands[me]:
        nxt = me
    else:
        nxt = other
    if not hands[nxt] and hands[1 - nxt]:
        nxt, again = 1 - nxt, False

    if finished:
        owner = last if last is not None else me
        piles = _replace(piles, owner, piles[owner] + table)
        table = ()
    elif not (hands[0] or hands[1]):
        lead = last if last is not None else nxt
        hands = _replace(_replace(hands, lead, talon[0:3]), 1 - lead, talon[3:6])
        talon = talon[6:]
        nxt, again = lead, False

    return replace(state, hands=hands, table=table, talon=talon, piles=piles,
                   sweeps=sweeps, player=nxt, last_capturer=last, again=again)


def score(state: State) -> tuple[int, int]:
    """Points each player earned in the finished deal."""
    points = []
    for player in (0, 1):
        pile = state.piles[player]
        points.append(
            (3 if len(pile) >= 27 else 0)
            + (2 if sum(c.endswith("S") for c in pile) >= 7 else 0)
            + sum(c.startswith("A") for c in pile)
            + (2 if "10D" in pile else 0)
            + (1 if "2S" in pile else 0)
            + state.sweeps[player]
        )
    return tuple(points)
