import copy
import sympy
from itertools import chain

class SlpdProto:

    def __init__(self, slpd_json):
        self._proto = copy.deepcopy(slpd_json)
        self._setup()

    def register(self, jinja_env):
        for name in dir(self):
            if not name.startswith('_'):
                jinja_env.globals[name] = getattr(self, name)

    @property
    def header(self):
        return self._proto["header"][0]

    @property
    def code(self):
        return self._proto["code"][0]

    @property
    def type(self):
        return self._proto["type"][0]

    @property
    def enums(self):
        return self._proto["enums"]

    @property
    def structs(self):
        return self._proto.get("structs", [])

    @property
    def messages(self):
        return self._proto.get("messages", [])

    @property
    def enumerables(self):
        return list(chain(
            self._proto.get("code", []), 
            self._proto.get("type", []), 
            self._proto.get("enums", [])
        ))
    
    @property
    def structurals(self):
        return list(chain(
            self._proto.get("header", []), 
            self._proto.get("structs", []), 
            self._proto.get("messages", [])
        ))
    
    @property
    def rdms(self):
        rdms = []

        def rdm(command, type, packet):
            return {"command": command, "type": type, "packet": packet}
    
        for rule in self._proto["rules"]:
            if rule["sendPacket"] != None:
                rdms.append(rdm(rule["command"], rule["sendType"], rule["sendPacket"]))
            if rule["responseType"] != None and rule["responsePacket"] != None:
                rdms.append(rdm(rule["command"], rule["responseType"], rule["responsePacket"]))
        return rdms    

    def enumerable(self, name):
        for enum in self.enumerables:
            if enum["name"] == name:
                return enum
        return None

    @staticmethod
    def is_builtin(target):
        if SlpdProto.is_array(target):
            return False
        
        typename = SlpdProto._get_typename(target)
        if typename is None:
            return False
        
        if typename in {"char", "bool", "f32", "f64"}:
            return True
        if len(typename) < 2: 
            return False
        if typename[0] in {'u', 'i'} and typename[1:].isnumeric():
            return True
        return False

    @staticmethod
    def is_bool(target):
        if SlpdProto.is_array(target):
            return False 
        return SlpdProto._get_typename(target) == 'bool'

    def is_enumerable(self, target):
        name = SlpdProto._get_typename(target)
        if name is None: 
            return False
        
        return any(enum["name"] == name for enum in self.enumerables)

    def is_structural(self, target):
        if SlpdProto.is_array(target):
            return False

        name = SlpdProto._get_typename(target)
        if name is None:
            return False
        
        for struct in self.structurals:
            if struct["name"] == name : return True
        return False

    def is_message(self, name):
        return any(msg["name"] == name for msg in self.messages)

    @staticmethod
    def is_array(target):
        if not isinstance(target, dict):
            return False
        
        for key in ["sizeVar", "constantSize"]:
            if key in target and target[key] != None:
                return True
        return False

    def offset(self, field):
        offset = 0
        structural = self._find_target_by_name(field["owner"], self.structurals)
        for desc in structural["fields"]:
            if desc["name"] == field["name"]:
                return offset
            else:
                offset += self.sizeof(desc)
        return None
    
    def is_always_aligned(self, field):        
        offset = self.offset(field)
        
        if field["owner"] == self.header["name"]:
            return self._is_multiple_of(offset, 8)
        
        offset += self.sizeof(self.header)
        
        if msg := self._find_target_by_name(field["owner"], self.messages):
            return self._is_multiple_of(offset, 8)
        
        if struct := self._find_target_by_name(field["owner"], self.structs):
            for msg in self.messages:
                for field in msg["fields"]:
                    if field["type"] == struct["name"]:
                        if self._is_multiple_of(offset + self.offset(field), 8):
                            continue
                        else:
                            return False
        return True

    def sizeof(self, target):
        if self.is_array(target):
            return self._array_size(target)
        
        typename = self._get_typename(target)
        if self.is_builtin(typename):
            return self._builtin_size(typename)
        if self.is_enumerable(typename):
            return self._enumerable_size(typename)
        if self.is_structural(typename):
            return self._structural_size(typename)
        return None

    @staticmethod
    def length(target):
        if not isinstance(target, dict):
            return None
        
        for key in ["sizeVar", "constantSize"]:
             if target[key] != None:
                 return target[key]
        return 1
    
    def is_length(self, field):
        structural = self._find_target_by_name(field["owner"], self.structurals)
        for desc in structural["fields"]:
            if self.is_array(desc):
                if self.length(desc) == field["name"]:
                    return True
        return False

    def is_builtin_array_aligned(self, field):
        return (self.is_array(field) and
                self.is_always_aligned(field) and 
                self.is_builtin(field["type"]))

    def is_bytes_aligned(self, field):
        return (self.is_builtin_array_aligned(field) and
                self.sizeof(field["type"]) == 8)

    def _setup(self):
        for structural in self.structurals:
            for field in structural["fields"]:
                field["owner"] = structural["name"]

    @staticmethod
    def _builtin_size(name):
        prefix = name[0]
        size = name[1:]
        if name == "char": return 8
        if name == "bool": return 8
        if name == "f32": return 32
        if name == "f64": return 64
        elif prefix in {'u', 'i'} and size.isnumeric():
            return int(size)
        return None

    def _enumerable_size(self, name):
        enum = self._find_target_by_name(name, self.enumerables)
        if enum["size"] != "null": 
            return enum["size"]
        else:
            field = max(enum["fields"], key=lambda field: field["value"])
            if field["value"] > 255: return 16
            else: return 8

    def _structural_size(self, name):
        struct = self._find_target_by_name(name, self.structurals)
        size = 0
        for field in struct["fields"]:
            size += self.sizeof(field)
        return size
    

    def _array_size(self, target):
        length = SlpdProto.length(target)
        length = sympy.Symbol(length) if isinstance(length, str) else length
        return self.sizeof(target["type"]) * length

    @staticmethod 
    def _get_typename(target):
        if isinstance(target, str):
            return target
        for key in ["type", "name"]:
            if key in target: return target[key]
        return None

    @staticmethod
    def _find_target_by_name(name, entities):
        for entity in entities:
            if entity["name"] == name:
                return entity
        return None
    
    @staticmethod
    def _is_multiple_of(expr, devider):    
        quotient = sympy.simplify(expr) / devider
        for arg in (quotient.args or [quotient]):
            coeff, _ = arg.as_coeff_mul()
            if not coeff.q == 1: return False
        return True