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
6. 右手側で BT_SEL 0（`&lt 6 SEMICOLON`〔右手row2、L の右隣〕長押し + 左手中段の X 位置）を押してから再ペアリング
```

設定リセットをすると **DYA Studio で加えた変更もすべて消える**。必要なら事前に
DYA Studio の Import/Export からバックアップを取る（`docs/dya-studio.md` 参照）。

## 3.5 4.1 系に上げると左右が繋がらなくなる問題（部分的に未解決）

ZMK v0.3 系から 4.1 系（`main+dya`）に上げた直後、**左右のリンクが張れず、ホストとの BLE も
不安定**になった。v0.3 系（`firmware/20260501/`）に戻すと正常に動く、という症状。

DYA Studio のウォッチドッグに残っていたカーネル Oops を ELF で解決したところ、原因が判明した。

```
PC 0x0002b232 -> lll_central.c:250  LL_ASSERT_OVERHEAD  (central 役 = 左手側とのリンク)
PC 0x0002a514 -> lll_adv.c:1041     LL_ASSERT_OVERHEAD  (ホストへのアドバタイズ)
```

`lll_preempt_calc()` が「無線イベントの準備が予定に間に合わなかった」と判定したときのアサートで、
`CONFIG_BT_CTLR_ASSERT_OVERHEAD_START`（**Zephyr の既定は `y`**）が `k_oops()` に落としている。
4.1 系はモジュールが増えて CPU 負荷が重く、リンクを張ろうとするたびに落ちて再起動していた。

Zephyr は公式の回避策として次を用意している。

```
CONFIG_BT_CTLR_ASSERT_OVERHEAD_START=n
```

`CLine46_R.conf` / `CLine46_L.conf` の両方にこれを設定済みだが、**実機では効いていない**。
ビルドログを見ると次の Kconfig 警告が出ており、`n` を指定しても最終的な `.config` は `y` の
ままになる（2026-08-23 に GitHub Actions のビルドログで確認）。

```
warning: BT_CTLR_ASSERT_OVERHEAD_START ... was assigned the value 'n' but got the value 'y'.
```

`cormoran/zmk-feature-watchdog` の `DESIGN.md` §12.1 に同一事象の詳しい調査記録があり、
`-D` cmake 引数・`EXTRA_CONF_FILE`・素の `.conf` 記述など複数の方法を試したが、
`select`/`imply` の類はツリー内に見つからず、原因不明のまま対処を断念したとある
（「稀にしか起きず、JLink デバッガでの一時停止が誘発要因になっているようだ」との所見）。

つまり **`CONFIG_BT_CTLR_ASSERT_OVERHEAD_START=n` という対処自体が機能していない**。
これは Zephyr 本体の BLE コントローラ側の脆弱性で、split central 構成
（`BT_CENTRAL`+`BT_PERIPHERAL`+`BT_OBSERVER` を同時に動かす、ZMK の split central は
すべてこの条件に該当する）でのマルチロール負荷下に起因するとされており、
この設定リポジトリや watchdog モジュール自体のコードが原因ではない。

根本修正の手段が無いため、当面は CPU 負荷を下げて衝突（発生）確率を下げる方向で
緩和している。

- 未使用の `CONFIG_ZMK_PHYSICAL_LAYOUTS_FEATURE` を無効化（`CLine46_R.conf`）
- `CONFIG_ZMK_WATCHDOG_FREEZE_MONITOR_LOWPRIO_QUEUE=n` でウォッチドッグ自身の
  フリーズ検出タイマー数を半減（左右両方）。`zmk-feature-watchdog` の Kconfig ヘルプに
  「このモジュール自身の周期タイマーが BLE コントローラの極めてタイトな無線イベント
  準備タイミング（~275us）とたまたま衝突し、`LL_ASSERT_OVERHEAD` を誘発しうる」との
  記載があり、これに対応する

これらは緩和策であって根治ではない。DYA Studio 接続時にいきなり切断される場合、
この再起動（右手側の central が落ちて USB ごと瞬断される）が疑われる。

あわせて `CONFIG_ZMK_SPLIT_RELAY_EVENT` を **L 側にも**入れた。これは
"Relay Events from Peripheral to Central" という左右両方の機能だが、上流の構成では
R にしか無く、peripheral が relay 用のキャラクタリスティックを公開していなかった。
DYA Studio の「周辺側」タブが `Peripheral did not respond` になる原因はこれ。

> クラッシュ位置の解決には `.github/workflows/build-elf.yml`（ELF を出す手動ビルド）と
> `tools/resolve_crash.py`（PC/LR → 関数名・ソース行）を使う。

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
