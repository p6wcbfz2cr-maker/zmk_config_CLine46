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
| `boards/shields/CLine46/CLine46_L.conf` | 左 = peripheral。電源・バッテリー設定のみ |
| `boards/shields/CLine46/CLine46_R.overlay` | SPI とトラックボール、input processor |
| `boards/shields/CLine46/Kconfig.defconfig` | シールド既定値 |
| `build.yaml` | GitHub Actions のビルド対象 |
| `firmware/` | ビルド済み uf2 の保管場所 |
| `docs/`, `tools/` | このプロジェクトで追加した資料と検証スクリプト（上流には無い） |

## 守るべき不変条件

- **全レイヤーが 46 キー**（12 / 12 / 12 / 10）。1 つでも欠けるとビルドは通っても配列がずれる。
- レイヤー index: `default_layer`=0, `layer_1`=1, `MOUSE`=2, `SCROLL`=3, `layer_4`=4, `layer_5`=5, `layer_6`=6。
  順番を変えると `&mo` / `&lt` の参照と `CLine46_R.overlay` の `scroller { layers = <3>; }` が壊れる。
- `&studio_unlock` を消さない（消すと DYA Studio から書き換えられなくなる）。
- DYA Studio 関連の `CONFIG_*_STUDIO_RPC` は **R 側（central）** に置く。
- `config/west.yml` のモジュールは commit / タグでピンする（`main` 追従にしない）。

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
- **Studio Unlock**: `MO(3)`（右手最下段、`.` の右隣）+ 右親指の ENTER 位置
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
