# Copyright (C) 2020 FireEye, Inc. All Rights Reserved.
# Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
# You may obtain a copy of the License at: [package root]/LICENSE.txt
# Unless required by applicable law or agreed to in writing, software distributed under the License
#  is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and limitations under the License.

import sys
import builtins

from capa.features.file import Import
from capa.features.insn import API

MIN_STACKSTRING_LEN = 8


def xor_static(data, i):
    if sys.version_info >= (3, 0):
        return bytes(c ^ i for c in data)
    else:
        return "".join(chr(ord(c) ^ i) for c in data)


def is_aw_function(function_name):
    """
    is the given function name an A/W function?
    these are variants of functions that, on Windows, accept either a narrow or wide string.
    """
    if len(function_name) < 2:
        return False

    # last character should be 'A' or 'W'
    if function_name[-1] not in ("A", "W"):
        return False

    # second to last character should be lowercase letter
    return "a" <= function_name[-2] <= "z" or "0" <= function_name[-2] <= "9"


def generate_api_features(apiname, va):
    """
    for a given function name and address, generate API names.
    we over-generate features to make matching easier.
    these include:
      - kernel32.CreateFileA
      - kernel32.CreateFile
      - CreateFileA
      - CreateFile
    """
    # (kernel32.CreateFileA, 0x401000)
    yield API(apiname), va

    if is_aw_function(apiname):
        # (kernel32.CreateFile, 0x401000)
        yield API(apiname[:-1]), va

    if "." in apiname:
        modname, impname = apiname.split(".")
        # strip modname to support importname-only matching
        # (CreateFileA, 0x401000)
        yield API(impname), va

        if is_aw_function(impname):
            # (CreateFile, 0x401000)
            yield API(impname[:-1]), va


def is_ordinal(symbol):
    return symbol[0] == "#"


def generate_import_features(dll, symbol, va):
    """
    for a given dll, symbol, and address, generate import features.
    we over-generate features to make matching easier.
    these include:
      - kernel32.CreateFileA
      - kernel32.CreateFile
      - CreateFileA
      - CreateFile
    """
    # (kernel32.CreateFileA, 0x401000)
    yield Import(dll + "." + symbol), va
    # (CreateFileA, 0x401000)
    if not is_ordinal(symbol):
        yield Import(symbol), va

    if is_aw_function(symbol):
        # (kernel32.CreateFile, 0x401000)
        yield Import(dll + "." + symbol[:-1]), va
        # (CreateFile, 0x401000)
        if not is_ordinal(symbol):
            yield Import(symbol[:-1]), va


def all_zeros(bytez):
    return all(b == 0 for b in builtins.bytes(bytez))


def twos_complement(val, bits):
    """
    compute the 2's complement of int value val

    from: https://stackoverflow.com/a/9147327/87207
    """
    # if sign bit is set e.g., 8bit: 128-255
    if (val & (1 << (bits - 1))) != 0:
        # compute negative value
        return val - (1 << bits)
    else:
        # return positive value as is
        return val
