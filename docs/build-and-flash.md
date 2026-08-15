# ビルドと書き込み手順

## 前提

| 項目 | 値 |
|---|---|
| MCU | Seeed Studio XIAO nRF52840 (BLE) |
| 中央 (central) | **右手側**。トラックボール搭載、USB で PC につないで DYA Studio と通信する |
| 周辺 (peripheral) | 左手側 |
| ビルド | GitHub Actions（ローカルに Zephyr 環境は不要） |

ビルド対象は `build.yaml` で定義。`settings_reset` は設定領域を消すためのユーティリティ
ファームウェアで、キーボードとしては動作しない。

## 0. ビルド不要の最短ルート

`feature/dya-studio` ブランチには上流がビルドした uf2 が
`firmware/20260816_zmk4.1_dya-studio/` に同梱されている。**この uf2 を追加したコミット
（`a19f381`）以降、`config/` `boards/` `build.yaml` は変更されていない**ため、
現在のブランチの設定内容とそのまま一致する。

キーマップや設定を自分で変える前に DYA Studio の動作だけ確認したい場合は、
ビルドを待たずに「3. 設定リセット」の手順でこの 3 ファイルを書き込めばよい。

## 1. ビルド（GitHub Actions）

1. ブランチを push する
   ```bash
   git push origin <ブランチ名>
   ```
2. `https://github.com/p6wcbfz2cr-maker/zmk_config_CLine46/actions` で実行を確認
3. 成功したら実行ページ下部の **Artifacts** から `firmware.zip` をダウンロードして展開

> **フォークでは Actions が既定で無効。** 実行履歴が空の場合は Actions タブを開き、
> 「I understand my workflows, go ahead and enable them」を一度クリックする。

含まれる uf2（`zmk4.1対応` 系の `build.yaml` は `artifact-name` を指定しているため短い名前）:

| ファイル | 書き込み先 |
|---|---|
| `CLine46_R.uf2` | 右手側 |
| `CLine46_L.uf2` | 左手側 |
| `settings_reset.uf2` | 左右どちらにも（設定リセット用） |

## 2. uf2 の書き込み

片側ずつ、USB-C で PC に接続して行う。

1. キーボードを USB で接続する
2. XIAO のリセットボタンを**素早く 2 回押す**（ダブルリセット）
3. `XIAO-SENSE` という USB ドライブがマウントされる
4. uf2 をそのドライブにドラッグ&ドロップでコピーする
5. コピー完了で自動的に再起動し、ドライブは消える

macOS では「ディスクの取り出しが正しく行われませんでした」という警告が出ることがあるが、
書き込み自体は完了しているので無視してよい。

## 3. 設定リセットが必要な場面

XIAO の内部フラッシュにはキーマップ変更・BLE ペアリング・DYA Studio で変更した設定が保存される。
以下の場合は `settings_reset.uf2` を**左右両方**に書き込んでから、通常のファームウェアを書き込む。

- ZMK のメジャーバージョンをまたぐ更新（例: v0.3 系 → main / 4.1 系）
- 左右が繋がらない、BLE の挙動がおかしい
- DYA Studio で入れた設定を初期状態に戻したいとき

手順:

```
1. 左に settings_reset.uf2 → 2. 右に settings_reset.uf2
3. 左に CLine46_L.uf2      → 4. 右に CLine46_R.uf2
5. ホスト側の Bluetooth 設定から古い "CLine46" を削除
6. 右手側で BT_SEL 0（MO(3) + 左手中段の X 位置）を押してから再ペアリング
```

設定リセットをすると **DYA Studio で加えた変更もすべて消える**。必要なら事前に
DYA Studio の Import/Export からバックアップを取る（`docs/dya-studio.md` 参照）。

## 4. 既存ファームウェアへの巻き戻し

`firmware/` にコミット済みのビルド成果物がある。

| ディレクトリ | 構成 |
|---|---|
| `firmware/20260501/` | ZMK v0.3 系（`cormoran/zmk@v0.3-branch+dya`）。main ブランチ相当 |
| `firmware/20260816_zmk4.1_dya-studio/` | ZMK main+dya / 4.1 系。DYA Studio 全機能（`zmk4.1対応` ブランチ） |

巻き戻すときも「settings_reset を左右 → 目的の uf2 を左右」の順で行う。

## 5. ローカルでできる確認

ファームウェアをビルドせずに、キーマップの構文的な整合性だけは確認できる。

```bash
python3 tools/check_keymap.py
```
