import jinja2
from typing import Literal
from pathlib import Path
from utils import case_convert
from core.slpd import SlpdProto

def header_fields(proto: SlpdProto, kind: Literal["local", "remote"]):
    header = proto.header
    return [f for f in header['fields'] if f['specialType'] == kind]


def header_args(proto: SlpdProto, kind: Literal["local", "remote"]):
    args = []
    for field in header_fields(proto, kind):
        fname = to_field_format(field["name"])
        
        ftype = field["type"]
        ftype = ftype if proto.is_builtin(field) else to_type_format(ftype)

        args.append(f'{fname}: {ftype}')
    
    return args

def field_with_length(proto: SlpdProto, length: dict) -> dict:
    for struct in proto.structurals:
        if struct["name"] == length["owner"]:
            for field in struct["fields"]:
                if field["sizeVar"] == length["name"]:
                    return field


def is_data_len(proto: SlpdProto, field: dict) -> bool:
    if field.get('owner') != proto.header['name']:
        return False
    
    name = case_convert.to_snake(field.get('name', ''))
    return 'data' in name and 'len' in name


def to_type_name(proto: SlpdProto, name: str) -> str:
    return name + ("Msg" if proto.is_message(name) else "")


def to_type_format(name: str) -> str:
    return case_convert.to_pascal(name) 


def to_const_format(name: str) -> str:
    return case_convert.to_upper_snake(name) 


def to_func_format(name: str) -> str:
    return case_convert.to_snake(name)


def to_field_format(name: str) -> str:
    return case_convert.to_snake(name)


def generate(proto: SlpdProto, proto_name: str) -> None:
    template_path = Path(__file__).resolve().parent / "templates"
    templateEnv = jinja2.Environment(loader=jinja2.FileSystemLoader(template_path))
    
    proto.register(templateEnv)

    context = {
        'to_type_format'   : to_type_format,
        'to_const_format'  : to_const_format, 
        'to_func_format'   : to_func_format,
        'to_field_format'  : to_field_format,
        'to_type_name'     : lambda name: to_type_name(proto, name), 
        'local_args'       : lambda: header_args(proto, "local"),
        'remote_args'      : lambda: header_args(proto, "remote"),
        'local_fields'     : lambda: header_fields(proto, "local"),
        'remote_fields'    : lambda: header_fields(proto, "remote"),
        'is_data_len'      : lambda field: is_data_len(proto, field),
        'field_with_length': lambda field: field_with_length(proto, field),
        'proto_name'       : proto_name
    }

    template = templateEnv.get_template("proto.jinja")
    out = template.render(**context) 

    with open(proto_name + '.py', 'w') as file:
        file.write(out)

    template = templateEnv.get_template("proto_impl.jinja")
    out = template.render(**context) 

    with open(proto_name + '_impl.py', 'w') as file:
        file.write(out)

    template = templateEnv.get_template("slpd_core.jinja")
    out = template.render(**context) 

    with open('slpd_core.py', 'w') as file:
        file.write(out)