#!/usr/bin/env python3
"""CLine46 のキーマップ／シールド定義を静的に検証する。

ZMK のビルド環境なしで、編集直後に「キー数が合わない」「存在しないレイヤーを
参照している」といった典型的なミスを検出するためのスクリプト。
Python 標準ライブラリのみで動作する。

    python3 tools/check_keymap.py

エラーが 1 件でもあれば終了コード 1 を返す。
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
KEYMAP_PATH = REPO_ROOT / "config" / "CLine46.keymap"
DTSI_PATH = REPO_ROOT / "boards" / "shields" / "CLine46" / "CLine46.dtsi"

# CLine46 の物理キー数（12 + 12 + 12 + 10）
EXPECTED_KEY_COUNT = 46

# 第 1 引数がレイヤー番号になる behavior
LAYER_ARG_BEHAVIORS = ("mo", "to", "tog", "sl", "lt", "lt_to_layer_0")

errors: list[str] = []
warnings: list[str] = []


def strip_comments(text: str) -> str:
    text = re.sub(r"/\*.*?\*/", " ", text, flags=re.S)
    text = re.sub(r"//[^\n]*", " ", text)
    return text


def block_body(text: str, open_index: int) -> tuple[str, int]:
    """text[open_index] == '{' として、対応する '}' までの中身と終端位置を返す。"""
    depth = 0
    for i in range(open_index, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                return text[open_index + 1 : i], i
    raise ValueError(f"閉じ括弧が見つかりません (位置 {open_index})")


def find_named_block(text: str, name: str) -> str | None:
    """`name { ... }` の中身を返す。ラベル付き (`name: node {`) にも対応する。"""
    pattern = rf"\b{re.escape(name)}\s*(?::\s*[A-Za-z_][\w-]*\s*)?\{{"
    for match in re.finditer(pattern, text):
        body, _ = block_body(text, match.end() - 1)
        return body
    return None


def child_blocks(body: str) -> list[tuple[str, str]]:
    """直下の子ノードを (名前, 中身) のリストで返す。"""
    result: list[tuple[str, str]] = []
    index = 0
    pattern = re.compile(r"(?:([A-Za-z_][\w-]*)\s*:\s*)?([A-Za-z_][\w-]*)\s*\{")
    while index < len(body):
        match = pattern.search(body, index)
        if not match:
            break
        inner, end = block_body(body, match.end() - 1)
        result.append((match.group(2), inner))
        index = end + 1
    return result


def first_property(body: str, prop: str) -> str | None:
    """`prop = < ... >;` の < > の中身を返す。"""
    match = re.search(rf"\b{re.escape(prop)}\s*=\s*<(.*?)>\s*;", body, flags=re.S)
    return match.group(1) if match else None


def check_keymap() -> None:
    if not KEYMAP_PATH.exists():
        errors.append(f"{KEYMAP_PATH} が見つかりません")
        return

    raw = KEYMAP_PATH.read_text(encoding="utf-8")
    text = strip_comments(raw)

    keymap_body = find_named_block(text, "keymap")
    if keymap_body is None:
        errors.append("keymap ノードが見つかりません")
        return

    layers = child_blocks(keymap_body)
    if not layers:
        errors.append("レイヤーが 1 つも見つかりません")
        return

    print(f"レイヤー数: {len(layers)}")

    # 1. 各レイヤーのキー数
    for index, (name, body) in enumerate(layers):
        bindings = first_property(body, "bindings")
        if bindings is None:
            errors.append(f"レイヤー {index} ({name}): bindings が見つかりません")
            continue
        count = bindings.count("&")
        status = "OK" if count == EXPECTED_KEY_COUNT else "NG"
        print(f"  [{index}] {name:<14} {count:>3} キー  {status}")
        if count != EXPECTED_KEY_COUNT:
            errors.append(
                f"レイヤー {index} ({name}): キー数が {count} 個。"
                f"{EXPECTED_KEY_COUNT} 個である必要があります"
            )

    layer_count = len(layers)

    # 2. レイヤー参照が範囲内か（keymap 全体を対象にする）
    for behavior in LAYER_ARG_BEHAVIORS:
        for match in re.finditer(rf"&{behavior}\s+(\d+)", keymap_body):
            target = int(match.group(1))
            if target >= layer_count:
                errors.append(
                    f"&{behavior} {target}: レイヤー {target} は存在しません"
                    f"（定義済みは 0〜{layer_count - 1}）"
                )

    # 3. combos の key-positions が範囲内か
    combos_body = find_named_block(text, "combos")
    if combos_body:
        for name, body in child_blocks(combos_body):
            positions_raw = first_property(body, "key-positions")
            if positions_raw is None:
                errors.append(f"combo {name}: key-positions が見つかりません")
                continue
            positions = [int(p) for p in re.findall(r"\d+", positions_raw)]
            if len(positions) < 2:
                errors.append(f"combo {name}: key-positions が 2 個未満です")
            out_of_range = [p for p in positions if p >= EXPECTED_KEY_COUNT]
            if out_of_range:
                errors.append(
                    f"combo {name}: キー位置 {out_of_range} が範囲外です"
                    f"（0〜{EXPECTED_KEY_COUNT - 1}）"
                )
            if first_property(body, "bindings") is None:
                errors.append(f"combo {name}: bindings が見つかりません")
            print(f"  combo {name:<12} 位置 {positions}")

    # 4. DYA Studio / ZMK Studio で編集するには &studio_unlock が必要
    if "&studio_unlock" not in text:
        warnings.append(
            "&studio_unlock がキーマップにありません。"
            "DYA Studio から設定を書き換えられなくなります"
        )


def check_dtsi() -> None:
    if not DTSI_PATH.exists():
        errors.append(f"{DTSI_PATH} が見つかりません")
        return

    text = strip_comments(DTSI_PATH.read_text(encoding="utf-8"))

    physical_keys = len(re.findall(r"&key_physical_attrs", text))
    print(f"physical layout のキー数: {physical_keys}")
    if physical_keys != EXPECTED_KEY_COUNT:
        errors.append(
            f"physical layout のキー数が {physical_keys} 個。"
            f"{EXPECTED_KEY_COUNT} 個である必要があります"
        )

    transform_body = find_named_block(text, "default_transform")
    if transform_body is None:
        errors.append("default_transform ノードが見つかりません")
        return

    mapping = first_property(transform_body, "map")
    if mapping is None:
        errors.append("default_transform の map が見つかりません")
        return

    positions = len(re.findall(r"RC\(", mapping))
    print(f"matrix transform のキー数: {positions}")
    if positions != EXPECTED_KEY_COUNT:
        errors.append(
            f"matrix transform のキー数が {positions} 個。"
            f"{EXPECTED_KEY_COUNT} 個である必要があります"
        )


def main() -> int:
    print(f"検証対象: {KEYMAP_PATH.relative_to(REPO_ROOT)}")
    check_keymap()
    print()
    print(f"検証対象: {DTSI_PATH.relative_to(REPO_ROOT)}")
    check_dtsi()
    print()

    for warning in warnings:
        print(f"WARN: {warning}")
    for error in errors:
        print(f"ERROR: {error}")

    if errors:
        print(f"\nFAIL: {len(errors)} 件のエラー")
        return 1

    print("PASS: すべてのチェックを通過しました"
          + (f"（警告 {len(warnings)} 件）" if warnings else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
