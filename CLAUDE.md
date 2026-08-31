# CLine46 ZMK 設定リポジトリ

自作分割キーボード **CLine46**（46 キー / Seeed XIAO nRF52840 / 右手側に PMW3610 トラックボール）の
ZMK 設定。ブラウザから設定を動的に変更する **DYA Studio** に対応させることを主目的にしている。

## リポジトリの関係

| リモート | 用途 |
|---|---|
| `origin` = `p6wcbfz2cr-maker/zmk_config_CLine46` | 自分のフォーク。ここでビルドする |
| `upstream` = `takamaru-fpv/zmk_config_CLine46` | キーボード作者。設計変更はここが起点 |

- 上流に **`zmk4.1対応`** ブランチがあり、ZMK `main+dya` + DYA Studio 全機能モジュール構成に
  移行済み（現在も更新中の WIP）。取り込みは `git fetch upstream` してから差分を確認する。
- 作業は `feature/*` ブランチで行い、実機確認が取れてから `main` にマージする。

## ファイル構成

| パス | 役割 |
|---|---|
| `config/CLine46.keymap` | キーマップ本体（レイヤー、コンボ、マクロ、behavior） |
| `config/west.yml` | ZMK 本体と依存モジュールのバージョン |
| `boards/shields/CLine46/CLine46.dtsi` | physical layout / matrix transform / kscan（左右共通） |
| `boards/shields/CLine46/CLine46_R.conf` | **右 = central**。Studio と DYA 機能の設定はここ |
| `boards/shields/CLine46/CLine46_L.conf` | 左 = peripheral。電源・バッテリーに加え、split relay と周辺側 Studio 用の設定 |
| `boards/shields/CLine46/CLine46_R.overlay` | SPI とトラックボール、input processor |
| `boards/shields/CLine46/Kconfig.defconfig` | シールド既定値 |
| `build.yaml` | GitHub Actions のビルド対象 |
| `firmware/` | ビルド済み uf2 の保管場所 |
| `docs/`, `tools/` | このプロジェクトで追加した資料と検証スクリプト（上流には無い） |

## 守るべき不変条件

- **全レイヤーが 46 キー**（12 / 12 / 12 / 10）。1 つでも欠けるとビルドは通っても配列がずれる。
- レイヤー index: `0_base_mac`=0, `1_base_win`=1, `2_number`=2, `3_function`=3, `4_func_win`=4,
  `5_mouse`=5, `6_ble`=6。順番を変えると `&lt` の参照と `CLine46_R.overlay` の
  `scroller { layers = <6>; }` が壊れる。
- `0_base_mac`（index 0）は ZMK の仕様上無効化できない常時有効な土台レイヤー。`1_base_win`
  （index 1）は Windows 検出時だけ自動でオーバーレイ有効化される差分レイヤーで、
  `CLine46_R.conf` の `CONFIG_ZMK_OS_DETECTION_LAYER_AUTO_SWITCH` /
  `CONFIG_ZMK_OS_DETECTION_LAYER_WINDOWS=1` と対応している（`zmk-feature-os-detection`）。
  `4_func_win`・`5_mouse` は到達手段のない予約レイヤー。
- `&studio_unlock` を消さない（消すと DYA Studio から書き換えられなくなる）。
- DYA Studio 関連の `CONFIG_*_STUDIO_RPC` は **R 側（central）** に置く。ただし
  周辺側の情報を Studio から見る機能は、モジュール本体（`CONFIG_ZMK_WATCHDOG` など）と
  `CONFIG_ZMK_SPLIT_RELAY_EVENT`、スタック設定を **L 側にも**置く必要がある。
  詳細は `docs/dya-studio.md`。
- `CONFIG_BT_CTLR_ASSERT_OVERHEAD_START=n` を左右から消さない。ただし**この設定自体は
  実機に反映されておらず、y のままである**ことが判明している（原因不明、Kconfig 警告あり）。
  無線イベントの遅延で `k_oops()` に落ち再起動する既知の問題は未解決のまま残っており、
  `CONFIG_ZMK_WATCHDOG_FREEZE_MONITOR_LOWPRIO_QUEUE=n` 等の CPU 負荷軽減策で発生確率を
  下げているだけの状態（`docs/build-and-flash.md` の 3.5）。
- `config/west.yml` のモジュールは commit / タグでピンする（`main` 追従にしない）。
- トラックボールのドライバは `cormoran/zmk-driver-pmw3610-with-custom-studio-rpc`
  （devicetree の compatible は `cormoran,pmw3610`、CONFIG 接頭辞は `CONFIG_PMW3610_*`）。
  かつて使っていた `badjeff/zmk-pmw3610-driver`（`pixart,pmw3610-alt` /
  `CONFIG_PMW3610_ALT_*`）と**接頭辞も compatible も違う**ので混ぜない。差し替えたのは
  cpi・レストモードの各時間を DYA Studio から実行時に変更できるようにするため
  （`CONFIG_ZMK_PMW3610_CUSTOM_SETTINGS=y`）。詳細は `docs/dya-studio.md` の
  「PMW3610 の詳細設定」。
- トラックボールの X 軸反転は `CLine46_R.overlay` の `zip_xy_transform` 側だけで行う。
  センサー側（`CONFIG_PMW3610_INVERT_X` / Studio の `invert_x`）で重ねると二重反転になる。

## 編集後に必ず実行する

```bash
python3 tools/check_keymap.py
```

キー数・レイヤー参照・コンボ位置・`&studio_unlock` の有無・physical layout と
matrix transform の整合を検証する（ZMK ビルド環境は不要）。

## ファームウェアの書き込み

```bash
./tools/flash.sh reset|left|right
```

Finder のドラッグ&ドロップは macOS のメタデータが原因でエラー -36 / -50 になることが
あるため、このスクリプト（`cp -X`）を使う。詳細は `docs/build-and-flash.md`。

## DYA Studio

- 右手側を USB 接続 → https://studio.dya.cormoran.works/ を Chrome/Edge で開く
- **Studio Unlock**: `&lt 6 SEMICOLON`（右手 row2、`L` の右隣）長押し + 右親指の ENTER 位置
- **Studio での変更はキーボード本体に保存され、`config/CLine46.keymap` は書き換わらない。**
  恒久化したい変更はファイルにも反映してコミットする。ファーム更新前は Import/Export から
  Keyboard Abyss にバックアップする。

## ドキュメント

| ファイル | 内容 |
|---|---|
| `docs/keymap.md` | 現行キーマップの全レイヤー、キー位置番号、要確認事項 |
| `docs/dya-studio.md` | 接続手順、タブ別対応状況、トラブルシューティング |
| `docs/build-and-flash.md` | Actions でのビルド、uf2 書き込み、設定リセット手順 |

キーマップを変更したら `docs/keymap.md` も更新する（自動同期はされない）。
