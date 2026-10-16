"""八元RGS划分、S2位序与旧严格方向的纯函数接口。"""
from __future__ import annotations

from functools import lru_cache

from common import ATOMS,KINTYPES,CATEGORY_ORDER
from structural_enumeration import canonical_partition,partition_to_labels,strict_prediction_directions

N_ATOMS=8
UNIVERSE=255


def canonical_rgs(labels):
    if len(labels)!=N_ATOMS:raise ValueError('需要按S2位序给出八个标签。')
    mapping={};out=[]
    for label in labels:
        if label not in mapping:mapping[label]=len(mapping)
        out.append(mapping[label])
    return tuple(out)


def validate_rgs(rgs):
    values=tuple(rgs)
    if len(values)!=N_ATOMS or values[0]!=0:raise ValueError('RGS必须八位且首位0。')
    largest=0
    for value in values:
        if not isinstance(value,int) or value<0 or value>largest+1:raise ValueError('不是合法restricted growth string。')
        largest=max(largest,value)
    return values


@lru_cache(None)
def enumerate_rgs():
    result=[]
    def add(prefix,largest):
        if len(prefix)==N_ATOMS:result.append(tuple(prefix));return
        for label in range(largest+2):add(prefix+[label],max(largest,label))
    add([0],0)
    return tuple(result)


def rgs_to_blocks(rgs):
    values=validate_rgs(tuple(int(x) for x in rgs));blocks={}
    for i,label in enumerate(values):blocks[label]=blocks.get(label,0)|(1<<i)
    return canonical_partition(blocks.values())


def blocks_to_rgs(blocks):return canonical_rgs(partition_to_labels(canonical_partition(blocks)))


def rgs_string(rgs):return ''.join(map(str,validate_rgs(tuple(int(x) for x in rgs))))


@lru_cache(None)
def partition_id_map():return {rgs:i for i,rgs in enumerate(enumerate_rgs())}


def partition_id_from_labels(labels):return partition_id_map()[canonical_rgs(labels)]


def strict_direction_vector(labels):
    result=strict_prediction_directions(labels)
    mapping={'predicted_side':1,'opposite_side':-1,'not_applicable':0}
    return tuple(mapping[result[name]] for name in ['P2','P3','P4'])


@lru_cache(None)
def partition_catalogue():
    return tuple({'partition_id':i,'rgs':rgs_string(rgs),'labels':rgs,'blocks':rgs_to_blocks(rgs),
                  's2_labels':partition_to_labels(rgs_to_blocks(rgs)),'k':max(rgs)+1,
                  'shape':tuple(sorted(block.bit_count() for block in rgs_to_blocks(rgs))),
                  **dict(zip(['P2','P3','P4'],strict_direction_vector(rgs)))} for i,rgs in enumerate(enumerate_rgs()))
