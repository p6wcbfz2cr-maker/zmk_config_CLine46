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
#   CLINE46_FIRMWARE_DIR  uf2 の置き場（既定: firmware/20260816_zmk4.1_dya-studio）
#   CLINE46_TIMEOUT       ブートローダー待ち時間の秒数（既定: 60）

set -uo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FIRMWARE_DIR="${CLINE46_FIRMWARE_DIR:-$REPO_ROOT/firmware/20260816_zmk4.1_dya-studio}"
TIMEOUT="${CLINE46_TIMEOUT:-60}"

usage() {
    cat <<'USAGE'
使い方: tools/flash.sh <reset|left|right|uf2 へのパス>

  reset   設定リセット用ファームウェア（左右それぞれに書き込む）
  left    左手側（peripheral）
  right   右手側（central、トラックボールと USB Studio 側）
USAGE
}

case "${1:-}" in
    reset)        SRC="$FIRMWARE_DIR/settings_reset.uf2" ;;
    left  | l)    SRC="$FIRMWARE_DIR/CLine46_L.uf2" ;;
    right | r)    SRC="$FIRMWARE_DIR/CLine46_R.uf2" ;;
    "" | -h | --help) usage; exit 1 ;;
    *)            SRC="$1" ;;
esac

if [ ! -f "$SRC" ]; then
    echo "ファイルが見つかりません: $SRC" >&2
    exit 1
fi

find_volume() {
    local volume
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
