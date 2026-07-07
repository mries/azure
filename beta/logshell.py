#!/usr/bin/env python3
"""
LogShell — A bash-like environment for Linux log analysis on Windows.
Supports: .tar, .gz, .xz, .bz2, .tar.gz, .tar.xz, .tar.bz2, .zip
Built-in Linux commands: cat, less, tail, head, grep, find, ls, cd, pwd,
                         zcat, zless, wc, sort, uniq, cut, awk, sed,
                         du, stat, file, echo, which, history, clear
"""

import bz2
import gzip
import lzma
import os
import re
import shutil
import stat
import struct
import sys
import tarfile
import tempfile
import textwrap
import time
import zipfile
from collections import deque
from datetime import datetime
from pathlib import Path
from typing import Optional

# ── optional rich / prompt_toolkit ──────────────────────────────────────────
try:
    from rich.console import Console
    from rich.syntax import Syntax
    from rich.table import Table
    from rich.text import Text
    from rich import print as rprint
    HAS_RICH = True
except ImportError:
    HAS_RICH = False

try:
    from prompt_toolkit import PromptSession
    from prompt_toolkit.completion import Completer, Completion
    from prompt_toolkit.history import InMemoryHistory
    from prompt_toolkit.styles import Style
    HAS_PROMPT_TOOLKIT = True
except ImportError:
    HAS_PROMPT_TOOLKIT = False

# ── globals ─────────────────────────────────────────────────────────────────
console = Console() if HAS_RICH else None
HISTORY: deque = deque(maxlen=500)
EXTRACTED_ROOTS: list[Path] = []   # track temp extraction dirs for cleanup
PAGER_SIZE = 40                     # lines per page in less/more


# ════════════════════════════════════════════════════════════════════════════
#  ARCHIVE HANDLING
# ════════════════════════════════════════════════════════════════════════════

def detect_format(path: Path) -> str:
    """Return a format tag for the archive, or '' if unknown."""
    name = path.name.lower()
    if name.endswith((".tar.gz", ".tgz")):
        return "tar.gz"
    if name.endswith((".tar.bz2", ".tbz2")):
        return "tar.bz2"
    if name.endswith((".tar.xz", ".txz")):
        return "tar.xz"
    if name.endswith(".tar"):
        return "tar"
    if name.endswith(".gz"):
        return "gz"
    if name.endswith(".bz2"):
        return "bz2"
    if name.endswith(".xz"):
        return "xz"
    if name.endswith(".zip"):
        return "zip"
    # fall back to magic bytes
    try:
        header = path.read_bytes()[:6]
        if header[:2] == b"\x1f\x8b":
            return "gz"
        if header[:3] == b"BZh":
            return "bz2"
        if header[:6] == b"\xfd7zXZ\x00":
            return "xz"
        if header[:4] == b"PK\x03\x04":
            return "zip"
        if header[:5] == b"ustar" or (len(header) >= 5 and header[:4] == b"\x1f\x9d"):
            return "tar"
    except OSError:
        pass
    return ""


def extract_archive(archive_path: Path, dest: Path) -> Path:
    """Extract an archive to dest and return the extraction root."""
    fmt = detect_format(archive_path)
    dest.mkdir(parents=True, exist_ok=True)

    _print_info(f"Detected format: [bold cyan]{fmt or 'unknown'}[/]")
    _print_info(f"Extracting to:   [bold]{dest}[/]")

    if fmt in ("tar", "tar.gz", "tar.bz2", "tar.xz"):
        mode_map = {"tar": "r:", "tar.gz": "r:gz", "tar.bz2": "r:bz2", "tar.xz": "r:xz"}
        with tarfile.open(archive_path, mode_map[fmt]) as tf:
            members = tf.getmembers()
            _print_info(f"Members: {len(members)}")
            try:
                tf.extractall(dest, members=members, filter="data")
            except TypeError:
                tf.extractall(dest, members=members)  # noqa: S202

    elif fmt == "gz":
        out_name = archive_path.stem  # strip .gz
        out_path = dest / out_name
        with gzip.open(archive_path, "rb") as f_in, open(out_path, "wb") as f_out:
            shutil.copyfileobj(f_in, f_out)

    elif fmt == "bz2":
        out_name = archive_path.stem
        out_path = dest / out_name
        with bz2.open(archive_path, "rb") as f_in, open(out_path, "wb") as f_out:
            shutil.copyfileobj(f_in, f_out)

    elif fmt == "xz":
        out_name = archive_path.stem
        out_path = dest / out_name
        with lzma.open(archive_path, "rb") as f_in, open(out_path, "wb") as f_out:
            shutil.copyfileobj(f_in, f_out)

    elif fmt == "zip":
        with zipfile.ZipFile(archive_path, "r") as zf:
            _print_info(f"Members: {len(zf.namelist())}")
            zf.extractall(dest)

    else:
        raise ValueError(f"Unsupported or unrecognised archive format: {archive_path}")

    _print_ok(f"Extraction complete → {dest}")
    return dest


# ════════════════════════════════════════════════════════════════════════════
#  DISPLAY HELPERS
# ════════════════════════════════════════════════════════════════════════════

def _print_info(msg: str):
    if HAS_RICH:
        console.print(f"[dim]→[/] {msg}")
    else:
        # strip rich markup
        print("→ " + re.sub(r"\[.*?\]", "", msg))

def _print_ok(msg: str):
    if HAS_RICH:
        console.print(f"[green]✔[/] {msg}")
    else:
        print("✔ " + re.sub(r"\[.*?\]", "", msg))

def _print_err(msg: str):
    if HAS_RICH:
        console.print(f"[red]✘ {msg}[/]")
    else:
        print("✘ " + re.sub(r"\[.*?\]", "", msg), file=sys.stderr)

def _print_warn(msg: str):
    if HAS_RICH:
        console.print(f"[yellow]⚠ {msg}[/]")
    else:
        print("⚠ " + re.sub(r"\[.*?\]", "", msg))

def plain(text: str) -> str:
    """Strip rich markup for fallback printing."""
    return re.sub(r"\[.*?\]", "", text)


def pager(lines: list[str], title: str = ""):
    """Simple terminal pager (space/q)."""
    total = len(lines)
    pos = 0
    while pos < total:
        chunk = lines[pos: pos + PAGER_SIZE]
        for l in chunk:
            print(l)
        pos += PAGER_SIZE
        if pos >= total:
            break
        try:
            key = input(f"-- MORE ({pos}/{total}) [Space=next page, q=quit] -- ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            break
        if key == "q":
            break


# ════════════════════════════════════════════════════════════════════════════
#  FILE READING HELPERS
# ════════════════════════════════════════════════════════════════════════════

def _open_file(path: Path):
    """Open a file, transparently decompressing .gz / .bz2 / .xz."""
    name = path.name.lower()
    if name.endswith(".gz"):
        return gzip.open(path, "rt", errors="replace")
    if name.endswith(".bz2"):
        return bz2.open(path, "rt", errors="replace")
    if name.endswith(".xz"):
        return lzma.open(path, "rt", errors="replace")
    return open(path, "r", errors="replace")


def _read_lines(path: Path) -> list[str]:
    with _open_file(path) as f:
        return f.readlines()


# ════════════════════════════════════════════════════════════════════════════
#  BUILT-IN COMMANDS
# ════════════════════════════════════════════════════════════════════════════

class Shell:
    def __init__(self, start_dir: Path):
        self.cwd = start_dir.resolve()
        self.env: dict[str, str] = dict(os.environ)
        self.aliases: dict[str, str] = {
            "ll": "ls -l",
            "la": "ls -la",
            "l": "ls -la",
        }

    # ── path resolution ──────────────────────────────────────────────────

    def resolve(self, arg: str) -> Path:
        # Normalise Windows backslashes → forward slashes before parsing
        arg = arg.replace("\\", "/")
        p = Path(arg)
        if not p.is_absolute():
            p = self.cwd / p
        return p.resolve()

    # ── argument parser helpers ───────────────────────────────────────────

    @staticmethod
    def _parse_flags(args: list[str], flags: str) -> tuple[dict, list[str]]:
        """Very simple flag parser: flags is a string of single-char flags."""
        result = {f: False for f in flags}
        rest = []
        i = 0
        while i < len(args):
            a = args[i]
            if a.startswith("-") and not a.startswith("--") and len(a) > 1:
                for c in a[1:]:
                    if c in result:
                        result[c] = True
                    # ignore unknown flags silently
            elif a.startswith("--"):
                pass  # skip long opts for now
            else:
                rest.append(a)
            i += 1
        return result, rest

    # ════════════════════════════════════════════════════════════════════
    #  COMMAND IMPLEMENTATIONS
    # ════════════════════════════════════════════════════════════════════

    def cmd_pwd(self, args):
        print(self.cwd.as_posix())

    def cmd_cd(self, args):
        if not args:
            # cd with no args → go to extraction root if available
            target = EXTRACTED_ROOTS[0] if EXTRACTED_ROOTS else Path.home()
        else:
            raw = args[0]
            if raw == "-":
                _print_warn("cd - not supported")
                return
            target = self.resolve(raw)
        if not target.exists():
            _print_err(f"cd: {target}: No such file or directory")
            return
        if not target.is_dir():
            _print_err(f"cd: {target}: Not a directory")
            return
        self.cwd = target

    def cmd_ls(self, args):
        flags, paths = self._parse_flags(args, "lahHrRt1")
        show_hidden = flags["a"] or flags["A"] if "A" in flags else flags["a"]
        long_fmt = flags["l"] or flags["h"]
        reverse = flags["r"]
        recurse = flags["R"]
        sort_time = flags["t"]

        targets = [self.resolve(p) for p in paths] if paths else [self.cwd]

        for target in targets:
            if len(targets) > 1:
                print(f"\n{target.as_posix()}:")
            if not target.exists():
                _print_err(f"ls: {target}: No such file or directory")
                continue
            if target.is_file():
                entries = [target]
                parent = target.parent
            else:
                parent = target
                try:
                    entries = list(target.iterdir())
                except PermissionError:
                    _print_err(f"ls: {target}: Permission denied")
                    continue

            if not show_hidden:
                entries = [e for e in entries if not e.name.startswith(".")]

            if sort_time:
                entries.sort(key=lambda e: e.stat().st_mtime, reverse=not reverse)
            else:
                entries.sort(key=lambda e: e.name.lower(), reverse=reverse)

            if long_fmt:
                if HAS_RICH:
                    table = Table(show_header=False, box=None, padding=(0, 1))
                    for e in entries:
                        s = e.stat()
                        mode = stat.filemode(s.st_mode)
                        size = _human(s.st_size) if flags["h"] else str(s.st_size)
                        mtime = datetime.fromtimestamp(s.st_mtime).strftime("%b %d %H:%M")
                        color = "bold blue" if e.is_dir() else ("bold cyan" if e.name.endswith((".gz", ".bz2", ".xz", ".tar", ".zip")) else "default")
                        name = e.name + ("/" if e.is_dir() else "")
                        table.add_row(mode, size, mtime, Text(name, style=color))
                    console.print(table)
                else:
                    for e in entries:
                        s = e.stat()
                        mode = stat.filemode(s.st_mode)
                        size = str(s.st_size)
                        mtime = datetime.fromtimestamp(s.st_mtime).strftime("%b %d %H:%M")
                        name = e.name + ("/" if e.is_dir() else "")
                        print(f"{mode}  {size:>10}  {mtime}  {name}")
            else:
                names = []
                for e in entries:
                    name = e.name + ("/" if e.is_dir() else "")
                    names.append(name)
                # columnar output
                if names:
                    col_w = max(len(n) for n in names) + 2
                    term_w = shutil.get_terminal_size((80, 24)).columns
                    cols = max(1, term_w // col_w)
                    for i, name in enumerate(names):
                        end = "\n" if (i + 1) % cols == 0 or i == len(names) - 1 else ""
                        if HAS_RICH:
                            style = "bold blue" if name.endswith("/") else "default"
                            console.print(Text(name.ljust(col_w), style=style), end=end)
                        else:
                            print(name.ljust(col_w), end=end)

    def cmd_cat(self, args):
        flags, paths = self._parse_flags(args, "n")
        show_num = flags["n"]
        if not paths:
            _print_warn("cat: no files specified")
            return
        for p_str in paths:
            path = self.resolve(p_str)
            if not path.exists():
                _print_err(f"cat: {path}: No such file or directory")
                continue
            if path.is_dir():
                _print_err(f"cat: {path}: Is a directory")
                continue
            try:
                lines = _read_lines(path)
                for i, line in enumerate(lines, 1):
                    out = f"{i:6}\t{line}" if show_num else line
                    print(out, end="" if line.endswith("\n") else "\n")
            except Exception as e:
                _print_err(f"cat: {path}: {e}")

    def cmd_less(self, args):
        """Paged file viewer."""
        _, paths = self._parse_flags(args, "")
        if not paths:
            _print_warn("less: no files specified")
            return
        for p_str in paths:
            path = self.resolve(p_str)
            if not path.exists():
                _print_err(f"less: {path}: No such file or directory")
                return
            try:
                lines = [l.rstrip("\n") for l in _read_lines(path)]
                pager(lines, title=path.name)
            except Exception as e:
                _print_err(f"less: {e}")

    cmd_more = cmd_less

    def cmd_head(self, args):
        n = 10
        paths = []
        i = 0
        while i < len(args):
            a = args[i]
            if a in ("-n", "--lines") and i + 1 < len(args):
                n = int(args[i + 1]); i += 2; continue
            elif a.startswith("-") and a[1:].isdigit():
                n = int(a[1:]); i += 1; continue
            else:
                paths.append(a)
            i += 1
        if not paths:
            _print_warn("head: no files specified")
            return
        for p_str in paths:
            path = self.resolve(p_str)
            if not path.exists():
                _print_err(f"head: {path}: No such file or directory"); continue
            try:
                lines = _read_lines(path)
                if len(paths) > 1:
                    print(f"==> {path.name} <==")
                for line in lines[:n]:
                    print(line, end="" if line.endswith("\n") else "\n")
            except Exception as e:
                _print_err(f"head: {e}")

    def cmd_tail(self, args):
        n = 10
        follow = False
        paths = []
        i = 0
        while i < len(args):
            a = args[i]
            if a in ("-n", "--lines") and i + 1 < len(args):
                n = int(args[i + 1]); i += 2; continue
            elif a.startswith("-") and a[1:].isdigit():
                n = int(a[1:]); i += 1; continue
            elif a in ("-f", "--follow"):
                follow = True; i += 1; continue
            else:
                paths.append(a)
            i += 1
        if not paths:
            _print_warn("tail: no files specified")
            return
        for p_str in paths:
            path = self.resolve(p_str)
            if not path.exists():
                _print_err(f"tail: {path}: No such file or directory"); continue
            try:
                lines = _read_lines(path)
                if len(paths) > 1:
                    print(f"==> {path.name} <==")
                for line in lines[-n:]:
                    print(line, end="" if line.endswith("\n") else "\n")
                if follow:
                    _print_info(f"Following {path.name} — Ctrl+C to stop")
                    try:
                        with _open_file(path) as f:
                            f.seek(0, 2)
                            while True:
                                line = f.readline()
                                if line:
                                    print(line, end="")
                                else:
                                    time.sleep(0.2)
                    except KeyboardInterrupt:
                        print()
            except Exception as e:
                _print_err(f"tail: {e}")

    def cmd_grep(self, args):
        flags, rest = self._parse_flags(args, "invrElc")
        ignore_case = flags["i"]
        line_num = flags["n"]
        invert = flags["v"]
        recurse = flags["r"] or flags["R"] if "R" in flags else flags["r"]
        extended = flags["E"]
        count_only = flags["c"]
        color = flags["l"]  # reuse -l as "filenames only" like grep -l

        if not rest:
            _print_warn("grep: usage: grep [flags] PATTERN [FILE...]")
            return

        pattern_str = rest[0]
        paths = rest[1:]

        re_flags = re.IGNORECASE if ignore_case else 0
        try:
            pat = re.compile(pattern_str, re_flags)
        except re.error as e:
            _print_err(f"grep: invalid regex: {e}")
            return

        def _grep_file(path: Path, show_filename: bool):
            try:
                lines = _read_lines(path)
            except Exception as e:
                _print_err(f"grep: {path}: {e}")
                return
            match_count = 0
            for i, line in enumerate(lines, 1):
                raw = line.rstrip("\n")
                matched = bool(pat.search(raw))
                if invert:
                    matched = not matched
                if matched:
                    match_count += 1
                    if not count_only:
                        parts = []
                        if show_filename:
                            parts.append(f"\033[35m{path.name}\033[0m:")
                        if line_num:
                            parts.append(f"\033[32m{i}\033[0m:")
                        # highlight match in red
                        highlighted = pat.sub(lambda m: f"\033[1;31m{m.group()}\033[0m", raw) if not invert else raw
                        parts.append(highlighted)
                        print("".join(parts))
            if count_only:
                prefix = f"{path.name}:" if show_filename else ""
                print(f"{prefix}{match_count}")

        def _collect(p: Path) -> list[Path]:
            if p.is_file():
                return [p]
            if recurse and p.is_dir():
                return [f for f in p.rglob("*") if f.is_file()]
            return []

        if not paths:
            _print_warn("grep: reading from stdin not supported; provide file paths")
            return

        file_list: list[Path] = []
        for p_str in paths:
            file_list.extend(_collect(self.resolve(p_str)))

        show_fn = len(file_list) > 1
        for f in file_list:
            _grep_file(f, show_fn)

    def cmd_find(self, args):
        """find PATH [options]"""
        if not args:
            args = ["."]

        root = self.resolve(args[0])
        rest = args[1:]

        name_pat = None
        type_filter = None
        mtime_days = None
        size_filter = None
        maxdepth = None

        i = 0
        while i < len(rest):
            a = rest[i]
            if a == "-name" and i + 1 < len(rest):
                name_pat = re.compile(
                    "^" + re.escape(rest[i + 1]).replace(r"\*", ".*").replace(r"\?", ".") + "$",
                    re.IGNORECASE,
                )
                i += 2
            elif a == "-type" and i + 1 < len(rest):
                type_filter = rest[i + 1]
                i += 2
            elif a == "-mtime" and i + 1 < len(rest):
                mtime_days = int(rest[i + 1])
                i += 2
            elif a == "-maxdepth" and i + 1 < len(rest):
                maxdepth = int(rest[i + 1])
                i += 2
            else:
                i += 1

        now = time.time()

        def _walk(path: Path, depth: int):
            if maxdepth is not None and depth > maxdepth:
                return
            try:
                entries = list(path.iterdir())
            except PermissionError:
                return
            for e in entries:
                ok = True
                if name_pat and not name_pat.match(e.name):
                    ok = False
                if type_filter == "f" and not e.is_file():
                    ok = False
                if type_filter == "d" and not e.is_dir():
                    ok = False
                if mtime_days is not None:
                    age = (now - e.stat().st_mtime) / 86400
                    if abs(age - abs(mtime_days)) > 1:
                        ok = False
                if ok:
                    print(e.as_posix())
                if e.is_dir():
                    _walk(e, depth + 1)

        _walk(root, 0)

    def cmd_wc(self, args):
        flags, paths = self._parse_flags(args, "lwc")
        if not paths:
            _print_warn("wc: no files specified")
            return
        for p_str in paths:
            path = self.resolve(p_str)
            if not path.exists():
                _print_err(f"wc: {path}: No such file or directory"); continue
            try:
                lines = _read_lines(path)
                lc = len(lines)
                wc = sum(len(l.split()) for l in lines)
                cc = sum(len(l) for l in lines)
                if flags["l"]:
                    print(f"{lc:7} {path.name}")
                elif flags["w"]:
                    print(f"{wc:7} {path.name}")
                elif flags["c"]:
                    print(f"{cc:7} {path.name}")
                else:
                    print(f"{lc:7} {wc:7} {cc:7} {path.name}")
            except Exception as e:
                _print_err(f"wc: {e}")

    def cmd_sort(self, args):
        flags, paths = self._parse_flags(args, "rnuk")
        if not paths:
            _print_warn("sort: no files specified")
            return
        lines = []
        for p_str in paths:
            path = self.resolve(p_str)
            if not path.exists():
                _print_err(f"sort: {path}: No such file or directory"); continue
            lines.extend(l.rstrip("\n") for l in _read_lines(path))

        if flags["n"]:
            def key_fn(l):
                try: return float(l.split()[0])
                except: return 0.0
        else:
            key_fn = str.lower

        result = sorted(set(lines) if flags["u"] else lines, key=key_fn, reverse=flags["r"])
        for l in result:
            print(l)

    def cmd_uniq(self, args):
        flags, paths = self._parse_flags(args, "cd")
        if not paths:
            _print_warn("uniq: no files specified")
            return
        for p_str in paths:
            path = self.resolve(p_str)
            if not path.exists():
                _print_err(f"uniq: {path}: No such file or directory"); continue
            lines = [l.rstrip("\n") for l in _read_lines(path)]
            from itertools import groupby
            for key, group in groupby(lines):
                items = list(group)
                if flags["c"]:
                    print(f"{len(items):7} {key}")
                elif flags["d"]:
                    if len(items) > 1:
                        print(key)
                else:
                    print(key)

    def cmd_cut(self, args):
        delim = "\t"
        fields = None
        chars = None
        paths = []
        i = 0
        while i < len(args):
            a = args[i]
            if a in ("-d", "--delimiter") and i + 1 < len(args):
                delim = args[i + 1]; i += 2
            elif a.startswith("-d"):
                delim = a[2:]; i += 1
            elif a in ("-f", "--fields") and i + 1 < len(args):
                fields = [int(x) - 1 for x in args[i + 1].split(",")]; i += 2
            elif a.startswith("-f"):
                fields = [int(x) - 1 for x in a[2:].split(",")]; i += 1
            elif a in ("-c", "--characters") and i + 1 < len(args):
                chars = [int(x) - 1 for x in args[i + 1].split(",")]; i += 2
            else:
                paths.append(a); i += 1

        for p_str in paths:
            path = self.resolve(p_str)
            if not path.exists():
                _print_err(f"cut: {path}: No such file or directory"); continue
            for line in _read_lines(path):
                line = line.rstrip("\n")
                if chars is not None:
                    print("".join(line[c] for c in chars if c < len(line)))
                elif fields is not None:
                    parts = line.split(delim)
                    print(delim.join(parts[f] for f in fields if f < len(parts)))
                else:
                    print(line)

    def cmd_awk(self, args):
        """Minimal awk: supports {print $N} and /pattern/{print $N}."""
        if not args:
            _print_warn("awk: no program specified"); return
        program = args[0]
        paths = args[1:]
        sep = " "

        # parse -F flag
        if program.startswith("-F"):
            sep = program[2:]
            if not paths:
                _print_warn("awk: no program"); return
            program = paths[0]; paths = paths[1:]

        def _run_program(line: str):
            line = line.rstrip("\n")
            fields = line.split(sep)
            fields_full = [""] + fields  # $0 is full line, $1..$N are parts

            def sub_fields(expr: str) -> str:
                expr = expr.replace("$0", line)
                for idx in range(len(fields_full) - 1, 0, -1):
                    expr = expr.replace(f"${idx}", fields_full[idx] if idx < len(fields_full) else "")
                return expr

            # Handle pattern/action blocks
            blocks = re.findall(r'(/[^/]*/|BEGIN|END)?\s*\{([^}]*)\}', program)
            if not blocks:
                # bare {action}
                m = re.match(r'\{(.+)\}', program.strip())
                if m:
                    blocks = [("", m.group(1))]

            if not blocks:
                # try simple print
                blocks = [("", program)]

            for pat, action in blocks:
                should_run = True
                if pat and pat.startswith("/") and pat.endswith("/"):
                    pat_re = pat[1:-1]
                    should_run = bool(re.search(pat_re, line))
                if should_run:
                    action = action.strip()
                    if action.startswith("print"):
                        expr = action[5:].strip()
                        if not expr:
                            print(line)
                        else:
                            print(sub_fields(expr))

        for p_str in paths:
            path = self.resolve(p_str)
            if not path.exists():
                _print_err(f"awk: {path}: No such file or directory"); continue
            for line in _read_lines(path):
                _run_program(line)

    def cmd_sed(self, args):
        """Minimal sed: supports s/pattern/replacement/[g][i] and /pattern/d."""
        if not args:
            _print_warn("sed: no expression"); return
        i = 0
        expr = None
        paths = []
        while i < len(args):
            a = args[i]
            if a in ("-e", "-n") and i + 1 < len(args):
                expr = args[i + 1]; i += 2
            elif a.startswith("-e"):
                expr = a[2:]; i += 1
            elif not a.startswith("-") and expr is None:
                expr = a; i += 1
            else:
                paths.append(a); i += 1

        if expr is None:
            _print_warn("sed: no expression"); return

        # parse s/pattern/replacement/flags
        s_match = re.match(r's([/|#!,])(.+?)\1(.*?)\1([gi]*)', expr)
        d_match = re.match(r'/(.+?)/d', expr)
        p_match = re.match(r'/(.+?)/p', expr)

        for p_str in paths:
            path = self.resolve(p_str)
            if not path.exists():
                _print_err(f"sed: {path}: No such file or directory"); continue
            for line in _read_lines(path):
                line = line.rstrip("\n")
                if s_match:
                    _, pattern, repl, flags = s_match.groups()
                    re_flags = re.IGNORECASE if "i" in flags else 0
                    count = 0 if "g" in flags else 1
                    line = re.sub(pattern, repl, line, count=count, flags=re_flags)
                    print(line)
                elif d_match:
                    if not re.search(d_match.group(1), line):
                        print(line)
                elif p_match:
                    if re.search(p_match.group(1), line):
                        print(line)
                else:
                    print(line)

    def cmd_du(self, args):
        flags, paths = self._parse_flags(args, "sh")
        human = flags["h"]
        summ = flags["s"]
        targets = [self.resolve(p) for p in paths] if paths else [self.cwd]
        for t in targets:
            if not t.exists():
                _print_err(f"du: {t}: No such file or directory"); continue
            total = sum(f.stat().st_size for f in (t.rglob("*") if t.is_dir() else [t]) if f.is_file())
            size = _human(total) if human else str(total)
            print(f"{size}\t{t.as_posix()}")

    def cmd_stat(self, args):
        for p_str in args:
            path = self.resolve(p_str)
            if not path.exists():
                _print_err(f"stat: {path}: No such file or directory"); continue
            s = path.stat()
            print(f"  File: {path}")
            print(f"  Size: {s.st_size}\tBlocks: {getattr(s,'st_blocks',0)}")
            print(f"  Mode: {stat.filemode(s.st_mode)}")
            print(f"Modify: {datetime.fromtimestamp(s.st_mtime)}")
            print(f"Access: {datetime.fromtimestamp(s.st_atime)}")

    def cmd_file(self, args):
        for p_str in args:
            path = self.resolve(p_str)
            if not path.exists():
                _print_err(f"file: {path}: No such file or directory"); continue
            if path.is_dir():
                print(f"{path.name}: directory"); continue
            try:
                header = path.read_bytes()[:16]
            except OSError:
                print(f"{path.name}: cannot read"); continue
            if header[:2] == b"\x1f\x8b":
                kind = "gzip compressed data"
            elif header[:3] == b"BZh":
                kind = "bzip2 compressed data"
            elif header[:6] == b"\xfd7zXZ\x00":
                kind = "XZ compressed data"
            elif header[:4] == b"PK\x03\x04":
                kind = "Zip archive data"
            elif b"ustar" in header[:512]:
                kind = "POSIX tar archive"
            else:
                try:
                    path.read_text(errors="strict")
                    kind = "ASCII text"
                except UnicodeDecodeError:
                    kind = "data"
            print(f"{path.name}: {kind}")

    def cmd_echo(self, args):
        print(" ".join(args))

    def cmd_clear(self, args):
        os.system("cls" if sys.platform == "win32" else "clear")

    def cmd_history(self, args):
        for i, h in enumerate(HISTORY, 1):
            print(f"{i:4}  {h}")

    def cmd_which(self, args):
        built_ins = set(COMMANDS.keys())
        for a in args:
            if a in built_ins:
                print(f"{a}: shell built-in")
            else:
                print(f"{a}: not found")

    def cmd_open(self, args):
        """Open / extract an archive and cd into it."""
        if not args:
            _print_warn("open: specify an archive file")
            return
        path = self.resolve(args[0])
        if not path.exists():
            _print_err(f"open: {path}: No such file or directory")
            return
        tmp = Path(tempfile.mkdtemp(prefix="logshell_"))
        EXTRACTED_ROOTS.append(tmp)
        try:
            extract_archive(path, tmp)
            self.cwd = tmp
            _print_ok(f"Working directory set to {tmp}")
        except Exception as e:
            _print_err(f"open: {e}")

    def cmd_lsarchive(self, args):
        """List contents of an archive without extracting."""
        if not args:
            _print_warn("lsarchive: specify an archive file")
            return
        path = self.resolve(args[0])
        fmt = detect_format(path)
        try:
            if fmt in ("tar", "tar.gz", "tar.bz2", "tar.xz"):
                mode_map = {"tar": "r:", "tar.gz": "r:gz", "tar.bz2": "r:bz2", "tar.xz": "r:xz"}
                with tarfile.open(path, mode_map[fmt]) as tf:
                    for m in tf.getmembers():
                        size = _human(m.size)
                        print(f"{size:>8}  {m.name}")
            elif fmt == "zip":
                with zipfile.ZipFile(path, "r") as zf:
                    for info in zf.infolist():
                        size = _human(info.file_size)
                        print(f"{size:>8}  {info.filename}")
            else:
                _print_warn(f"lsarchive: cannot list {fmt or 'unknown'} format")
        except Exception as e:
            _print_err(f"lsarchive: {e}")

    def cmd_zcat(self, args):
        """cat for compressed files."""
        self.cmd_cat(args)  # _open_file handles transparent decompression

    def cmd_zless(self, args):
        """less for compressed files."""
        self.cmd_less(args)

    def cmd_zgrep(self, args):
        """grep inside compressed files."""
        self.cmd_grep(args)

    def cmd_help(self, args):
        if HAS_RICH:
            table = Table(title="LogShell Built-in Commands", show_lines=True)
            table.add_column("Command", style="bold cyan")
            table.add_column("Description")
            for cmd, desc in HELP_TEXT.items():
                table.add_row(cmd, desc)
            console.print(table)
        else:
            print("\nLogShell Built-in Commands")
            print("-" * 40)
            for cmd, desc in HELP_TEXT.items():
                print(f"  {cmd:<14} {desc}")
            print()

    def cmd_exit(self, args):
        raise SystemExit(0)

    cmd_quit = cmd_exit


# ════════════════════════════════════════════════════════════════════════════
#  COMMAND TABLE & HELP
# ════════════════════════════════════════════════════════════════════════════

COMMANDS: dict = {}          # populated after Shell class is defined
HELP_TEXT: dict[str, str] = {
    "open":       "open <archive>   — extract archive and cd into it",
    "lsarchive":  "lsarchive <file> — list contents of archive without extracting",
    "ls":         "ls [-lahrt]      — list directory",
    "cd":         "cd [dir]         — change directory",
    "pwd":        "pwd              — print working directory",
    "cat":        "cat [-n] <file>  — print file contents",
    "less/more":  "less <file>      — paged viewer",
    "head":       "head [-n N] <f>  — first N lines (default 10)",
    "tail":       "tail [-n N -f]   — last N lines / follow",
    "grep":       "grep [-invrE] PATTERN [FILE...] — search text",
    "find":       "find [PATH] [-name -type -mtime -maxdepth]",
    "wc":         "wc [-lwc] <file> — word/line/char count",
    "sort":       "sort [-nru]      — sort lines",
    "uniq":       "uniq [-cd]       — filter duplicate lines",
    "cut":        "cut -d DELIM -f FIELDS <file>",
    "awk":        "awk 'PROG' <file> — minimal awk (print, /pat/)",
    "sed":        "sed 's/pat/rep/g' <file> — minimal sed",
    "du":         "du [-sh]         — disk usage",
    "stat":       "stat <file>      — file metadata",
    "file":       "file <f>         — detect file type",
    "zcat/zless": "zcat/zless       — cat/less for .gz .bz2 .xz",
    "zgrep":      "zgrep            — grep inside compressed files",
    "echo":       "echo <text>",
    "clear":      "clear            — clear screen",
    "history":    "history          — command history",
    "which":      "which <cmd>",
    "exit":       "exit / quit      — quit LogShell",
    "help":       "help             — this message",
}

def _build_commands(shell: "Shell") -> dict:
    return {
        name[4:]: getattr(shell, name)
        for name in dir(shell)
        if name.startswith("cmd_")
    }


# ════════════════════════════════════════════════════════════════════════════
#  COMPLETER
# ════════════════════════════════════════════════════════════════════════════

class ShellCompleter(Completer):
    def __init__(self, shell: Shell):
        self.shell = shell

    def get_completions(self, document, complete_event):
        text = document.text_before_cursor
        words = text.split()
        if not words or (len(words) == 1 and not text.endswith(" ")):
            # complete command
            prefix = words[0] if words else ""
            for cmd in sorted(COMMANDS.keys()):
                if cmd.startswith(prefix):
                    yield Completion(cmd, start_position=-len(prefix))
        else:
            # complete path
            partial = words[-1] if not text.endswith(" ") else ""
            base = self.shell.cwd if not partial else (self.shell.cwd / partial).parent
            stem = Path(partial).name if partial else ""
            try:
                for entry in sorted(base.iterdir(), key=lambda e: e.name):
                    if entry.name.startswith(stem):
                        suffix = "/" if entry.is_dir() else ""
                        yield Completion(entry.name[len(stem):] + suffix, start_position=0)
            except OSError:
                pass


# ════════════════════════════════════════════════════════════════════════════
#  UTILITY
# ════════════════════════════════════════════════════════════════════════════

def _human(size: int) -> str:
    for unit in ("B", "K", "M", "G", "T"):
        if size < 1024:
            return f"{size:.1f}{unit}"
        size /= 1024
    return f"{size:.1f}P"


def _pipe_split(cmd_str: str) -> list[str]:
    """Split on | but not inside quotes."""
    parts, cur, in_q = [], [], False
    for ch in cmd_str:
        if ch == '"':
            in_q = not in_q
        if ch == "|" and not in_q:
            parts.append("".join(cur).strip())
            cur = []
        else:
            cur.append(ch)
    parts.append("".join(cur).strip())
    return parts


def _tokenise(cmd_str: str) -> list[str]:
    """Shell-like tokeniser respecting double quotes."""
    import shlex
    try:
        return shlex.split(cmd_str)
    except ValueError:
        return cmd_str.split()


# ════════════════════════════════════════════════════════════════════════════
#  BANNER
# ════════════════════════════════════════════════════════════════════════════

BANNER = r"""
  _                  ___ _          _ _
 | |   ___  __ _ / __| |_   ___| | |
 | |__/ _ \/ _` |\__ \ ' \ / -_) | |
 |____\___/\__, ||___/_||_|\___|_|_|
           |___/
  Linux Log Analysis Shell  •  Windows Edition
"""

def print_banner():
    if HAS_RICH:
        console.print(f"[bold cyan]{BANNER}[/]")
        console.print(f"  [dim]rich[/] [green]✔[/]  [dim]prompt_toolkit[/] {'[green]✔[/]' if HAS_PROMPT_TOOLKIT else '[red]✘[/]'}")
        console.print(f"  Type [bold]help[/] for commands, [bold]open <archive>[/] to load a log bundle.\n")
    else:
        print(BANNER)
        print("  Type 'help' for commands, 'open <archive>' to load a log bundle.\n")


# ════════════════════════════════════════════════════════════════════════════
#  MAIN LOOP
# ════════════════════════════════════════════════════════════════════════════

def make_prompt(shell: Shell) -> str:
    try:
        rel = shell.cwd.relative_to(EXTRACTED_ROOTS[0]) if EXTRACTED_ROOTS else shell.cwd
        return f"[logs:{rel.as_posix()}]$ "
    except ValueError:
        return f"[{shell.cwd.name}]$ "


def run(shell: Shell):
    global COMMANDS
    COMMANDS = _build_commands(shell)

    if HAS_PROMPT_TOOLKIT:
        style = Style.from_dict({"prompt": "ansigreen bold"})
        session = PromptSession(
            completer=ShellCompleter(shell),
            history=InMemoryHistory(),
            style=style,
        )
        get_input = lambda p: session.prompt(p)
    else:
        get_input = input

    while True:
        try:
            prompt = make_prompt(shell)
            line = get_input(prompt).strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if not line:
            continue

        # alias expansion
        for alias, expansion in shell.aliases.items():
            if line == alias or line.startswith(alias + " "):
                line = expansion + line[len(alias):]
                break

        HISTORY.append(line)

        # variable substitution ($VAR)
        line = re.sub(r'\$(\w+)', lambda m: shell.env.get(m.group(1), ""), line)

        # pipe handling (simple: only built-ins)
        segments = _pipe_split(line)
        if len(segments) > 1:
            # capture stdout of each segment and pipe into next
            import io, contextlib
            buf = None
            for seg in segments:
                tokens = _tokenise(seg)
                if not tokens:
                    continue
                cmd_name = tokens[0].lower()
                cmd_args = tokens[1:]
                fn = COMMANDS.get(cmd_name)
                if fn is None:
                    _print_warn(f"pipe: unknown command '{cmd_name}'")
                    buf = None
                    break
                out_buf = io.StringIO()
                with contextlib.redirect_stdout(out_buf):
                    try:
                        fn(cmd_args)
                    except SystemExit:
                        raise
                    except Exception as e:
                        _print_err(f"{cmd_name}: {e}")
                buf = out_buf.getvalue()
            if buf is not None:
                print(buf, end="")
            continue

        # single command
        tokens = _tokenise(line)
        if not tokens:
            continue

        cmd_name = tokens[0].lower()
        cmd_args = tokens[1:]

        # handle variable assignment
        if "=" in cmd_name and not cmd_name.startswith("-"):
            k, _, v = cmd_name.partition("=")
            shell.env[k] = v
            continue

        fn = COMMANDS.get(cmd_name)
        if fn is None:
            _print_err(f"{cmd_name}: command not found  (type 'help' for built-ins)")
            continue

        try:
            fn(cmd_args)
        except SystemExit:
            break
        except KeyboardInterrupt:
            print()
        except Exception as e:
            _print_err(f"{cmd_name}: {e}")


# ════════════════════════════════════════════════════════════════════════════
#  ENTRY POINT
# ════════════════════════════════════════════════════════════════════════════

def main():
    print_banner()

    start_dir = Path.cwd()

    # If an archive was passed as CLI arg, extract it first
    if len(sys.argv) > 1:
        archive = Path(sys.argv[1])
        if archive.exists():
            tmp = Path(tempfile.mkdtemp(prefix="logshell_"))
            EXTRACTED_ROOTS.append(tmp)
            try:
                extract_archive(archive, tmp)
                start_dir = tmp
            except Exception as e:
                _print_err(f"Could not open archive: {e}")
        else:
            _print_err(f"File not found: {archive}")

    shell = Shell(start_dir)
    try:
        run(shell)
    finally:
        # Cleanup temp dirs
        for d in EXTRACTED_ROOTS:
            try:
                shutil.rmtree(d, ignore_errors=True)
            except Exception:
                pass
        _print_info("Cleaned up temporary files. Goodbye.")


if __name__ == "__main__":
    main()