"""精确最小DNF文字成本；允许合取项重叠，不等同旧S2树成本。"""
from __future__ import annotations

from functools import lru_cache
from itertools import product

from common import FEATURES

LANGUAGES={'abs':('s','a','r'),'rel_r':('q','a','r'),'rel_s':('q','a','s'),'all':('s','a','r','q')}
LANGUAGE_NAMES=tuple(LANGUAGES)
UNIVERSE=255


def language_features(language):
    key=language.removeprefix('L_') if isinstance(language,str) else None
    return LANGUAGES[key] if key is not None else tuple(language)


@lru_cache(None)
def conjunction_terms(feature_names):
    """每种非空外延只保留最短文字见证；真式外延255、成本0。"""
    names=tuple(feature_names);out={}
    for assignment in product((-1,0,1),repeat=len(names)):
        literals=tuple((name,value) for name,value in zip(names,assignment) if value!=-1)
        extent=sum(1<<i for i in range(8) if all(FEATURES[name][i]==value for name,value in literals))
        if not extent:continue
        item=(len(literals),literals)
        if extent not in out or item<out[extent]:out[extent]=item
    return out


@lru_cache(None)
def conjunction_extents(language):return frozenset(conjunction_terms(language_features(language)))


@lru_cache(None)
def subset_dnf_table(language):
    terms=conjunction_terms(language_features(language));table={}
    for target in range(1,256):
        usable=[(extent,cost,witness) for extent,(cost,witness) in terms.items() if extent&~target==0]
        @lru_cache(None)
        def solve(remaining):
            if not remaining:return (0,())
            first=remaining&-remaining;candidates=[]
            for extent,cost,witness in usable:
                if extent&first:
                    rest,proof=solve(remaining&~extent)
                    candidates.append((cost+rest,(witness,)+proof))
            if not candidates:raise ValueError('描述语言不能区分目标位置。')
            return min(candidates)
        value,proof=solve(target)
        table[target]={'literals':value,'terms':proof}
    return table


def minimum_dnf(mask,language='abs'):
    if not isinstance(mask,int) or not 0<mask<=UNIVERSE:raise ValueError('DNF词项必须为非空八元子集。')
    return subset_dnf_table(language)[mask]['literals']


def minimum_dnf_witness(mask,language='abs'):
    minimum_dnf(mask,language)
    return subset_dnf_table(language)[mask]['terms']


def is_conjunctive(blocks,language='all'):
    extents=conjunction_extents(language)
    return all(int(block) in extents for block in blocks)


def partition_dl(blocks,language='abs'):return sum(minimum_dnf(int(block),language) for block in blocks)


def total_description_cost(blocks,language='abs',feature_cost=0):
    return partition_dl(blocks,language)+feature_cost*len(language_features(language))
