#!/usr/bin/env python3
"""Elevens solitaire: remove pairs that sum to 11 or J-Q-K trios.

A classic solitaire where you win by clearing all 52 cards from the table.
Only the Python standard library is used.
"""

import argparse
import random
import sys

RANKS = "A23456789TJQK"
SUITS = "♠♥♦♣"
CARD_NAMES = {"A": "A", "T": "10", "J": "J", "Q": "Q", "K": "K"}
FACE_POINTS = {"J": 11, "Q": 12, "K": 13}


def card_rank(card: str) -> str:
    return card[0]


def point_value(rank: str) -> int:
    """A=1, 2..9=face, 10=10. J/Q/K are face cards (not used in pairs)."""
    if rank == "A":
        return 1
    if rank in "23456789":
        return int(rank)
    if rank == "T":
        return 10
    return 0  # J/Q/K: face cards


def is_face_card(rank: str) -> bool:
    return rank in "JQK"


def fmt_card(card: str) -> str:
    rank = card_rank(card)
    suit = card[1]
    return f"{CARD_NAMES.get(rank, rank)}{suit}"


def new_deck(seed: int | None = None) -> list[str]:
    rng = random.Random(seed)
    deck = [r + s for r in RANKS for s in SUITS]
    rng.shuffle(deck)
    return deck


class Elevens:
    """Elevens solitaire state."""

    def __init__(self, seed: int | None = None):
        self.stock: list[str] = new_deck(seed)
        self.table: list[str | None] = [None] * 9
        self._deal_initial()

    def _deal_initial(self) -> None:
        for i in range(9):
            self.table[i] = self._draw()

    def _draw(self) -> str | None:
        return self.stock.pop() if self.stock else None

    # ---- rules ----

    def legal_pairs(self) -> list[tuple[int, int]]:
        """All index pairs summing to 11."""
        pairs = []
        for i in range(9):
            a = self.table[i]
            if a is None or is_face_card(card_rank(a)):
                continue
            for j in range(i + 1, 9):
                b = self.table[j]
                if b is None or is_face_card(card_rank(b)):
                    continue
                if point_value(card_rank(a)) + point_value(card_rank(b)) == 11:
                    pairs.append((i, j))
        return pairs

    def legal_triples(self) -> list[tuple[int, int, int]]:
        """All index triples forming a J-Q-K set (order irrelevant)."""
        idx = {"J": [], "Q": [], "K": []}
        for i in range(9):
            card = self.table[i]
            if card is None:
                continue
            r = card_rank(card)
            if r in idx:
                idx[r].append(i)
        return [
            (i, j, k)
            for i in idx["J"]
            for j in idx["Q"]
            for k in idx["K"]
        ]

    def has_legal_move(self) -> bool:
        return bool(self.legal_pairs() or self.legal_triples())

    def remove(self, indices: list[int]) -> None:
        """Remove cards at indices, replacing each from the stock."""
        if len(indices) == 2:
            if tuple(sorted(indices)) not in [tuple(sorted(p)) for p in self.legal_pairs()]:
                raise ValueError("这两张牌不能组成 11（A=1, 2-10 按点数，J/Q/K 不算）")
        elif len(indices) == 3:
            if tuple(sorted(indices)) not in [tuple(sorted(t)) for t in self.legal_triples()]:
                raise ValueError("这三张牌不是 J-Q-K 组合")
        else:
            raise ValueError("一次只能移走 2 张（点数和为 11）或 3 张（J-Q-K）")
        for i in indices:
            self.table[i] = self._draw()

    def cards_left(self) -> int:
        return sum(1 for c in self.table if c is not None) + len(self.stock)

    def is_won(self) -> bool:
        return self.cards_left() == 0

    def is_stuck(self) -> bool:
        return not self.is_won() and not self.has_legal_move()

    # ---- display ----

    def render(self) -> str:
        lines = []
        for row in (range(0, 3), range(3, 6), range(6, 9)):
            cells = []
            for i in row:
                c = self.table[i]
                cells.append(f"[{i}] {fmt_card(c):>4}" if c else f"[{i}]  ·  ")
            lines.append("  ".join(cells))
        lines.append(f"库存还剩 {len(self.stock)} 张 | 桌面 {sum(1 for c in self.table if c)} 张")
        return "\n".join(lines)


def auto_move(game: Elevens) -> bool:
    """Greedy bot: prefer trios, then the first pair. Returns False if stuck."""
    trips = game.legal_triples()
    if trips:
        game.remove(list(trips[0]))
        return True
    pairs = game.legal_pairs()
    if pairs:
        game.remove(list(pairs[0]))
        return True
    return False


def play_interactive(seed: int | None = None) -> int:
    game = Elevens(seed)
    print("=== Elevens 纸牌接龙 ===")
    print("规则：移走点数和为 11 的两张牌（A=1, 2-10 按点数，J/Q/K 不算）")
    print("     或移走一张 J + 一张 Q + 一张 K；腾出的位置会从库存补牌。")
    print("     把 52 张牌全部清掉即胜利。输入如：1 8（两张）或 2 4 6（三张），q 退出。\n")
    while True:
        print(game.render())
        if game.is_won():
            print("\n🎉 全部 52 张牌都清掉了！你赢了！")
            return 0
        if game.is_stuck():
            print(f"\n😞 无合法走法了，剩余 {game.cards_left()} 张，再接再厉！")
            return 1
        raw = input("选择牌（编号用空格隔开）> ").strip()
        if raw.lower() in {"q", "quit", "exit"}:
            print("已退出。")
            return 0
        try:
            indices = sorted({int(x) for x in raw.split()})
        except ValueError:
            print("请输入数字编号。")
            continue
        if any(i < 0 or i > 8 or game.table[i] is None for i in indices):
            print("编号无效或位置为空。")
            continue
        try:
            game.remove(indices)
        except ValueError as e:
            print(e)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Elevens 纸牌接龙：清掉所有 52 张牌（点数和 11 或 J-Q-K）。",
        prog="elevens",
    )
    parser.add_argument("--seed", type=int, default=None, help="随机种子")
    parser.add_argument("--auto", action="store_true", help="用贪心机器人自动玩")
    parser.add_argument("--moves", type=int, default=200, help="--auto 最多步数（默认 200）")
    args = parser.parse_args(argv)

    if args.auto:
        game = Elevens(args.seed)
        moves = 0
        while moves < args.moves:
            if not auto_move(game):
                break
            moves += 1
        if game.is_won():
            print(f"胜利！用了 {moves} 步清掉了全部 52 张牌（seed={args.seed}）。")
            return 0
        print(f"游戏结束：{'无合法走法' if game.is_stuck() else '达到步数上限'}，"
              f"还剩 {game.cards_left()} 张牌（seed={args.seed}）。")
        return 0
    return play_interactive(args.seed)


if __name__ == "__main__":
    sys.exit(main())
