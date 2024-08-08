from itertools import chain
import os

__all__ = ('LineWriter', 'tuple_pairs', 'q')

class LineWriter:
    def __init__(self, file):
        self.file = file
        self.prev = None
    
    @classmethod
    def from_path(cls, fpath):
        os.makedirs(os.path.dirname(fpath), exist_ok=True)
        return cls(open(fpath, "w"))
    
    def __enter__(self):
        self.file.__enter__()
        return self
    
    def __exit__(self, *args, **kwargs):
        return self.file.__exit__(*args, **kwargs)
        
    @staticmethod
    def flat_dict(d: dict):
        return ",".join(f"'{k}':{v}" for k, v in d.items())

    def module(self, name: str, cls: str, trigger_from = None, **params):
        if trigger_from is None:
            source_nodes = '' if self.prev is None else f'"{self.prev}"'
        else:
            if not isinstance(trigger_from, str):
                trigger_from = ",".join(trigger_from)
            source_nodes = f'"{trigger_from}"'

        self.file.write(f'"{name}","{cls}",{source_nodes},"{self.flat_dict(params)}"\n')
        self.prev = name
    
    def comment(self, comment: str, use_hash: bool = False):
        if use_hash:
            self.file.write(f'#{comment}\n')
        else:
            self.file.write(f',,,,,"{comment}"\n')

    def newline(self, n=1):
        for i in range(n):
            self.file.write(',,,,,\n')

def fix_writekey(key):
    if isinstance(key, (tuple, list)):
        return "/".join(key)
    else:
        return key

def tuple_pairs(*args, **kwargs):
    pairs = chain(*(arg.items() for arg in args), kwargs.items())
    pair_seq = ",".join(f"('{fix_writekey(k)}',{v})" for k, v in pairs)
    return f"({pair_seq})"

def q(string_contents: str):
    return f"'{string_contents}'"