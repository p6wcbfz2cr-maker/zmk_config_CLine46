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

上流がビルドした uf2 が `firmware/20260816_zmk4.1_dya-studio/` に同梱されている。
これは**上流コミット `a19f381` 時点の `config/` `boards/` `build.yaml` に対応する成果物**。

DYA Studio の動作だけ確認したい場合は、ビルドを待たずに「3. 設定リセット」の手順で
この 3 ファイルを書き込めばよい。

> **設定を変更したら同梱 uf2 とは一致しなくなる。** 現在の内容と一致するかは
> `git diff a19f381..HEAD -- config boards build.yaml` が空かどうかで確認できる。
> 空でなければ「1. ビルド」で作り直すこと。
> （例: OS 自動検出の追加で `config/west.yml` と `CLine46_R.conf` が変わっている）

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

### 推奨: スクリプトで書き込む（macOS）

```bash
./tools/flash.sh reset    # settings_reset.uf2
./tools/flash.sh left     # CLine46_L.uf2
./tools/flash.sh right    # CLine46_R.uf2
```

実行するとブートローダーの検出待ちになるので、その間に XIAO のリセットボタンを
**素早く 2 回押す**（ダブルリセット）。検出後に自動でコピーされる。

**Finder のドラッグ&ドロップは失敗することがある。** macOS は UF2 ドライブに
AppleDouble メタデータ（`._` で始まるファイル）や Spotlight のインデックスを
書こうとするが、UF2 ドライブは容量が極小のため
「操作を完了できません（エラー -36 / -50）」「ディスクが一杯です」で弾かれる。
スクリプトは `cp -X`（拡張属性を付けない）でコピーし、事前に残留メタデータの掃除と
Spotlight インデックスの無効化を行うため、この問題を回避できる。

### 左右の取り違え防止

スクリプトは `/Volumes/*` の中で `INFO_UF2.TXT` を持つ**最初のドライブ**に書き込む。
XIAO は左右で見分けが付かないため、これだけだと反対側をダブルリセットしたときに
逆のファームが入ってしまう。

そこで書き込む前に、ドライブの `CURRENT.UF2`（＝現在フラッシュに入っている内容）を
`firmware/` の uf2 と突き合わせて、どちら側かを判定している。

```
ブートローダーを検出: /Volumes/XIAO-SENSE
  現在の中身: CLine46_L に 100.0% 一致

中断: 反対側に書き込もうとしています。
  書き込もうとしたもの: CLine46_R.uf2
  このドライブの中身  : CLine46_L
```

設定リセット直後でも判定できる。`settings_reset` は先頭 60KB ほどしか使わず、
その先には前のファームが残るため、L と R のどちらに近いかで区別が付く。

| 環境変数 | 効果 |
|---|---|
| `CLINE46_YES=1` | 取り違えの警告を無視して書き込む |
| `CLINE46_VOLUME` | 書き込み先のドライブを明示する（動作確認用） |
| `CLINE46_FIRMWARE_DIR` | uf2 の置き場（既定は `firmware/20260816_zmk4.1_dya-studio`） |
| `CLINE46_TIMEOUT` | ブートローダー待ちの秒数（既定 60） |

判定だけを単独で行うこともできる。

```bash
python3 tools/identify_half.py /Volumes/XIAO-SENSE/CURRENT.UF2 \
    firmware/20260816_zmk4.1_dya-studio/CLine46_L.uf2 \
    firmware/20260816_zmk4.1_dya-studio/CLine46_R.uf2
```

### 手動で行う場合

```bash
# ダブルリセットしてドライブが出てから
cp -X firmware/20260816_zmk4.1_dya-studio/settings_reset.uf2 /Volumes/XIAO-SENSE/
```

Finder を使う場合は、コピー前にドライブ内の `._*` を削除しておく。

### 書き込み完了の見分け方

uf2 を受け取るとデバイスは即座に再起動し、**ドライブが消える**。これが成功の合図。
macOS が「ディスクの取り出しが正しく行われませんでした」と警告するが、
書き込みは完了しているので無視してよい。

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
