"""Format changes seen in Bitwig 6.1.7 (synthetic, no installation needed)."""

import io
import struct
import zipfile

from bwpreset import model as m
from bwpreset.build import fill_device_headers
from bwpreset.codec import Obj
from bwpreset.encoding import _find_key_method, _key_from_code


def _module(*extra):
    return Obj(m.MODULE, [(0x2B9, 8, "0"), (0x9A, 8, "Sine"), (0x9B, 8, "Bitwig"), (0x9C, 8, "Oscillator"), *extra, (m.F_TYPE, 0x15, None)])


def test_device_header_fields_follow_the_category():
    body = Obj(0xD3, [(0x20C, 0x12, [_module(), Obj(0x85, [(0x2B9, 8, "x")])])])
    fill_device_headers(body)
    ids = [f for f, _, _ in body.fields[0][2][0].fields]
    assert ids == [0x2B9, 0x9A, 0x9B, 0x9C, 0x9E, 0x9F, 0xA1, 0xA2, 0xA3, 0x3550, m.F_TYPE]
    assert body.fields[0][2][1].fields == [(0x2B9, 8, "x")]


def test_device_header_keeps_existing_values_and_moves_them_into_place():
    module = _module()
    module.fields.append((0xA3, 5, False))
    fill_device_headers(module)
    assert module.fields[8] == (0xA3, 5, False)
    assert [f for f, _, _ in module.fields].count(0xA3) == 1


def _key_code(values):
    code = bytearray([0x10, 0x80, 0xBC, 8])  # bipush 128; newarray byte
    for i, v in enumerate(values):
        code += bytes([0x59, 0x10, i if i < 128 else 0, 0x10]) + struct.pack("b", v - 256 if v > 127 else v) + b"\x54"
    return bytes(code + b"\xb0")


def _class_with_method(code):
    pool = [b"Code", b"k", b"()[B"]
    out = bytearray(b"\xca\xfe\xba\xbe\x00\x00\x00\x34") + struct.pack(">H", len(pool) + 1)
    for s in pool:
        out += b"\x01" + struct.pack(">H", len(s)) + s
    out += b"\x00\x21\x00\x00\x00\x00" + b"\x00\x00"  # access, this, super; no interfaces
    out += b"\x00\x00"  # fields
    attr = struct.pack(">HHI", 1, 1, len(code)) + code + b"\x00\x00\x00\x00"
    out += b"\x00\x01" + struct.pack(">HHHH", 9, 2, 3, 1) + struct.pack(">HI", 1, len(attr)) + attr
    return bytes(out)


def test_key_method_is_found_when_the_class_is_renamed():
    values = list(range(128))
    jar = io.BytesIO()
    with zipfile.ZipFile(jar, "w") as z:
        z.writestr("com/bitwig/base/serial/file/Renamed.class", _class_with_method(_key_code(values)))
        z.writestr("com/bitwig/base/serial/file/Other.class", _class_with_method(b"\xb1"))
    with zipfile.ZipFile(jar) as z:
        assert _key_from_code(_find_key_method(z)) == bytes(values)
