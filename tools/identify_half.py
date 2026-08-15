#!/usr/bin/env python3
"""ブートローダーの CURRENT.UF2 から、その半分に何のファームが入っているかを判定する。

UF2 ブートローダーは現在のフラッシュ内容を `CURRENT.UF2` として見せる。これを
`firmware/` に置いてある uf2 と突き合わせれば、いまブートローダーに入っているのが
左手側か右手側かを、書き込む前に確定できる。

`tools/flash.sh` は `/Volumes/*` の中で `INFO_UF2.TXT` を持つ最初のドライブに
書き込むだけで左右を区別しないため、意図と違う側に焼く事故が起こりうる。
それを防ぐために使う。

使い方:
    python3 tools/identify_half.py <CURRENT.UF2> <照合する uf2> [<uf2> ...]

一致率の高い順に `<ラベル> <一致率>` を 1 行ずつ出す。呼び出し側は先頭行を見ればよい。

    $ python3 tools/identify_half.py /Volumes/XIAO-SENSE/CURRENT.UF2 \
          firmware/20260816_zmk4.1_dya-studio/CLine46_{L,R}.uf2
    CLine46_R 84.1
    CLine46_L 2.2

設定リセット直後は先頭 60KB ほどが settings_reset で上書きされるだけで、その先には
前のファームが残る。上の例のように L と R だけで比べれば、リセット後でも
どちら側かは判別できる。
"""

import struct
import sys

UF2_MAGIC0 = 0x0A324655
UF2_MAGIC1 = 0x9E5D5157
UF2_BLOCK = 512
UF2_PAYLOAD_MAX = 476


def load(path):
    """uf2 を {アドレス: バイト} に展開する。"""
    memory = {}
    with open(path, "rb") as fh:
        data = fh.read()
    for offset in range(0, len(data) - len(data) % UF2_BLOCK, UF2_BLOCK):
        block = data[offset:offset + UF2_BLOCK]
        magic0, magic1, _flags, addr, length = struct.unpack_from("<5I", block)
        if magic0 != UF2_MAGIC0 or magic1 != UF2_MAGIC1:
            continue
        for i in range(min(length, UF2_PAYLOAD_MAX)):
            memory[addr + i] = block[32 + i]
    return memory


def compare(current, reference):
    """重なっている範囲での一致率（%）を返す。"""
    common = reference.keys() & current.keys()
    if not common:
        return 0.0
    same = sum(1 for addr in common if reference[addr] == current[addr])
    return 100.0 * same / len(common)


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        return 2

    current = load(sys.argv[1])

    scores = []
    for path in sys.argv[2:]:
        # firmware/.../CLine46_L.uf2 -> CLine46_L
        label = path.split("/")[-1].rsplit(".", 1)[0]
        scores.append((compare(current, load(path)), label))

    scores.sort(reverse=True)
    for score, label in scores:
        print(f"{label} {score:.1f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
