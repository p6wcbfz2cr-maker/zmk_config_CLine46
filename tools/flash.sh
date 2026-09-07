#!/usr/bin/env bash
#
# CLine46 のファームウェアを XIAO の UF2 ブートローダーへ書き込む。
#
# macOS の Finder でドラッグ&ドロップすると、AppleDouble メタデータ（._ で始まる
# ファイル）や Spotlight インデックスを一緒に書こうとして、容量の小さい UF2 ドライブが
# 「操作を完了できません（エラー -36 / -50）」「ディスクが一杯です」で失敗することがある。
# このスクリプトは Finder を経由せず、拡張属性を付けずにコピーする。
#
# 使い方:
#   tools/flash.sh reset    # settings_reset.uf2
#   tools/flash.sh left     # CLine46_L.uf2
#   tools/flash.sh right    # CLine46_R.uf2
#   tools/flash.sh <uf2 へのパス>
#
# 環境変数:
#   CLINE46_FIRMWARE_DIR  uf2 の置き場（既定: firmware/20260907_pmw3610_motion_overflow）
#   CLINE46_TIMEOUT       ブートローダー待ち時間の秒数（既定: 60）

set -uo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FIRMWARE_DIR="${CLINE46_FIRMWARE_DIR:-$REPO_ROOT/firmware/20260907_pmw3610_motion_overflow}"
TIMEOUT="${CLINE46_TIMEOUT:-60}"

usage() {
    cat <<'USAGE'
使い方: tools/flash.sh <reset|left|right|uf2 へのパス>

  reset   設定リセット用ファームウェア（左右それぞれに書き込む）
  left    左手側（peripheral）
  right   右手側（central、トラックボールと USB Studio 側）
USAGE
}

# EXPECT: そのドライブに現在入っているはずの側。左右を取り違えた書き込みを止めるのに使う。
# reset は左右どちらにも流すので判定しない。
case "${1:-}" in
    reset)        SRC="$FIRMWARE_DIR/settings_reset.uf2"; EXPECT="" ;;
    left  | l)    SRC="$FIRMWARE_DIR/CLine46_L.uf2";      EXPECT="CLine46_L" ;;
    right | r)    SRC="$FIRMWARE_DIR/CLine46_R.uf2";      EXPECT="CLine46_R" ;;
    "" | -h | --help) usage; exit 1 ;;
    *)            SRC="$1"; EXPECT="" ;;
esac

if [ ! -f "$SRC" ]; then
    echo "ファイルが見つかりません: $SRC" >&2
    exit 1
fi

find_volume() {
    local volume
    # CLINE46_VOLUME で書き込み先を明示できる（動作確認用、複数ドライブがあるとき用）
    if [ -n "${CLINE46_VOLUME:-}" ]; then
        printf '%s' "$CLINE46_VOLUME"
        return 0
    fi
    for volume in /Volumes/*; do
        if [ -f "$volume/INFO_UF2.TXT" ]; then
            printf '%s' "$volume"
            return 0
        fi
    done
    return 1
}

echo "書き込むファイル: $SRC"
echo "                 $(wc -c < "$SRC" | tr -d ' ') バイト"
echo

VOLUME="$(find_volume)" || {
    echo "XIAO のリセットボタンを素早く 2 回押してください（最大 ${TIMEOUT} 秒待ちます）"
    for _ in $(seq "$TIMEOUT"); do
        sleep 1
        VOLUME="$(find_volume)" && break
    done
}

if [ -z "${VOLUME:-}" ]; then
    echo >&2
    echo "ブートローダードライブが見つかりませんでした。" >&2
    echo "  - ダブルリセットのタイミング（素早く 2 回）を変えて試す" >&2
    echo "  - USB ケーブルが充電専用でないか確認する" >&2
    exit 1
fi

echo "ブートローダーを検出: $VOLUME"
if [ -f "$VOLUME/INFO_UF2.TXT" ]; then
    sed -n '1,3p' "$VOLUME/INFO_UF2.TXT" | sed 's/^/  /'
fi

# このドライブが左右どちらかを、CURRENT.UF2（現在のフラッシュ内容）から判定する。
# このスクリプトは最初に見つけたドライブに書くだけなので、反対側をダブルリセット
# していると逆のファームが入ってしまう。それを書き込む前に止める。
identify_side() {
    local identify="$REPO_ROOT/tools/identify_half.py"
    [ -f "$VOLUME/CURRENT.UF2" ] || return 1
    [ -f "$identify" ] || return 1
    command -v python3 >/dev/null || return 1

    # 照合先は「今から焼こうとしている置き場」だけでは足りない。ドライブに入って
    # いるのは前の世代のファームかもしれないので、firmware/ 配下も全部候補にする。
    local -a refs=()
    local f
    shopt -s nullglob
    for f in "$REPO_ROOT"/firmware/*/CLine46_[LR]*.uf2; do
        refs+=("$f")
    done
    case "$FIRMWARE_DIR" in
        "$REPO_ROOT"/firmware/*) ;;   # 上の glob に含まれているので足さない
        *) for f in "$FIRMWARE_DIR"/CLine46_[LR]*.uf2; do refs+=("$f"); done ;;
    esac
    shopt -u nullglob

    [ ${#refs[@]} -gt 0 ] || return 1
    python3 "$identify" "$VOLUME/CURRENT.UF2" "${refs[@]}" 2>/dev/null | head -1
}

TOP="$(identify_side)"
if [ -n "${TOP:-}" ]; then
    # ラベルには空白が入りうる（例: "CLine46_L rgbled_adapter-seeeduino_xiao_ble-zmk"）
    # ので、末尾の一致率だけを切り出す。
    SCORE="${TOP##* }"
    LABEL="${TOP% *}"
    case "$LABEL" in
        CLine46_L*) SIDE="CLine46_L" ;;
        CLine46_R*) SIDE="CLine46_R" ;;
        *)          SIDE="" ;;
    esac
    echo "  現在の中身: $LABEL に ${SCORE}% 一致"
    # 一致率が低いときは判定できない（別のファームや空など）ので何も言わない
    if [ -n "$SIDE" ] && [ "${SCORE%%.*}" -ge 50 ] && [ -n "$EXPECT" ] && [ "$SIDE" != "$EXPECT" ]; then
        echo >&2
        echo "中断: 反対側に書き込もうとしています。" >&2
        echo "  書き込もうとしたもの: $(basename "$SRC")" >&2
        echo "  このドライブの中身  : $SIDE" >&2
        echo "  もう片方をダブルリセットし直してください。" >&2
        echo "  意図的に行う場合は CLINE46_YES=1 を付けて実行します。" >&2
        [ "${CLINE46_YES:-}" = "1" ] || exit 1
        echo "CLINE46_YES=1 のため続行します。" >&2
    fi
fi

# Finder が過去に書いたメタデータが残っていると容量不足になることがあるので掃除する
rm -f "$VOLUME"/._* "$VOLUME"/.DS_Store 2>/dev/null
mdutil -i off "$VOLUME" >/dev/null 2>&1

echo "コピー中..."
# -X: 拡張属性・リソースフォークをコピーしない（._ ファイルを作らせない）
cp -X "$SRC" "$VOLUME/"
COPY_STATUS=$?
sync

# 書き込みが受理されるとデバイスは即座に再起動し、ドライブが外れる。
# そのため cp が終盤でエラーを返すことがあるが、ドライブが消えていれば成功。
for _ in $(seq 20); do
    [ -d "$VOLUME" ] || break
    sleep 1
done

echo
if [ ! -d "$VOLUME" ]; then
    echo "書き込み完了（デバイスが再起動してドライブが外れました）"
    exit 0
fi

if [ "$COPY_STATUS" -eq 0 ]; then
    echo "コピーは成功しましたが、ドライブがまだマウントされています。"
    echo "デバイスが再起動していない可能性があります。"
    exit 0
fi

echo "コピーに失敗しました（終了コード $COPY_STATUS）" >&2
echo "ドライブの空き容量:" >&2
df -h "$VOLUME" >&2
exit 1
