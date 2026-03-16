import sys
import math
import jinja2
from typing import Any
from pathlib import Path
from core.slpd import SlpdProto

#def resource_path():
#    return sys._MEIPASS if hasattr(sys, '_MEIPASS') else "."

def round_up(number: int)-> int:
    values = [8, 16, 24, 32, 64]
    for val in values:
        if val >= number:
            return val
    return number

def lua_type(proto: SlpdProto, field: dict) -> str:
    if proto.is_bytes_aligned(field): return "bytes"
    type = field["type"] if proto.is_builtin(field) else None
    if type == "char": return "char"
    if type == "bool": return "bool"
    if type == "f32": return "float"
    if type == "f64": return "double"
    elif type and type[0] in {'u', 'i'} and type[1:].isnumeric():
        return f"{'u' if type[0] == 'u' else ''}int{round_up(int(type[1:]))}"
    return "uint32"

def lua_base(proto: SlpdProto, field: dict) -> str:
    if proto.is_bytes_aligned(field):return "base.SPACE"
    type = field["type"]
    if type == "char": return "base.CHAR"
    if type == "bool": return "base.NONE"
    if type == "f32": return "base.DEC"
    if type == "f64": return "base.DEC"
    if type[0] == 'i': return "base.DEC"
    return "base.HEX"

def save_ceil(num: Any) -> int:
    if isinstance(num, float) or isinstance(num, int):
        return math.ceil(float(num))
    else:
        return num

def enumerable_val(enum: dict, enumerator: str) -> int:
    for field in enum["fields"]:
        if field["name"] == enumerator:
            return field["value"]

def generate(proto: SlpdProto, proto_name: str, proto_port: int) -> None:
    template_path = Path(__file__).resolve().parent / "templates"
    templateEnv = jinja2.Environment(loader=jinja2.FileSystemLoader(template_path))

    proto.register(templateEnv)

    context = {
        'ceil' : save_ceil, 
        'enumerable_val' : enumerable_val,
        'lua_type' : lambda field: lua_type(proto, field),
        'lua_base' : lambda field: lua_base(proto, field),
        'proto_name' : proto_name,
        'proto_port' : proto_port
    }

    template = templateEnv.get_template("dissector.jinja")
    output = template.render(**context) 

    with open(proto_name + '.lua', 'w') as file:
        file.write(output)
