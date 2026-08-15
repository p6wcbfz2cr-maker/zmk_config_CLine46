# CLine46 キーマップ現状

定義元: `config/CLine46.keymap`（このドキュメントは手動で同期する）

## 物理レイアウトとキー位置

46 キー（左右分割 / 上 3 段は片手 6 キー、最下段は左 6 + 右 4）。
キー位置番号は `combos` の `key-positions` や ZMK Studio の並びと同じ。

```
  0   1   2   3   4   5  │   6   7   8   9  10  11
 12  13  14  15  16  17  │  18  19  20  21  22  23
 24  25  26  27  28  29  │  30  31  32  33  34  35
     36  37  38  39  40  41  │  42  43      44  45
```

- physical layout の定義: `boards/shields/CLine46/CLine46.dtsi` の `cline46_physical_layout`
- 行列との対応: 同ファイルの `default_transform`（charlieplex kscan、12 列 × 4 行）
- 右手側は `CLine46_R.overlay` で `col-offset = <6>` が入る

## レイヤー一覧

| index | 名前 | 役割 | 入り方 |
|---|---|---|---|
| 0 | `default_layer` | 通常入力 | ― |
| 1 | `layer_1` | 数字・記号 | 左親指 `LT1/SPACE` を長押し |
| 2 | `MOUSE` | F キー・矢印・コピペ・マウスボタン | 左親指 `LT2/無変換` を長押し |
| 3 | `SCROLL` | Bluetooth 設定 + Studio Unlock + トラックボールのスクロール化 | 右手最下段の `MO(3)` を長押し |
| 4 | `layer_4` | Bluetooth 設定（`SCROLL` とほぼ同じ内容、到達手段なし） | ― |
| 5 | `layer_5` | 空き（全 `&trans`） | ― |
| 6 | `layer_6` | 空き（全 `&trans`） | ― |

トラックボールは通常はポインター移動、**レイヤー 3 に入っている間だけスクロール**になる
（`CLine46_R.overlay` の `scroller { layers = <3>; }`）。

## レイヤー 0: default_layer

```
 TAB    Q     W     E     R     T   │   Y     U     I     O     P     [
 CTRL   A     S     D     F     G   │   H     J     K     L     -     ]
 SHIFT  Z     X     C     V     B   │   N     M     ,     .   MO(3) RSHIFT
       ESC   GUI   ALT   LT2   LT1   SFT │ ENT  BSPC          9    DEL
                        無変換  SPACE 変換
```

最下段の複合キー:

| キー | 長押し | 単押し |
|---|---|---|
| `&lt 2 INT_MUHENKAN` | レイヤー 2 (MOUSE) | 無変換 |
| `&lt 1 SPACE` | レイヤー 1 | スペース |
| `&mt LSFT INT_HENKAN` | 左シフト | 変換 |

`&mt` の設定はキーマップ先頭で `flavor = "balanced"` / `quick-tap-ms = <0>`。

## レイヤー 1: 数字・記号

```
  ^     =     7     8     9     @   │   (     "     )     ;     !     ?
  -     +     4     5     6     #   │   [     '     ]     :     &     |
  /     *     1     2     3     _   │   /     \     ,     .     $     %
       ESC    0     .     ―     ―    ― │ ENT  BSPC         DEL    ―
```

`―` は `&trans`（下位レイヤーの割り当てが透過する）。

## レイヤー 2: MOUSE

```
  ―     ―    F7    F8    F9   F10   │  C-Y   C-C   C-V   C-X   C-P    ―
  ―     ―    F4    F5    F6   F11   │  C-Z   左ｸﾘｯｸ  ↑   右ｸﾘｯｸ C-F    ―
  ―     ―    F1    F2    F3   F12   │  C-A    ←     ↓     →     ―     ―
        ―     ―     ―     ―     ―   │ ENT   BSPC        HOME   END
```

## レイヤー 3: SCROLL（Bluetooth + Studio Unlock）

```
BT_CLR    ―     ―      ―      ―     ―  │   ―     ―     ―     ―     ―     ―
BT_CLR_ALL ―  BT_SEL4   ―      ―     ―  │   ―     ―     ―     ―     ―     ―
  ―       ―   BT_SEL1 BT_SEL2 BT_SEL3 ― │   ―     ―     ―     ―     ―     ―
          ―  BT_SEL0   ―      ―     ―   ― │ STUDIO_UNLOCK  ―        ―     ―
```

- **`&studio_unlock` は右親指の ENTER 位置（キー位置 42）**。`MO(3)` を押しながらここを押すと
  DYA Studio / ZMK Studio からの書き換えが解除される。
- BT_SEL は 0〜4 の 5 プロファイル。`BT_CLR` は現在のプロファイルのペアリング削除、
  `BT_CLR_ALL` は全消去。

## レイヤー 4

`SCROLL` から `&studio_unlock` を除いた Bluetooth 設定のみ。**到達手段が定義されていない**
（`&mo 4` / `&to 4` がキーマップ内に存在しない）。

## レイヤー 5 / 6

全キー `&trans` の空きレイヤー。

## コンボ

| 名前 | キー位置 | 出力 |
|---|---|---|
| `tab` | 11, 12 | TAB |
| `shift_tab` | 12, 13 | Shift + TAB |

キー位置 11 は右手上段の `[`、12 は左手中段の `CTRL`、13 は `A`。**左右にまたがる組み合わせ**
になっているため、意図通りか要確認（`[` + `CTRL` / `CTRL` + `A`）。

## マクロ / behavior

| 名前 | 内容 |
|---|---|
| `to_layer_0` | レイヤー 0 に戻してから引数のキーを送るマクロ（1 引数） |
| `lt_to_layer_0` | 長押しで `&mo`、単押しで `to_layer_0` を実行する hold-tap（tapping-term 200ms） |

いずれも**現在どのレイヤーからも使われていない**（定義のみ）。

## 要確認事項

現行キーマップを読んで気付いた点。意図的ならこのセクションを消してよい。

1. `default_layer` のキー位置 44（右親指 BSPC の隣）が `&kp NUMBER_9`。他の記号・数字は
   レイヤー 1 に集約されているため浮いている。
2. コンボ `tab` / `shift_tab` のキー位置が左右にまたがる（上記）。
3. レイヤー名 `MOUSE`(2) / `SCROLL`(3) と中身が一致していない。2 は F キーと矢印が主体、
   3 は Bluetooth 設定。**この名前は DYA Studio の画面にもそのまま表示される**。
4. レイヤー 4 は到達手段がなく、レイヤー 3 とほぼ重複。
5. `to_layer_0` / `lt_to_layer_0` が未使用。

## 編集後にすること

```bash
python3 tools/check_keymap.py
```

キー数（全レイヤー 46）、レイヤー参照の範囲、コンボのキー位置、`&studio_unlock` の有無、
physical layout と matrix transform のキー数一致を検証する。
