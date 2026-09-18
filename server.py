"""Play Cassino in the browser: `python server.py`, then open http://localhost:8000.

You are player 0, the computer is player 1.
"""
import json
import random
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

from casino import DECK, Move, deal_over, new_deal, play, score
from computer import choose_move

PAGE = Path(__file__).with_name("static") / "index.html"
YOU, COMPUTER = 0, 1

game = {"state": None, "log": []}


def describe(who: str, move: Move) -> str:
    hand = ", ".join(sorted(move.hand))
    if move.table:
        return f"{who} took {', '.join(sorted(move.table))} with {hand}"
    return f"{who} placed {hand}"


def computer_turns() -> None:
    while not deal_over(game["state"]) and game["state"].player == COMPUTER:
        move = choose_move(game["state"])
        before = game["state"].sweeps[COMPUTER]
        game["state"] = play(game["state"], move)
        game["log"].append(describe("Computer", move))
        if game["state"].sweeps[COMPUTER] > before:
            game["log"].append("Computer swept the table!")


def start_deal() -> None:
    cards = list(DECK)
    random.shuffle(cards)
    game["state"] = new_deal(cards, first=random.choice((YOU, COMPUTER)))
    game["log"] = ["New deal."]
    computer_turns()


def view() -> dict:
    s = game["state"]
    over = deal_over(s)
    return {
        "hand": list(s.hands[YOU]),
        "computerCards": len(s.hands[COMPUTER]),
        "table": list(s.table),
        "talon": len(s.talon),
        "piles": [len(p) for p in s.piles],
        "sweeps": list(s.sweeps),
        "yourTurn": s.player == YOU and not over,
        "over": over,
        "score": list(score(s)) if over else None,
        "log": game["log"],
    }


class Handler(BaseHTTPRequestHandler):
    def send(self, status: int, body: bytes, kind: str = "application/json") -> None:
        self.send_response(status)
        self.send_header("Content-Type", kind)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def send_json(self, payload: dict, status: int = 200) -> None:
        self.send(status, json.dumps(payload).encode())

    def do_GET(self) -> None:
        if self.path == "/api/state":
            self.send_json(view())
        elif self.path in ("/", "/index.html"):
            self.send(200, PAGE.read_bytes(), "text/html; charset=utf-8")
        else:
            self.send(404, b"not found", "text/plain")

    def do_POST(self) -> None:
        if self.path == "/api/new":
            start_deal()
            return self.send_json(view())
        if self.path != "/api/move":
            return self.send(404, b"not found", "text/plain")
        length = int(self.headers.get("Content-Length", 0))
        try:
            data = json.loads(self.rfile.read(length))
            move = Move(frozenset(data["hand"]), frozenset(data["table"]))
            if game["state"].player != YOU:
                raise ValueError("it is not your turn")
            game["state"] = play(game["state"], move)
        except (ValueError, KeyError, TypeError) as error:
            return self.send_json({"error": str(error)}, 400)
        game["log"].append(describe("You", move))
        computer_turns()
        self.send_json(view())

    def log_message(self, *args) -> None:
        pass


if __name__ == "__main__":
    start_deal()
    print("Cassino: http://localhost:8000")
    HTTPServer(("localhost", 8000), Handler).serve_forever()
