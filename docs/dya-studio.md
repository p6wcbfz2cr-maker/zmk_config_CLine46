# DYA Studio で CLine46 を設定する

DYA Studio はブラウザから ZMK キーボードを設定する Web アプリ。ファームウェアを
ビルドし直さずに、キーマップ・マクロ・コンボ・トラックボール・接続先・スリープ設定などを
変更できる。

- 本体: https://studio.dya.cormoran.works/
- 紹介記事: https://note.com/cormoran/n/ncd20ee4c1213
- 開発者ガイド: https://studio.dya.cormoran.works/developer-guide

## 接続手順

1. **Chrome / Edge** で https://studio.dya.cormoran.works/ を開く（Web Serial が必要）
2. **右手側（central）** を USB-C で PC に接続する
   - 左手側では接続できない。USB Serial は右手側にしか出ていない（`build.yaml` の
     `snippet: studio-rpc-usb-uart` が右手側だけに付いている）
3. 「USBで接続」を選び、表示されたシリアルポートを許可する
4. **Studio Unlock**: `MO(3)`（右手最下段、`.` の右隣）を押しながら、
   **右親指の ENTER 位置**を押す（キー位置 42 の `&studio_unlock`）
   - Unlock しないと閲覧はできても書き換えができない
5. 変更後は画面の保存操作でキーボード本体のフラッシュに保存される

実機がなくても「デモモードを試す」で画面を確認できる。

## タブ別の対応状況

対応は「対応モジュールが west.yml にある」ことと「`*_STUDIO_RPC=y` が
`boards/shields/CLine46/CLine46_R.conf` にある」ことの両方で決まる。

### main ブランチ（ZMK v0.3 系 / `cormoran/zmk@v0.3-branch+dya`）

| タブ | 対応 | 根拠 |
|---|---|---|
| Keymap（キー割り当て・レイヤー名・レイアウト） | ○ | `CONFIG_ZMK_STUDIO=y` |
| Macro & Combo | × | モジュール無し |
| Trackball（感度・回転・スクロール化・一時レイヤー） | ○ | `zmk-module-runtime-input-processor` |
| Connection（BLE プロファイル） | ○ | `zmk-module-ble-management` |
| Connection（OS 別レイヤー自動切替） | × | モジュール無し |
| Settings（idle / sleep） | ○ | `zmk-module-settings-rpc` |
| Troubleshooting（Device Info / Watchdog / KSCAN） | × | モジュール無し |
| バッテリー履歴 | × | `CONFIG_ZMK_BATTERY_HISTORY=n` |

### feature/dya-studio ブランチ（ZMK main+dya / 4.1 系）

上流 `takamaru-fpv/zmk_config_CLine46` の `zmk4.1対応` ブランチを取り込んだもの。
**取り込み時点の上流 commit: `a19f381`（2026-08-15「トラボのパラメータ調整」）**

実機で確認済み（Troubleshooting → Device Info の表示が `config/west.yml` のピンと一致）:

| Device Info の表示 | west.yml のピン |
|---|---|
| ZMK `E5C9B691` | `zmk` = `e5c9b6915b56801193e359dd9bad4a167ce0d1b8`（`main+dya`） |
| モジュール `8CEDD2D` | `zmk-feature-device-info` = `8cedd2dd9f04e19ea5a17b94914dd47a09d8db11` |
| Zephyr `4.1.0` | `cormoran/zephyr@v4.1.0+zmk-fixes` |

凡例: ◎ = 実機で確認済み / ○ = 対応しているはず / △ = 出ない可能性 / × = 非対応

| タブ | 状況 | 根拠（west.yml のモジュール / R.conf の CONFIG） |
|---|---|---|
| Keymap | ○ | `zmk-feature-fast-keymap`, `zmk-feature-module-physical-layout` |
| Keymap の押下キー可視化 | ○ | `zmk-feature-input-stream` |
| Macro | ◎ | `zmk-feature-runtime-macro` |
| Combo | ◎ | `zmk-feature-runtime-combo` |
| Trackball（感度・回転・スクロール・一時レイヤー） | ○ | `zmk-module-runtime-input-processor` |
| Trackball（PMW3610 の省電力など詳細設定） | △ | ドライバが `badjeff/zmk-pmw3610-driver`。cormoran の `zmk-driver-pmw3610-with-custom-studio-rpc` ではないため出ない可能性が高い |
| Connection（BLE プロファイル） | ○ | `zmk-module-ble-management` |
| Connection（接続先別デフォルトレイヤー） | ○ | `zmk-feature-default-layer` |
| Connection（OS 自動検出） | ◎ | `zmk-feature-os-detection`（`3052679f`）+ `CONFIG_ZMK_OS_DETECTION_*` |
| Connection（OS 別レイヤー自動切替） | × | `CONFIG_ZMK_OS_DETECTION_LAYER_AUTO_SWITCH` を有効にしていない |
| Settings（idle / sleep） | ○ | `zmk-module-settings-rpc` |
| Settings（詳細設定） | ○ | `CONFIG_ZMK_CUSTOM_SETTINGS=y`（`runtime-macro` / `runtime-combo` の `import: true` 経由で取り込まれる） |
| Troubleshooting（Device Info） | ◎ | `zmk-feature-device-info` |
| Troubleshooting（Watchdog: 再起動原因） | ○ | `zmk-feature-watchdog` |
| Troubleshooting（KSCAN 診断） | ○ | `zmk-feature-kscan-diagnostics` |
| バッテリー履歴 | × | `CONFIG_ZMK_BATTERY_HISTORY` はコメントアウト（保存が遅い問題のため上流で無効化中） |

> 残りのタブを確認したら ○ を ◎ に更新する。

## OS 自動検出

`cormoran/zmk-feature-os-detection` により、つないでいるホストの OS を判定して
Connection タブに表示する。判定は **USB の列挙パターン**（`usb_handle_bos` をリンカで
ラップして GET_DESCRIPTOR の並びを観測）と **BLE の GATT 読み取りパターン**
（HID Report Map / HID Info / DIS PnP ID / GAP Appearance を読む順序、MTU、接続間隔）の 2 経路。

- **central（右手側）でのみ動作する。** 設定は `CLine46_R.conf` にのみ置く。
  左手側のキーも右手側を経由してホストへ送られるため、R だけで左右ともに同じ判定が適用される
- iPad / iPhone を macOS と区別するため `CONFIG_ZMK_OS_DETECTION_BLE_GATT_CLIENT_PROBE=y`
  を有効にしている（ペアリング後に ANCS/AMS をクライアントとして探索する opt-in 機能）

### 判別の限界（README 記載）

| 組み合わせ | 状況 |
|---|---|
| USB での macOS と iOS | **区別できない**（同一の列挙パターン） |
| BLE での Windows と Linux | 確実には区別できない |
| USB での Android と Linux | 列挙パターンが同じ |

判定を間違えたときは Studio から **BLE プロファイルごとに手動で上書き**できる
（上書きはフラッシュに保存され、再接続後も保持される）。

### OS 別レイヤー自動切替について

このモジュールには「検出した OS に応じてレイヤーを自動で有効化する」機能もあるが、
**現在は無効にしている**（`CONFIG_ZMK_OS_DETECTION_LAYER_AUTO_SWITCH` を書いていない）。

有効にする場合、OS → レイヤー番号の対応は **ビルド時の Kconfig 固定**で、
Studio からは変更できない。実行時に変えられるのは検出結果の表示と手動上書きだけ。

```
CONFIG_ZMK_OS_DETECTION_LAYER_AUTO_SWITCH=y
CONFIG_ZMK_OS_DETECTION_LAYER_MACOS=5      # -1 は無効
CONFIG_ZMK_OS_DETECTION_LAYER_WINDOWS=6
```

割り当て先の候補は空きレイヤーの `layer_5`(5) / `layer_6`(6)。

## うまくいかないとき

| 症状 | 確認すること |
|---|---|
| そもそも接続できない | 右手側を USB で繋いでいるか / `build.yaml` の `snippet: studio-rpc-usb-uart` / `CONFIG_ZMK_STUDIO=y` / Chrome か Edge か |
| Keymap は見えるが変更できない | Studio Unlock したか（`MO(3)` + 右親指 ENTER 位置） |
| 期待したタブが「未対応です」になる | `config/west.yml` に該当モジュールがあるか、`CLine46_R.conf` に `*_STUDIO_RPC=y` があるか |
| フリーズや勝手に再起動する | スタック不足の可能性。`CLine46_R.conf` の `CONFIG_ZMK_STUDIO_RPC_THREAD_STACK_SIZE` / `CONFIG_SYSTEM_WORKQUEUE_STACK_SIZE` などを確認。Troubleshooting タブの Watchdog に再起動原因が残る |
| キー位置がずれる | `CLine46.dtsi` の physical layout と `default_transform`、`python3 tools/check_keymap.py` |
| OS の判定がおかしい | 「判別の限界」を確認したうえで、Connection タブから手動で上書きする。USB は 200ms、BLE は 1000ms のデバウンス後に確定するので、つないだ直後は `Unknown` のことがある |
| OS 自動検出を入れてから BLE が不安定 | `CONFIG_ZMK_OS_DETECTION_BLE_GATT_CLIENT_PROBE=n` にして切り分ける。それでも駄目なら `CONFIG_ZMK_OS_DETECTION_BLE=n`（`BT_GATT_AUTHORIZATION_CUSTOM` を select しなくなる） |
| 周辺側タブが `Peripheral did not respond (timed out after 3000ms)` | `CLine46_L.conf` に `CONFIG_ZMK_SPLIT_RELAY_EVENT=y` と `CONFIG_ZMK_WATCHDOG=y` があるか。前者が無いと relay 用のキャラクタリスティックを公開せず、後者が無いと中継されてきた要求に答える相手がいない（`ZMK_WATCHDOG_SPLIT_RELAY` は `if ZMK_WATCHDOG` の中にある）|
| 周辺側タブを開くと Studio が切断される | 中央側が落ちている。`CLine46_L.conf` の `CONFIG_ZMK_LOW_PRIORITY_THREAD_STACK_SIZE` / `CONFIG_SYSTEM_WORKQUEUE_STACK_SIZE` を R 側と同じ 4096 にする。peripheral も応答を nanopb で組み立てるため、既定のスタックでは足りない |
| 左右が繋がらない / BLE が不安定（4.1 系） | `CONFIG_BT_CTLR_ASSERT_OVERHEAD_START=n` が左右に入っているか。詳細は `docs/build-and-flash.md` の「3.5」 |

## 設定ファイルとの関係（重要）

- DYA Studio で変えた内容は**キーボード本体のフラッシュ**に保存される。
  `config/CLine46.keymap` は**書き換わらない**。
- ファームウェアを書き直したり `settings_reset.uf2` を流すと、Studio で入れた変更は消える。
- 恒久的に残したい変更は、`config/CLine46.keymap` にも反映してコミットする。
- Import/Export タブから [Keyboard Abyss](https://abyss.keyboard-hub.com/) にバックアップ・
  共有できる。ファームウェア更新の前にはここでバックアップを取っておく。
