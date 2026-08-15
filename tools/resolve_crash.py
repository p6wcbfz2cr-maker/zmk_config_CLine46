#!/usr/bin/env python3
"""ウォッチドッグに残った PC / LR を、ELF から関数名とソース行に解決する。

DYA Studio の「トラブルシューティング → 安定性（ウォッチドッグ）」に残る
`PC 0x...., LR 0x....` を、その firmware の zmk.elf と突き合わせる。

ELF は `.github/workflows/build-elf.yml` を走らせると成果物として取れる
（通常の build.yml は uf2 しか出さない）。

使い方:
    python3 tools/resolve_crash.py <zmk.elf> 0x0002b232 0x0002a514 ...

関数名だけなら標準ライブラリのみで動く。ソース行まで出すには pyelftools が要る:
    pip3 install --user pyelftools
"""

import bisect
import struct
import sys

STT_FUNC = 2
SHT_SYMTAB = 2
# フラッシュに載るコードの下限。デバッグセクションは 0 番地起点の別アドレス空間を
# 持っていて実行アドレスと重なるため、これで弾く。
LOAD_LOW = 0x1000


def read_functions(data):
    """ELF32 のシンボルテーブルから (先頭アドレス, サイズ, 名前) を集める。"""
    if data[:4] != b"\x7fELF" or data[4] != 1:
        raise SystemExit("ELF32 ではありません")

    (e_shoff,) = struct.unpack_from("<I", data, 0x20)
    e_shentsize, e_shnum = struct.unpack_from("<HH", data, 0x2E)

    sections = []
    for i in range(e_shnum):
        off = e_shoff + i * e_shentsize
        fields = struct.unpack_from("<10I", data, off)
        sections.append(
            dict(type=fields[1], offset=fields[4], size=fields[5],
                 link=fields[6], entsize=fields[9])
        )

    funcs = []
    for sec in sections:
        if sec["type"] != SHT_SYMTAB or not sec["entsize"]:
            continue
        strtab = sections[sec["link"]]
        for i in range(sec["size"] // sec["entsize"]):
            off = sec["offset"] + i * sec["entsize"]
            st_name, st_value, st_size, st_info = struct.unpack_from("<IIIB", data, off)
            if (st_info & 0xF) != STT_FUNC:
                continue
            p = strtab["offset"] + st_name
            name = data[p:data.index(b"\0", p)].decode(errors="replace")
            funcs.append((st_value & ~1, st_size, name))

    funcs.sort()
    return funcs


def read_lines(path):
    """(アドレス, ファイル, 行) を集める。pyelftools が無ければ None。"""
    try:
        from elftools.elf.elffile import ELFFile
    except ImportError:
        return None

    rows = []
    with open(path, "rb") as fh:
        dwarf = ELFFile(fh).get_dwarf_info()
        for cu in dwarf.iter_CUs():
            line_program = dwarf.line_program_for_CU(cu)
            if line_program is None:
                continue
            header = line_program.header

            def filename(index):
                try:
                    entry = header.file_entry[index if header.version >= 5 else index - 1]
                    directory = header.include_directory[
                        entry.dir_index if header.version >= 5 else entry.dir_index - 1
                    ]
                    if isinstance(directory, bytes):
                        directory = directory.decode()
                    return f"{directory}/{entry.name.decode()}"
                except Exception:
                    return "?"

            for entry in line_program.get_entries():
                state = entry.state
                if state is None or state.end_sequence or state.address < LOAD_LOW:
                    continue
                rows.append((state.address, filename(state.file), state.line))

    rows.sort()
    return rows


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        return 1

    elf_path = sys.argv[1]
    with open(elf_path, "rb") as fh:
        data = fh.read()

    funcs = read_functions(data)
    func_starts = [f[0] for f in funcs]

    lines = read_lines(elf_path)
    if lines is None:
        print("※ pyelftools が無いため関数名のみ（pip3 install --user pyelftools で行番号も出ます）\n")
        line_addrs = []
    else:
        line_addrs = [r[0] for r in lines]

    for arg in sys.argv[2:]:
        # Thumb のリターンアドレスは bit0 が立っているので落とす
        addr = int(arg, 16) & ~1
        print(f"0x{addr:08x}")

        i = bisect.bisect_right(func_starts, addr) - 1
        if i < 0:
            print("    関数: 該当なし")
        else:
            start, size, name = funcs[i]
            outside = "  ※ シンボル範囲外" if size and addr >= start + size else ""
            print(f"    関数: {name} +{addr - start}{outside}")

        if line_addrs:
            j = bisect.bisect_right(line_addrs, addr) - 1
            if j >= 0:
                _, filename, line = lines[j]
                print(f"    行  : {filename}:{line}")
        print()

    return 0


if __name__ == "__main__":
    sys.exit(main())
