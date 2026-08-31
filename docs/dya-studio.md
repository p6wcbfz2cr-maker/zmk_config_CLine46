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
4. **Studio Unlock**: `&lt 6 SEMICOLON`（右手row2、`L` の右隣、キー位置22）を押しながら、
   **右親指の ENTER 位置**を押す（キー位置 42 の `&studio_unlock`、レイヤー`6_ble`内）
   - Unlock しないと閲覧はできても書き換えができない
5. 変更後は画面の保存操作でキーボード本体のフラッシュに保存される

実機がなくても「デモモードを試す」で画面を確認できる。

## ⚠️ キーマップタブの「並び替え」を使わない

Studio の `キーマップ` タブにあるレイヤーの並び替え機能（レイヤーの表示順＝実インデックスを
変更する）は**使わないこと**。これは元々 `CLAUDE.md` に書かれている制約
（`config/CLine46.keymap` 側でレイヤー順を変えてはいけない）と同じ理由で、Studio上の
並び替えでも壊れる。

- `CLine46_R.overlay` の `scroller { layers = <6>; }` は「今インデックス6にあるレイヤー」に
  無条件で紐づく静的な設定。並び替えるとスクロールが別のレイヤーで発動する（または発動しなく
  なる）
- トラックボールの「一時レイヤー」機能は、Studioが送るレイヤーIDとファームウェアが期待する
  インデックスの対応が「並び替えていない」前提でしか成立しない（下記「既知の問題」参照）。
  並び替えると対象レイヤーがズレたり、最悪スクロール固定の無限ループに陥る

レイヤーの**中身**（どのキーに何を割り当てるか、名前）を変えるのは問題ない。**並び順
（インデックス）だけは触らない。**

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
| Trackball のスクロール専用チェーン（レイヤー6 = `6_ble` 中の速度・XY反転） | ○ | `CLine46_R.overlay` の `scroller` が `scroll_runtime_input_processor` を使用 |
| Trackball（PMW3610 の CPI・省電力など詳細設定） | ○ | `zmk-driver-pmw3610-with-custom-studio-rpc` + `CONFIG_ZMK_PMW3610_CUSTOM_SETTINGS=y`。`Settings（詳細設定）` タブに出る。下記「PMW3610 の詳細設定」参照 |
| Connection（BLE プロファイル） | ○ | `zmk-module-ble-management` |
| Connection（接続先別デフォルトレイヤー） | ×（試したが起動時クラッシュのため見送り） | `zmk-feature-default-layer`。詳細は下記「接続先別デフォルトレイヤーは使わない」参照 |
| Connection（OS 自動検出） | ◎ | `zmk-feature-os-detection`（`3052679f`）+ `CONFIG_ZMK_OS_DETECTION_*` |
| Connection（OS 別レイヤー自動切替） | ○ | `CONFIG_ZMK_OS_DETECTION_LAYER_AUTO_SWITCH=y`（`0_base_mac`/`1_base_win`を自動切替、実機未確認） |
| Settings（idle / sleep） | ○ | `zmk-module-settings-rpc` |
| Settings（詳細設定） | ○ | `CONFIG_ZMK_CUSTOM_SETTINGS=y`（`runtime-macro` / `runtime-combo` の `import: true` 経由で取り込まれる）。PMW3610 の項目もここに出る |
| Troubleshooting（Device Info） | ◎ | `zmk-feature-device-info` |
| Troubleshooting（Watchdog: 再起動原因） | ◎ | `zmk-feature-watchdog`。**中央側・周辺側とも確認済み**。周辺側は `CLine46_L.conf` 側の設定が要る（下記） |
| Troubleshooting（KSCAN 診断） | ○ | `zmk-feature-kscan-diagnostics` |
| バッテリー履歴 | × | `CONFIG_ZMK_BATTERY_HISTORY` はコメントアウト（保存が遅い問題のため上流で無効化中） |

> 残りのタブを確認したら ○ を ◎ に更新する。

`zmk-module-runtime-input-processor` を使うノードは Studio の Trackball 設定に
processor 単位で個別に表示される。CLine46 では現在 `mouse`（通常のポインター移動、
`CLine46_R.overlay` トップレベルの `input-processors`）と `scroll`（レイヤー6 = `6_ble`
専用の `scroller` チェーン）の 2 つが並んで表示され、それぞれ独立に速度
（`scale-multiplier`/`scale-divisor`）・向き反転（X/Y invert）などを変更できる。

### 周辺側（左手側）を Studio から見るために必要な設定

上流の構成は Studio 関連の設定を R.conf にしか置いておらず、周辺側の情報は
一切取れなかった。左手側を見るには `CLine46_L.conf` に次の 3 つが要る。

```
CONFIG_ZMK_SPLIT_RELAY_EVENT=y            # relay のキャラクタリスティックを公開する
CONFIG_ZMK_SPLIT_RELAY_EVENT_DATA_LEN=240 # R 側と揃える
CONFIG_ZMK_WATCHDOG=y                     # 中継された要求に答える相手を用意する
CONFIG_ZMK_LOW_PRIORITY_THREAD_STACK_SIZE=4096   # 応答の組み立てに要る
CONFIG_SYSTEM_WORKQUEUE_STACK_SIZE=4096
```

1 つでも欠けると症状が変わる。relay が無ければタイムアウト、`ZMK_WATCHDOG` が
無ければやはりタイムアウト、スタックが足りなければ**中央側が落ちて Studio が切断**される。
同じ理屈で、他の Studio 機能を周辺側にも広げたい場合は該当モジュールを L.conf でも
有効にする必要がある（Device Info、KSCAN 診断など）。

## PMW3610 の詳細設定（CPI・レストモード）

**Trackball タブの「感度」とは別物**なので注意する。

| | Trackball タブの感度 | Settings（詳細設定）の `cpi` |
|---|---|---|
| 実体 | `zmk-module-runtime-input-processor` の `scale-multiplier`/`scale-divisor` | センサー PMW3610 の解像度そのもの |
| 効く場所 | センサーが出したカウントの**後段**での倍率 | センサーが**カウントを出す時点**の細かさ |
| 低速時の取りこぼし | 直せない（切り捨てられた後なので復元できない） | 直せる |

ゆっくり動かしたときの追従が悪い場合に効くのは後者。前者をいくら上げても、
1 レポート周期に 1 カウントも溜まらず切り捨てられた動きは戻らない。

### 出てくる項目

ドライバを `cormoran/zmk-driver-pmw3610-with-custom-studio-rpc` に差し替え、
`CLine46_R.conf` に `CONFIG_ZMK_PMW3610_CUSTOM_SETTINGS=y` を置いたことで、
以下 13 項目がサブシステム `cormoran__pmw3610` として **Settings（詳細設定）** タブに出る。
キーは `<項目名>@trackbal`。末尾は overlay の `settings-id` 由来だが、**ファーム側の
バッファが 8 文字ぶんしかない**ため `"trackball"`（9 文字）は `trackbal` に切り詰められる
（`l` が 1 つ落ちる。誤字ではない）。登録側も参照側も同じ切り詰め後の値を使うので
動作に影響はない。`settings-id` を付ける際は 8 文字以内に収めるのが無難。

> セクションが出てこない場合、まず**新しいファームを書き込んだか**を疑う。
> 新ファームなら 4 つ目に `cormoran__pmw3610`（**13 件の設定**）が並ぶ。

### ⚠️ 必要な CONFIG は 2 つある（ハマりどころ）

`CLine46_R.conf` に**両方**要る。片方だけでは詳細設定に何も出ない。

```conf
CONFIG_ZMK_PMW3610_CUSTOM_SETTINGS=y   # 設定を登録する
CONFIG_ZMK_PMW3610_STUDIO_RPC=y        # サブシステムをRPCに登録する ← これが無いと出ない
```

Kconfig 上、`ZMK_PMW3610_CUSTOM_SETTINGS` は `depends on ZMK_CUSTOM_SETTINGS` だけなので
`STUDIO_RPC` は不要に見えるが、**実際には必須**。理由は
`zmk-feature-custom-settings` の `src/studio/custom_settings_handler.c` にある
`custom_subsystem_index_for_identifier()` で、設定を protobuf に詰める前に
「その `custom_subsystem_id` が RPC サブシステムとして登録済みか」を走査し、
無ければ `-ENOENT` を返して**その設定を黙って捨てる**ため。

`STUDIO_RPC` を切ると `cormoran__pmw3610` が RPC サブシステム登録に載らないので、
13 項目が丸ごと Studio に届かない。**ファーム側の設定登録自体は正常に行われている**
（ELF の `zmk_custom_setting_area` には 13 項目とも入っている）ので、
症状だけ見ると「なぜか出ない」となり原因に辿り着きにくい。

切り分け方: ELF で登録状況を直接見るのが確実。

```bash
# 設定が登録されているか（ここに出るのは前提条件でしかない）
nm CLine46_R.elf | grep pmw3610_setting_
# RPCサブシステムに載っているか（こちらが表示の可否を決める）
nm CLine46_R.elf | grep zmk_rpc_custom_subsystem_
```

後者に `zmk_rpc_custom_subsystem_cormoran__pmw3610` が無ければ、
`CONFIG_ZMK_PMW3610_STUDIO_RPC=y` が抜けている。

| 項目 | 範囲 | 本リポジトリの既定値 | 意味 |
|---|---|---|---|
| `cpi` | 200–3200（200 刻み） | 600 | センサー解像度。上げると低速時の追従が良くなる代わりに高速時が過敏になる |
| `run_downshift_ms` | 32–8160 | **2000** | 無操作からこの時間で RUN → REST1 に落ちる。短いと動き出しが飲まれる |
| `rest1_sample_ms` | 10–2550 | **20** | REST1 のサンプル周期。小さいほど復帰が早く、消費電力は増える |
| `rest1_downshift_ms` | 320–81600 | 5000 | REST1 → REST2 |
| `rest2_sample_ms` | 10–2550 | 100 | REST2 のサンプル周期 |
| `rest2_downshift_ms` | 12800–3264000 | 17000 | REST2 → REST3 |
| `rest3_sample_ms` | 10–2550 | 500 | REST3 のサンプル周期 |
| `report_interval_min_ms` | 0–1000 | 0 | 最小レポート間隔。0 = 制限なし |
| `force_awake` | bool | false | ZMK が ACTIVE の間はダウンシフトさせない。反応は最良だが消費電力と CPU 負荷が増える |
| `smart_algorithm` | bool | true | 表面追従の内部補正 |
| `swap_xy` / `invert_x` / `invert_y` | bool | false | 軸の入れ替え・反転 |

太字は「ゆっくり動かすと反応が遅い」対策として既定値から変更したもの
（ドライバ既定は `run_downshift_ms=128` / `rest1_sample_ms=40`）。

> **`invert_x` を ON にしないこと。** 本機の X 軸反転は `CLine46_R.overlay` の
> `&trackball_listener` にある `zip_xy_transform INPUT_TRANSFORM_X_INVERT` で既に
> 掛かっている。センサー側でも反転すると二重になって元に戻ってしまう。

> **`*_downshift_ms` の範囲は `*_sample_ms` から決まる。** 上表の範囲は
> `rest1_downshift_ms` が `rest1_sample_ms × 16`〜`× 4080`、`rest2_downshift_ms` が
> `rest2_sample_ms × 128`〜`× 32640` として算出されたもので、**ビルド時の
> `CONFIG_PMW3610_REST*_SAMPLE_TIME_MS` を基準に固定されている**。Studio で
> `rest1_sample_ms` を変えた後に `rest1_downshift_ms` を書くと、Studio 側の範囲
> チェックは通ってもドライバ側で（現在のサンプル周期を基準に）拒否されることがある。
> 両方を大きく変えたい場合は、Studio で詰めるより `CLine46_R.conf` に書いてビルドし直す
> ほうが確実。

### 追い込みの手順

一度に複数変えず、この順で 1 項目ずつ実機確認する。

1. まず素の状態でゆっくり動かし、既定値変更だけで解消したか確認する
2. `cpi` を 600 → 800 → 1000 と上げ、低速の追従と高速の過敏さの折り合いを探す
3. まだ動き出しが飲まれるなら `run_downshift_ms` を上げる / `rest1_sample_ms` を下げる
4. それでも残るなら `force_awake` を ON にして切り分ける。ON で消えるならレストモードが
   原因と確定できる（常用するかは消費電力と相談）

**値が固まったら `CLine46_R.conf` の `CONFIG_PMW3610_*`（と必要なら overlay の `cpi`）に
反映してコミットする。** Studio の値はフラッシュにしか無く、ファーム再書き込みや
`settings_reset.uf2` で消える（下記「設定ファイルとの関係」）。

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

このモジュールには「検出した OS に応じてレイヤーを自動で有効化する」機能があり、**有効化済み**
（`CLine46_R.conf`）。

OS → レイヤー番号の対応は **ビルド時の Kconfig 固定**で、Studio からは変更できない。
実行時に変えられるのは検出結果の表示と手動上書きだけ。

```
CONFIG_ZMK_OS_DETECTION_LAYER_AUTO_SWITCH=y
CONFIG_ZMK_OS_DETECTION_LAYER_WINDOWS=1
```

ZMK では**レイヤー0は常時有効な土台レイヤーで無効化できない**ため、`LAYER_MACOS` /
`LAYER_IOS` は指定していない（既定値 `-1` のまま）。実際の構成は対称な2レイヤーではなく:

- `0_base_mac`（index 0）: 常時有効な土台レイヤー。Mac向けの内容を直接書く
- `1_base_win`（index 1）: Windows検出時だけ `0_base_mac` の上にオーバーレイとして自動有効化される
  差分レイヤー。現状すべて `&trans`（差分は未設定）

macOS / iOS 検出時は追加のレイヤー活性化が不要なため、`0_base_mac` がそのまま使われる。

### 接続先別デフォルトレイヤーは使わない（起動時クラッシュの既知問題）

`cormoran/zmk-feature-default-layer` を使うと、DYA Studio の Connection タブ上で
接続先ごとにデフォルトレイヤーを選択・記憶できるはずだった（`CONFIG_ZMK_DEFAULT_LAYER`）。
`config/west.yml` には依存としてピン留め済みだが、**実際に有効化して試したところ、
書き込み直後からキー操作なしで連続的に再起動する症状が発生した**（2026-08-26、実機で確認）。

**原因（`zmk-feature-default-layer` 側のバグと推定）**:
`src/behaviors/behavior_default_layer.c` の `default_layer_init()` は
`SYS_INIT`（`APPLICATION` 優先度）で起動直後に呼ばれるが、ソースコード中に
開発者自身のコメントで次のように明記されている。

```
// NOTE: endpoint is not initialized yet. zmk_endpoint_get_selected doesn't
// return proper value.
```

つまり、まだ正しく初期化されていない endpoint の情報を使って
`apply_default_layer_config()` を呼んでおり、そこで求めたインデックスが不正な値になると
`zmk_keymap_layer_activate()` に不正なレイヤー番号を渡してクラッシュする可能性が高い。
起動直後に毎回同じ場所でクラッシュするため、電源を入れるたびに再起動を繰り返す症状になる。

ビルド自体は成功し、RAM/FLASH使用量も既存構成とほぼ同じ（差100バイト程度）だったため、
メモリ不足ではなくこの初期化順序の問題が直接の原因と考えられる。GitHub Issuesには
報告が無く、モジュール自体もREADMEのTODOに未実装項目（`Respect CONFIG_SETTING flag`）が
残る発展途上の状態。

**対応**: このモジュールの使用を見送り、前述の `zmk-feature-os-detection` の
`CONFIG_ZMK_OS_DETECTION_LAYER_AUTO_SWITCH`（Studio上には見えないが安定動作する
ビルド時固定の自動切替方式）のままとする。`config/west.yml` の
`zmk-feature-default-layer` のピン留め自体は残しているが、`CONFIG_ZMK_DEFAULT_LAYER` は
有効化しない。将来モジュール側の初期化順序が修正されたら再検討する。

## 既知の問題: 一時レイヤー（temp-layer）の対象レイヤーがズレる

`トラックボール設定 → mouse プロセッサー → 一時レイヤー` の「対象レイヤー」で選んだ
レイヤーと、実際にトラックボール使用時に有効化されるレイヤーが食い違うことがある
（2026-08-16、実機で確認）。

**原因（`zmk-module-runtime-input-processor` 側のバグと推定）**:
DYA Studio 本体（[cormoran/dya-studio](https://github.com/cormoran/dya-studio) の
`src/pages/TrackballPage.tsx` / `src/hooks/useKeymap.ts`）は、レイヤーの
**並び替えても変わらない安定した `id`** を対象レイヤーとして送信している。
devicetree の `temp-layer` プロパティの説明も「Default target layer **ID**」と明記して
おり、Studio 側の実装は仕様通り。

一方、[cormoran/zmk-module-runtime-input-processor](https://github.com/cormoran/zmk-module-runtime-input-processor)
の `src/pointing/input_processor_runtime.c` は、Studio から受け取ったこの値をそのまま
`zmk_keymap_layer_activate()` や `zmk_keymap_get_layer_binding_at_idx()`
（関数名の `_at_idx` が示す通り、本来は「現在の表示順インデックス」を期待する）に渡して
おり、ID→インデックスの変換をしていない。レイヤーを一度も並び替えていなければ ID と
インデックスが一致するため気づきにくいが、Studio でレイヤーを並び替えた後は対象レイヤーが
別のレイヤーにすり替わる。

**関連する別バグ**: 対象レイヤーを変更しても、既に有効化されているレイヤーは無効化されない
（`zmk_input_processor_runtime_set_temp_layer_layer()` 等が `temp_layer_layer_active` を
見ずに設定値を上書きするだけのため）。誤って `scroller` が紐づくレイヤー（本リポジトリでは
レイヤー6 = `6_ble`）を対象にすると、トラックボールがスクロールモードに固定される
無限ループに陥る。**再起動しても直らないことがあり**、その場合は `mouse` プロセッサーを
一度リセット（工場出荷時のデフォルトに戻す）すると復旧する。

**現状の回避策**: Studio の「ストリーム」表示（キーマップタブ）で、実際にどのレイヤーが
光るかを目視確認し、使いたい割り当て（クリックキーなど）をそのレイヤーの中身として置く。

実例（2026-08-18、`インポート/エクスポート` でエクスポートした `.keymap` で裏付け済み）:
`mouse` という名前のレイヤーは実インデックス5にあるが、一時レイヤーの対象を `mouse` に
選ぶとプロセッサーカードには古いID（4）が表示され、正しく発火しなかった。**「レイヤー5」
という選択肢を選んだときに実際に発火するスロットへ `mouse` レイヤーの中身（`&mkp MB1`
などのクリック割り当て）を移した**ところ、一時レイヤーが正しく機能するようになった。
対象レイヤー名と実際に発火するスロットが一致しないことがある前提で、中身をスロット側に
合わせるのが確実な回避策。

**Issue報告**: 未報告（2026-08-16時点）。修正は `zmk-module-runtime-input-processor` 側の
対応が必要で、本リポジトリの `config/` からは直せない。

## うまくいかないとき

| 症状 | 確認すること |
|---|---|
| そもそも接続できない | 右手側を USB で繋いでいるか / `build.yaml` の `snippet: studio-rpc-usb-uart` / `CONFIG_ZMK_STUDIO=y` / Chrome か Edge か |
| Keymap は見えるが変更できない | Studio Unlock したか（`&lt 6 SEMICOLON` + 右親指 ENTER 位置） |
| 期待したタブが「未対応です」になる | `config/west.yml` に該当モジュールがあるか、`CLine46_R.conf` に `*_STUDIO_RPC=y` があるか |
| フリーズや勝手に再起動する | スタック不足の可能性。`CLine46_R.conf` の `CONFIG_ZMK_STUDIO_RPC_THREAD_STACK_SIZE` / `CONFIG_SYSTEM_WORKQUEUE_STACK_SIZE` などを確認。Troubleshooting タブの Watchdog に再起動原因が残る |
| キー位置がずれる | `CLine46.dtsi` の physical layout と `default_transform`、`python3 tools/check_keymap.py` |
| トラックボールが**低速時だけ**反応が鈍い | レストモードからの復帰遅延の可能性が高い。Settings（詳細設定）で `run_downshift_ms` を上げる / `rest1_sample_ms` を下げる / `cpi` を上げる。切り分けは `force_awake` を ON にして消えるか見る。詳細は上記「PMW3610 の詳細設定」 |
| トラックボールの**向きが逆**になった | `invert_x` / `invert_y` / `swap_xy` を触っていないか。X 反転は overlay の `zip_xy_transform` で既に掛かっており、Studio 側で重ねると二重反転になる |
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
