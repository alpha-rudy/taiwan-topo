#!/usr/bin/env python3
"""Assemble ZIP archives by reusing pre-compressed streams when available.

Copies raw compressed payloads directly from existing ZIP archives without
decompressing or recompressing them, while transparently falling back to
streaming zlib deflate when a reusable archive is missing or older than the
source file on disk.
"""

from __future__ import annotations

import argparse
import contextlib
import fnmatch
import os
import struct
import sys
import time
import zipfile
import zlib
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import IO

_CHUNK_SIZE = 1024 * 1024  # 1 MiB
_ZIP64_LIMIT = 0xFFFFFFFF
_ZIP64_COUNT_LIMIT = 0xFFFF
_UTF8_FLAG = 0x0800
_LFH_STRUCT = struct.Struct("<4sHHHHHIIIHH")
_CDH_STRUCT = struct.Struct("<4sHHHHHHIIIHHHHHII")
_EOCD_STRUCT = struct.Struct("<4sHHHHIIH")
_ZIP64_EOCD_STRUCT = struct.Struct("<4sQHHIIQQQQ")
_ZIP64_LOCATOR_STRUCT = struct.Struct("<4sIQI")


@dataclass
class _EntryRecord:
    arcname_bytes: bytes
    flag_bits: int
    compress_type: int
    dos_time: int
    dos_date: int
    crc: int
    compress_size: int
    file_size: int
    external_attr: int
    header_offset: int
    extract_version: int


def _encode_dos_datetime(date_time: tuple[int, int, int, int, int, int]) -> tuple[int, int]:
    year, month, day, hour, minute, second = date_time
    if year < 1980:
        year, month, day, hour, minute, second = 1980, 1, 1, 0, 0, 0
    dos_date = ((year - 1980) << 9) | (month << 5) | day
    dos_time = (hour << 11) | (minute << 5) | (second // 2)
    return dos_time, dos_date


def _mtime_to_dos_datetime(mtime: float) -> tuple[int, int]:
    lt = time.localtime(mtime)
    return _encode_dos_datetime((lt.tm_year, lt.tm_mon, lt.tm_mday, lt.tm_hour, lt.tm_min, lt.tm_sec))


def _encode_arcname(arcname: str) -> tuple[bytes, int]:
    try:
        return arcname.encode("ascii"), 0
    except UnicodeEncodeError:
        return arcname.encode("utf-8"), _UTF8_FLAG


def _pack_zip64_extra(*values: int) -> bytes:
    if not values:
        return b""
    body = struct.pack(f"<{len(values)}Q", *values)
    return struct.pack("<HH", 0x0001, len(body)) + body


class _ZipSourceCache:
    """Cache opened ZipFile + raw binary handles per source archive path."""

    def __init__(self) -> None:
        self._stack = contextlib.ExitStack()
        self._cache: dict[Path, tuple[zipfile.ZipFile, IO[bytes]]] = {}

    def open(self, path: Path) -> tuple[zipfile.ZipFile, IO[bytes]]:
        resolved = path.resolve()
        cached = self._cache.get(resolved)
        if cached is not None:
            return cached
        zf = self._stack.enter_context(zipfile.ZipFile(resolved, "r"))
        raw_fp = self._stack.enter_context(resolved.open("rb"))
        pair = (zf, raw_fp)
        self._cache[resolved] = pair
        return pair

    def close(self) -> None:
        self._stack.close()
        self._cache.clear()


class _ZipAssembler:
    """Write a ZIP archive supporting raw entry copying and streaming deflate."""

    def __init__(self, out_fp: IO[bytes]) -> None:
        self._fp = out_fp
        self._entries: list[_EntryRecord] = []
        self._seen: set[str] = set()

    def _write_local_header(
        self,
        arcname_bytes: bytes,
        flag_bits: int,
        compress_type: int,
        dos_time: int,
        dos_date: int,
        crc: int,
        compress_size: int,
        file_size: int,
    ) -> tuple[int, int]:
        header_offset = self._fp.tell()
        need_zip64 = file_size >= _ZIP64_LIMIT or compress_size >= _ZIP64_LIMIT
        extract_version = 45 if need_zip64 else 20
        if need_zip64:
            extra = _pack_zip64_extra(file_size, compress_size)
            lfh_csize = _ZIP64_LIMIT
            lfh_fsize = _ZIP64_LIMIT
        else:
            extra = b""
            lfh_csize = compress_size
            lfh_fsize = file_size

        header = _LFH_STRUCT.pack(
            b"PK\x03\x04",
            extract_version,
            flag_bits,
            compress_type,
            dos_time,
            dos_date,
            crc,
            lfh_csize,
            lfh_fsize,
            len(arcname_bytes),
            len(extra),
        )
        self._fp.write(header)
        self._fp.write(arcname_bytes)
        if extra:
            self._fp.write(extra)
        return header_offset, extract_version

    def add_dir(self, arcdir: str, mtime: float | None = None) -> None:
        normalized = arcdir.lstrip("/")
        if not normalized.endswith("/"):
            normalized += "/"
        if normalized in self._seen:
            return
        self._seen.add(normalized)

        arcname_bytes, utf8_flag = _encode_arcname(normalized)
        dos_time, dos_date = _mtime_to_dos_datetime(time.time() if mtime is None else mtime)
        header_offset, extract_version = self._write_local_header(
            arcname_bytes=arcname_bytes,
            flag_bits=utf8_flag,
            compress_type=zipfile.ZIP_STORED,
            dos_time=dos_time,
            dos_date=dos_date,
            crc=0,
            compress_size=0,
            file_size=0,
        )
        self._entries.append(
            _EntryRecord(
                arcname_bytes=arcname_bytes,
                flag_bits=utf8_flag,
                compress_type=zipfile.ZIP_STORED,
                dos_time=dos_time,
                dos_date=dos_date,
                crc=0,
                compress_size=0,
                file_size=0,
                external_attr=(0o40755 << 16) | 0x10,
                header_offset=header_offset,
                extract_version=extract_version,
            )
        )

    def copy_raw_entry(self, raw_fp: IO[bytes], zinfo: zipfile.ZipInfo, dst_name: str) -> None:
        normalized = dst_name.lstrip("/")
        if normalized in self._seen:
            return
        self._seen.add(normalized)

        raw_fp.seek(zinfo.header_offset)
        lfh = raw_fp.read(_LFH_STRUCT.size)
        if len(lfh) != _LFH_STRUCT.size:
            raise zipfile.BadZipFile(f"Truncated local header for {zinfo.filename}")
        sig, *_rest, fname_len, extra_len = _LFH_STRUCT.unpack(lfh)
        if sig != b"PK\x03\x04":
            raise zipfile.BadZipFile(f"Bad local header signature for {zinfo.filename}")
        data_offset = zinfo.header_offset + _LFH_STRUCT.size + fname_len + extra_len

        arcname_bytes, utf8_flag = _encode_arcname(normalized)
        # Clear bit 3 (data descriptor) because CRC & sizes are written upfront.
        flag_bits = (zinfo.flag_bits & ~0x08 & ~_UTF8_FLAG) | utf8_flag
        dos_time, dos_date = _encode_dos_datetime(zinfo.date_time)

        header_offset, extract_version = self._write_local_header(
            arcname_bytes=arcname_bytes,
            flag_bits=flag_bits,
            compress_type=zinfo.compress_type,
            dos_time=dos_time,
            dos_date=dos_date,
            crc=zinfo.CRC,
            compress_size=zinfo.compress_size,
            file_size=zinfo.file_size,
        )

        raw_fp.seek(data_offset)
        remaining = zinfo.compress_size
        while remaining > 0:
            chunk = raw_fp.read(min(_CHUNK_SIZE, remaining))
            if not chunk:
                raise zipfile.BadZipFile(f"Unexpected EOF copying {zinfo.filename}")
            self._fp.write(chunk)
            remaining -= len(chunk)

        ext_attr = zinfo.external_attr
        if ext_attr == 0:
            ext_attr = ((0o40755 << 16) | 0x10) if normalized.endswith("/") else (0o100644 << 16)

        self._entries.append(
            _EntryRecord(
                arcname_bytes=arcname_bytes,
                flag_bits=flag_bits,
                compress_type=zinfo.compress_type,
                dos_time=dos_time,
                dos_date=dos_date,
                crc=zinfo.CRC,
                compress_size=zinfo.compress_size,
                file_size=zinfo.file_size,
                external_attr=ext_attr,
                header_offset=header_offset,
                extract_version=extract_version,
            )
        )

    def add_stream_compressed(
        self,
        stream: IO[bytes],
        dst_name: str,
        dos_time: int,
        dos_date: int,
        external_attr: int,
        file_size_hint: int | None = None,
    ) -> None:
        normalized = dst_name.lstrip("/")
        if normalized in self._seen:
            return
        self._seen.add(normalized)

        arcname_bytes, utf8_flag = _encode_arcname(normalized)
        compress_type = zipfile.ZIP_STORED if file_size_hint == 0 else zipfile.ZIP_DEFLATED

        # Write a placeholder local header, stream compressed bytes, then seek back to patch sizes/CRC.
        need_zip64_placeholder = file_size_hint is not None and file_size_hint >= _ZIP64_LIMIT
        header_offset, extract_version = self._write_local_header(
            arcname_bytes=arcname_bytes,
            flag_bits=utf8_flag,
            compress_type=compress_type,
            dos_time=dos_time,
            dos_date=dos_date,
            crc=0,
            compress_size=_ZIP64_LIMIT if need_zip64_placeholder else 0,
            file_size=_ZIP64_LIMIT if need_zip64_placeholder else 0,
        )

        crc = 0
        file_size = 0
        compress_size = 0
        compressor = (
            zlib.compressobj(6, zlib.DEFLATED, -zlib.MAX_WBITS)
            if compress_type == zipfile.ZIP_DEFLATED
            else None
        )

        while True:
            chunk = stream.read(_CHUNK_SIZE)
            if not chunk:
                break
            file_size += len(chunk)
            crc = zlib.crc32(chunk, crc)
            if compressor is not None:
                out = compressor.compress(chunk)
                if out:
                    self._fp.write(out)
                    compress_size += len(out)
            else:
                self._fp.write(chunk)
                compress_size += len(chunk)

        if compressor is not None:
            tail = compressor.flush()
            if tail:
                self._fp.write(tail)
                compress_size += len(tail)

        crc &= 0xFFFFFFFF
        end_offset = self._fp.tell()

        need_zip64 = file_size >= _ZIP64_LIMIT or compress_size >= _ZIP64_LIMIT
        if need_zip64 and not need_zip64_placeholder:
            raise ValueError(f"ZIP64 overflow while streaming {dst_name}")

        self._fp.seek(header_offset)
        if need_zip64_placeholder:
            extra = _pack_zip64_extra(file_size, compress_size)
            lfh_csize = _ZIP64_LIMIT
            lfh_fsize = _ZIP64_LIMIT
        else:
            extra = b""
            lfh_csize = compress_size
            lfh_fsize = file_size

        self._fp.write(
            _LFH_STRUCT.pack(
                b"PK\x03\x04",
                extract_version,
                utf8_flag,
                compress_type,
                dos_time,
                dos_date,
                crc,
                lfh_csize,
                lfh_fsize,
                len(arcname_bytes),
                len(extra),
            )
        )
        self._fp.write(arcname_bytes)
        if extra:
            self._fp.write(extra)
        self._fp.seek(end_offset)

        self._entries.append(
            _EntryRecord(
                arcname_bytes=arcname_bytes,
                flag_bits=utf8_flag,
                compress_type=compress_type,
                dos_time=dos_time,
                dos_date=dos_date,
                crc=crc,
                compress_size=compress_size,
                file_size=file_size,
                external_attr=external_attr,
                header_offset=header_offset,
                extract_version=extract_version,
            )
        )

    def add_disk_file(self, src_path: Path, dst_name: str) -> None:
        st = src_path.stat()
        dos_time, dos_date = _mtime_to_dos_datetime(st.st_mtime)
        external_attr = (st.st_mode & 0xFFFF) << 16
        with open(src_path, "rb") as fp:
            self.add_stream_compressed(
                stream=fp,
                dst_name=dst_name,
                dos_time=dos_time,
                dos_date=dos_date,
                external_attr=external_attr,
                file_size_hint=st.st_size,
            )

    def finalize(self) -> None:
        cd_offset = self._fp.tell()
        for rec in self._entries:
            z64_vals: list[int] = []
            if rec.file_size >= _ZIP64_LIMIT:
                cd_fsize = _ZIP64_LIMIT
                z64_vals.append(rec.file_size)
            else:
                cd_fsize = rec.file_size
            if rec.compress_size >= _ZIP64_LIMIT:
                cd_csize = _ZIP64_LIMIT
                z64_vals.append(rec.compress_size)
            else:
                cd_csize = rec.compress_size
            if rec.header_offset >= _ZIP64_LIMIT:
                cd_hoff = _ZIP64_LIMIT
                z64_vals.append(rec.header_offset)
            else:
                cd_hoff = rec.header_offset

            cd_extra = _pack_zip64_extra(*z64_vals)
            extract_ver = max(rec.extract_version, 45 if cd_extra else 20)
            create_ver = (3 << 8) | extract_ver  # UNIX + version

            self._fp.write(
                _CDH_STRUCT.pack(
                    b"PK\x01\x02",
                    create_ver,
                    extract_ver,
                    rec.flag_bits,
                    rec.compress_type,
                    rec.dos_time,
                    rec.dos_date,
                    rec.crc,
                    cd_csize,
                    cd_fsize,
                    len(rec.arcname_bytes),
                    len(cd_extra),
                    0,  # comment length
                    0,  # disk number start
                    0,  # internal attrs
                    rec.external_attr,
                    cd_hoff,
                )
            )
            self._fp.write(rec.arcname_bytes)
            if cd_extra:
                self._fp.write(cd_extra)

        cd_size = self._fp.tell() - cd_offset
        entry_count = len(self._entries)

        need_zip64_eocd = (
            entry_count >= _ZIP64_COUNT_LIMIT
            or cd_size >= _ZIP64_LIMIT
            or cd_offset >= _ZIP64_LIMIT
        )
        if need_zip64_eocd:
            zip64_eocd_offset = self._fp.tell()
            self._fp.write(
                _ZIP64_EOCD_STRUCT.pack(
                    b"PK\x06\x06",
                    44,
                    (3 << 8) | 45,
                    45,
                    0,
                    0,
                    entry_count,
                    entry_count,
                    cd_size,
                    cd_offset,
                )
            )
            self._fp.write(
                _ZIP64_LOCATOR_STRUCT.pack(
                    b"PK\x06\x07",
                    0,
                    zip64_eocd_offset,
                    1,
                )
            )

        self._fp.write(
            _EOCD_STRUCT.pack(
                b"PK\x05\x06",
                0,
                0,
                min(entry_count, _ZIP64_COUNT_LIMIT),
                min(entry_count, _ZIP64_COUNT_LIMIT),
                min(cd_size, _ZIP64_LIMIT),
                min(cd_offset, _ZIP64_LIMIT),
                0,
            )
        )


class _AppendOp(argparse.Action):
    """Record CLI operations in exact invocation order."""

    def __call__(
        self,
        parser: argparse.ArgumentParser,
        namespace: argparse.Namespace,
        values: object,
        option_string: str | None = None,
    ) -> None:
        ops: list[tuple[str, tuple[str, ...]]] = getattr(namespace, "ops", None) or []
        if isinstance(values, str):
            val_tuple = (values,)
        elif isinstance(values, Sequence):
            val_tuple = tuple(str(v) for v in values)
        else:
            val_tuple = (str(values),)
        ops.append((self.dest, val_tuple))
        namespace.ops = ops


def _try_reuse_from_zip(
    assembler: _ZipAssembler,
    cache: _ZipSourceCache,
    src_path: Path,
    dst_name: str,
    reuse_zip: Path,
    reuse_member: str,
) -> bool:
    src_stat = src_path.stat()
    try:
        zip_stat = reuse_zip.stat()
    except OSError:
        return False

    # Never reuse an archive older than the source file on disk.
    if zip_stat.st_mtime_ns < src_stat.st_mtime_ns:
        return False

    try:
        zf, raw_fp = cache.open(reuse_zip)
        zinfo = zf.getinfo(reuse_member)
    except (OSError, zipfile.BadZipFile, KeyError):
        return False

    if zinfo.is_dir() or zinfo.file_size != src_stat.st_size:
        return False
    if zinfo.compress_type not in (zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED):
        return False

    assembler.copy_raw_entry(raw_fp, zinfo, dst_name)
    return True


def _copy_zip_entries(
    assembler: _ZipAssembler,
    cache: _ZipSourceCache,
    src_zip: Path,
    prefix: str,
    pattern: str,
) -> None:
    clean_prefix = "" if prefix in ("", ".") else prefix.lstrip("/")
    if clean_prefix and not clean_prefix.endswith("/"):
        clean_prefix += "/"
    if clean_prefix:
        assembler.add_dir(clean_prefix, mtime=src_zip.stat().st_mtime)

    zf, raw_fp = cache.open(src_zip)
    match_all = pattern in ("", "*")
    for zinfo in zf.infolist():
        if zinfo.is_dir():
            if not match_all:
                continue
        elif not match_all and not fnmatch.fnmatch(Path(zinfo.filename).name, pattern):
            continue

        dst_name = clean_prefix + zinfo.filename.lstrip("/")
        if zinfo.compress_type in (zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED):
            assembler.copy_raw_entry(raw_fp, zinfo, dst_name)
        else:
            dos_time, dos_date = _encode_dos_datetime(zinfo.date_time)
            ext_attr = zinfo.external_attr or (0o100644 << 16)
            with zf.open(zinfo, "r") as member_fp:
                assembler.add_stream_compressed(
                    stream=member_fp,
                    dst_name=dst_name,
                    dos_time=dos_time,
                    dos_date=dos_date,
                    external_attr=ext_attr,
                    file_size_hint=zinfo.file_size,
                )


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Assemble a ZIP archive by reusing pre-compressed streams where available."
    )
    parser.add_argument("output", type=Path, help="Output ZIP / CPKG archive path.")
    parser.add_argument(
        "--dir",
        dest="dir",
        action=_AppendOp,
        metavar="ARCDIR",
        help="Add an empty directory entry (e.g. map/).",
    )
    parser.add_argument(
        "--file",
        dest="file",
        nargs=2,
        action=_AppendOp,
        metavar=("SRC_PATH", "DST_NAME"),
        help="Compress a file from disk as DST_NAME.",
    )
    parser.add_argument(
        "--reuse-file",
        dest="reuse_file",
        nargs=4,
        action=_AppendOp,
        metavar=("SRC_PATH", "DST_NAME", "REUSE_ZIP", "REUSE_MEMBER"),
        help=(
            "Copy REUSE_MEMBER from REUSE_ZIP without recompression when REUSE_ZIP is "
            "at least as new as SRC_PATH and matches its size; otherwise compress SRC_PATH."
        ),
    )
    parser.add_argument(
        "--copy-zip",
        dest="copy_zip",
        nargs=3,
        action=_AppendOp,
        metavar=("SRC_ZIP", "PREFIX", "GLOB"),
        help=(
            "Copy entries matching GLOB (use '*' for all) from SRC_ZIP under PREFIX "
            "(use '' or '.' for root) without recompression."
        ),
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    ops: list[tuple[str, tuple[str, ...]]] = getattr(args, "ops", None) or []
    if not ops:
        print("zip-pack.py: no input entries specified", file=sys.stderr)
        return 2

    output: Path = args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = output.with_name(f".{output.name}.tmp.{os.getpid()}")

    cache = _ZipSourceCache()
    try:
        with open(tmp_path, "wb") as out_fp:
            assembler = _ZipAssembler(out_fp)
            for op, vals in ops:
                if op == "dir":
                    assembler.add_dir(vals[0])
                elif op == "file":
                    assembler.add_disk_file(Path(vals[0]), vals[1])
                elif op == "reuse_file":
                    src_path = Path(vals[0])
                    dst_name = vals[1]
                    reuse_zip = Path(vals[2]) if vals[2] else None
                    reuse_member = vals[3]
                    reused = (
                        reuse_zip is not None
                        and bool(reuse_member)
                        and _try_reuse_from_zip(
                            assembler, cache, src_path, dst_name, reuse_zip, reuse_member
                        )
                    )
                    if not reused:
                        assembler.add_disk_file(src_path, dst_name)
                elif op == "copy_zip":
                    _copy_zip_entries(assembler, cache, Path(vals[0]), vals[1], vals[2])
            assembler.finalize()
        os.replace(tmp_path, output)
    except Exception:
        if tmp_path.exists():
            tmp_path.unlink()
        raise
    finally:
        cache.close()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
