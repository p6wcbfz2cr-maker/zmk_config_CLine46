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

| タブ | 見込み | 根拠（west.yml のモジュール / R.conf の CONFIG） |
|---|---|---|
| Keymap | ○ | `zmk-feature-fast-keymap`, `zmk-feature-module-physical-layout` |
| Keymap の押下キー可視化 | ○ | `zmk-feature-input-stream` |
| Macro | ○ | `zmk-feature-runtime-macro` |
| Combo | ○ | `zmk-feature-runtime-combo` |
| Trackball（感度・回転・スクロール・一時レイヤー） | ○ | `zmk-module-runtime-input-processor` |
| Trackball（PMW3610 の省電力など詳細設定） | △ | ドライバが `badjeff/zmk-pmw3610-driver`。cormoran の `zmk-driver-pmw3610-with-custom-studio-rpc` ではないため出ない可能性が高い |
| Connection（BLE プロファイル） | ○ | `zmk-module-ble-management` |
| Connection（接続先別デフォルトレイヤー） | ○ | `zmk-feature-default-layer` |
| Connection（OS 自動検出と OS 別レイヤー） | × | `zmk-feature-os-detection` が west.yml に無い |
| Settings（idle / sleep） | ○ | `zmk-module-settings-rpc` |
| Settings（詳細設定） | ○ | `CONFIG_ZMK_CUSTOM_SETTINGS=y`（`runtime-macro` / `runtime-combo` の `import: true` 経由で取り込まれる） |
| Troubleshooting（Device Info） | ○ | `zmk-feature-device-info` |
| Troubleshooting（Watchdog: 再起動原因） | ○ | `zmk-feature-watchdog` |
| Troubleshooting（KSCAN 診断） | ○ | `zmk-feature-kscan-diagnostics` |
| バッテリー履歴 | × | `CONFIG_ZMK_BATTERY_HISTORY` はコメントアウト（保存が遅い問題のため上流で無効化中） |

> 実機で確認したら、この表の「見込み」を実測値に置き換える。

## うまくいかないとき

| 症状 | 確認すること |
|---|---|
| そもそも接続できない | 右手側を USB で繋いでいるか / `build.yaml` の `snippet: studio-rpc-usb-uart` / `CONFIG_ZMK_STUDIO=y` / Chrome か Edge か |
| Keymap は見えるが変更できない | Studio Unlock したか（`MO(3)` + 右親指 ENTER 位置） |
| 期待したタブが「未対応です」になる | `config/west.yml` に該当モジュールがあるか、`CLine46_R.conf` に `*_STUDIO_RPC=y` があるか |
| フリーズや勝手に再起動する | スタック不足の可能性。`CLine46_R.conf` の `CONFIG_ZMK_STUDIO_RPC_THREAD_STACK_SIZE` / `CONFIG_SYSTEM_WORKQUEUE_STACK_SIZE` などを確認。Troubleshooting タブの Watchdog に再起動原因が残る |
| キー位置がずれる | `CLine46.dtsi` の physical layout と `default_transform`、`python3 tools/check_keymap.py` |

## 設定ファイルとの関係（重要）

- DYA Studio で変えた内容は**キーボード本体のフラッシュ**に保存される。
  `config/CLine46.keymap` は**書き換わらない**。
- ファームウェアを書き直したり `settings_reset.uf2` を流すと、Studio で入れた変更は消える。
- 恒久的に残したい変更は、`config/CLine46.keymap` にも反映してコミットする。
- Import/Export タブから [Keyboard Abyss](https://abyss.keyboard-hub.com/) にバックアップ・
  共有できる。ファームウェア更新の前にはここでバックアップを取っておく。
