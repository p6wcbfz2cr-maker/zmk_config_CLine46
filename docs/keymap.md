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

| index | ノード名 (display-name) | 役割 | 入り方 |
|---|---|---|---|
| 0 | `0_base_mac` | 通常入力（常時有効な土台レイヤー。Mac向けのIMEキー・修飾キー配置） | ― |
| 1 | `1_base_win` | Windows検出時の差分オーバーレイ。**現状すべて `&trans`**（Mac版との差分は未設定） | OS自動判定で自動有効化（手動での入り方はなし） |
| 2 | `2_number` | 数字・記号 | キー位置39 `&lt 2 LANG2` を長押し |
| 3 | `3_function` | Fキー・矢印・Home/End/PageUp/Down・コピペショートカット(Cmd) | キー位置43 `&lt 3 SPACE` を長押し |
| 4 | `4_func_win` | `3_function` のWindows差分用に予約。**現状すべて `&trans`**、到達手段なし | ―（未配線） |
| 5 | `5_mouse` | マウスボタン(MB1/MB3/MB2)用に予約。ほぼ `&trans`、到達手段なし | ―（未配線） |
| 6 | `6_ble` | Bluetooth設定 + Studio Unlock + トラックボールのスクロール化 | キー位置22 `&lt 6 SEMICOLON` を長押し |

トラックボールは通常はポインター移動、**レイヤー 6 (`6_ble`) に入っている間だけスクロール**になる
（`CLine46_R.overlay` の `scroller { layers = <6>; }`）。

### OS自動判定によるレイヤー自動切替

`zmk-feature-os-detection`（`CONFIG_ZMK_OS_DETECTION_LAYER_AUTO_SWITCH`、`CLine46_R.conf`）により、
接続先ホストのOSに応じて `1_base_win` が自動でオン/オフされる。

- macOS / iOS 検出時: 追加のレイヤーは有効化されない（`0_base_mac` が常時有効な土台のため、そのまま使われる）
- Windows 検出時: `1_base_win`（index 1）がオーバーレイとして自動有効化される
  （`CONFIG_ZMK_OS_DETECTION_LAYER_WINDOWS=1`）
- `1_base_win` は現状すべて `&trans` のため、切り替わっても見た目上のキー入力に変化はない
  （DYA StudioのKeymapタブでレイヤーが光ることでのみ確認できる）。差分を入れたい場合はこのレイヤーの
  該当キーだけ書き換える。

詳細は [`docs/dya-studio.md`](dya-studio.md) の「OS 自動検出」を参照。

## レイヤー 0: 0_base_mac

```
 TAB    Q     W     E     R     T   │   Y     U     I     O     P     [
 CTRL   A     S     D     F     G   │   H     J     K     L    LT6    ]
 SHIFT  Z     X     C     V     B   │   N     M     ,     .     /   RALT
       CTRL   GUI   ALT   LT2   SFT   SFT │ ENT   LT3          ESC   ENT
```

最下段・row2右端の複合キー:

| キー位置 | behavior | 長押し | 単押し |
|---|---|---|---|
| 22 | `&lt 6 SEMICOLON` | レイヤー 6 (`6_ble`) | `;` |
| 39 | `&lt 2 LANG2` | レイヤー 2 (`2_number`) | LANG2（英数） |
| 40 | `&mt LEFT_SHIFT SPACE` | 左シフト | スペース |
| 41 | `&mt LEFT_SHIFT LANG1` | 左シフト | LANG1（かな） |
| 43 | `&lt 3 SPACE` | レイヤー 3 (`3_function`) | スペース |

`&mt` の設定はキーマップ先頭で `flavor = "balanced"` / `quick-tap-ms = <0>`。

## レイヤー 1: 1_base_win

Windows検出時だけ `0_base_mac` の上にオーバーレイとして自動有効化されるレイヤー。
**現状すべて `&trans`**（46キー全て透過、Macとの差分は未設定）。手動で入る手段は用意していない
（OS自動判定専用）。

## レイヤー 2: 2_number（数字・記号）

```
  ^     =     7     8     9     @   │   (     "     )     ;     !     \
  ―     +     4     5     6     #   │   {     -     }     :     &     |
  ―     *     1     2     3     _   │   <     _     >     /     $     %
       ESC    0     ―     ―     ―    ― │ ENT   ―           ?     ―
```

`―` は `&trans`（下位レイヤーの割り当てが透過する）。

## レイヤー 3: 3_function

```
  ―     ―    F7    F8    F9   F10   │   ―   HOME   ↑    END  PGUP    ―
  ―     ―    F4    F5    F6   F11   │ BSPC   ←     ↓     →  PGDN    ―
  ―     ―    F1    F2    F3   F12   │  G-A   G-X   G-C   G-V   ―     ―
        ―     ―     ―     ―     ―    ― │  ―     ―           ―     ―
```

`G-` は `LG()`（Cmd/GUI修飾）。行3右側は Cmd+A(全選択) / Cmd+X(切り取り) / Cmd+C(コピー) /
Cmd+V(貼り付け) という Mac 向けショートカット。Windows接続時にCtrl系へ切り替えたい場合は、
`4_func_win`（現状未配線・全`&trans`）に差分を書いて到達手段を用意する必要がある（今回は未対応）。

## レイヤー 4: 4_func_win

`3_function` のWindows差分を書き込むために予約されたレイヤー。**現状すべて `&trans`**。
**到達手段が定義されていない**（`&lt 4` / `&mo 4` / `&to 4` がキーマップ内に存在しない）。

## レイヤー 5: 5_mouse

マウスボタン用に予約されたレイヤー。row2 に `MB1`(左クリック) / `MB3`(中クリック) / `MB2`(右クリック)
のみ配置済みで、他は全て `&trans`。**到達手段が定義されていない**（`&lt 5` / `&mo 5` / `&to 5` が
キーマップ内に存在しない）。

## レイヤー 6: 6_ble（Bluetooth + Studio Unlock）

```
BT_CLR    ―     ―      ―      ―     ―  │   ―     ―     ―     ―     ―     ―
BT_CLR_ALL ―  BT_SEL4   ―      ―     ―  │   ―     ―     ―     ―     ―     ―
  ―       ―   BT_SEL1 BT_SEL2 BT_SEL3 ― │   ―     ―     ―     ―     ―     ―
          ―  BT_SEL0   ―      ―     ―   ― │ STUDIO_UNLOCK  ―        ―     ―
```

- **`&studio_unlock` は右親指の ENTER 位置（キー位置 42）**。`0_base_mac` のキー位置22
  （row2、`L` の右隣）にある `&lt 6 SEMICOLON` を押しながらここを押すと、DYA Studio / ZMK Studio
  からの書き換えが解除される。
- BT_SEL は 0〜4 の 5 プロファイル。`BT_CLR` は現在のプロファイルのペアリング削除、
  `BT_CLR_ALL` は全消去。

## コンボ

| 名前 | キー位置 | 出力 |
|---|---|---|
| `tab` | 11, 12 | TAB |
| `shift_tab` | 12, 13 | Shift + TAB |

キー位置 11 は右手上段の `[`、12 は左手中段の `CTRL`、13 は `A`（レイヤー再編後も物理的な
キー配置は変わっていないため、この対応は従来通り）。**左右にまたがる組み合わせ**になっているため、
意図通りか要確認（`[` + `CTRL` / `CTRL` + `A`）。

## マクロ / behavior

| 名前 | 内容 |
|---|---|
| `to_layer_0` | レイヤー 0 に戻してから引数のキーを送るマクロ（1 引数） |
| `lt_to_layer_0` | 長押しで `&mo`、単押しで `to_layer_0` を実行する hold-tap（tapping-term 200ms） |

いずれも**現在どのレイヤーからも使われていない**（定義のみ）。`&to 0` は改名後も引き続き
`0_base_mac` を指すため、参照先としては問題ない。

## 要確認事項

現行キーマップを読んで気付いた点。意図的ならこのセクションを消してよい。

1. コンボ `tab` / `shift_tab` のキー位置が左右にまたがる（上記）。
2. `to_layer_0` / `lt_to_layer_0` が未使用。
3. `4_func_win` / `5_mouse` は到達手段がなく、中身もほぼ未着手（意図的な予約レイヤーと思われる）。
4. `3_function` のコピペショートカットはCmd固定（Mac向け）。Windows接続時の差分は
   `4_func_win` に未実装。

## 編集後にすること

```bash
python3 tools/check_keymap.py
```

キー数（全レイヤー 46）、レイヤー参照の範囲、コンボのキー位置、`&studio_unlock` の有無、
physical layout と matrix transform のキー数一致を検証する。
