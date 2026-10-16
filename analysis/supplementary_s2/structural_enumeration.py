"""纯理论兄弟姐妹划分、定义诊断与基底比较；不读取实测文件。

所有数字仅由八个逻辑位置及文献手工转录表推导。这里并列任意合取
与单叶递归划分树，未替作者选择主定义。代码不读取CSV或共享结果。
"""
from __future__ import annotations

import argparse
from collections import Counter
from fractions import Fraction
from functools import lru_cache
from itertools import combinations, product
import json
from math import factorial
from typing import Iterable, Sequence


# 位序固定为(s, a, r)：0分别表示男性、年长、男性；q=0为同性。
ATOMS = tuple(product((0, 1), repeat=3))
KINTYPES = tuple("mf"[s] + "o" + "mf"[r] + "ey"[a] for s, a, r in ATOMS)
KINTYPE_INDEX = {code: index for index, code in enumerate(KINTYPES)}
UNIVERSE = (1 << len(ATOMS)) - 1
FEATURES = {
    "s": tuple(s for s, a, r in ATOMS),
    "a": tuple(a for s, a, r in ATOMS),
    "r": tuple(r for s, a, r in ATOMS),
    "q": tuple(s ^ r for s, a, r in ATOMS),
    # 比较的是两位实际兄弟姐妹中年长者／年幼者的性别。
    "elder_sex": tuple(r if a == 0 else s for s, a, r in ATOMS),
    "younger_sex": tuple(s if a == 0 else r for s, a, r in ATOMS),
}
BASIS_RAW = ("s", "a", "r")
BASIS_RELATIVE = ("s", "a", "q")
FEATURES_FOUR = ("s", "a", "r", "q")
FEATURES_SIX = FEATURES_FOUR + ("elder_sex", "younger_sex")


def canonical_partition(blocks: Iterable[int]) -> tuple[int, ...]:
    """验证并规范化完整、不相交、非空的八元划分。"""
    result = tuple(sorted(int(block) for block in blocks))
    seen = 0
    for block in result:
        if block <= 0 or block & ~UNIVERSE or block & seen:
            raise ValueError("划分块须非空、互不重叠且位于八元全集")
        seen |= block
    if seen != UNIVERSE:
        raise ValueError("划分必须覆盖全部八个逻辑位置")
    return result


def partition_from_groups(groups: Sequence[Sequence[str]]) -> tuple[int, ...]:
    return canonical_partition(
        sum(1 << KINTYPE_INDEX[code] for code in group) for group in groups
    )


def labels_to_partition(labels: Sequence[object]) -> tuple[int, ...]:
    """labels须按KINTYPES位序给出；同一标签代表同一类。"""
    if len(labels) != 8:
        raise ValueError("需要八个类别标签")
    groups: dict[object, int] = {}
    for index, label in enumerate(labels):
        groups[label] = groups.get(label, 0) | (1 << index)
    return canonical_partition(groups.values())


def partition_to_labels(partition: Sequence[int]) -> tuple[int, ...]:
    blocks = canonical_partition(partition)
    return tuple(next(j for j, block in enumerate(blocks) if block & (1 << i)) for i in range(8))


def partition_codes(partition: Sequence[int]) -> list[list[str]]:
    return [[code for i, code in enumerate(KINTYPES) if block & (1 << i)] for block in partition]


@lru_cache(None)
def enumerate_partitions(n: int = 8) -> tuple[tuple[int, ...], ...]:
    """递归加入最大元素；每一无标签集合划分恰出现一次。"""
    if not 0 <= n <= 8:
        raise ValueError("本模块只枚举0至8个元素")
    if n == 0:
        return ((),)
    bit = 1 << (n - 1)
    result = []
    for blocks in enumerate_partitions(n - 1):
        result.append(tuple(sorted(blocks + (bit,))))
        for index in range(len(blocks)):
            result.append(tuple(sorted(blocks[:index] + (blocks[index] | bit,) + blocks[index + 1:])))
    return tuple(result)


@lru_cache(None)
def conjunction_witnesses(feature_names: tuple[str, ...]) -> dict[int, tuple[tuple[str, int], ...]]:
    """每个特征取0、1或不指定；返回非空外延的最短合取见证。"""
    witnesses = {}
    for values in product((-1, 0, 1), repeat=len(feature_names)):
        literals = tuple((name, value) for name, value in zip(feature_names, values) if value != -1)
        mask = sum(1 << i for i in range(8) if all(FEATURES[name][i] == value for name, value in literals))
        if mask and (mask not in witnesses or len(literals) < len(witnesses[mask])):
            witnesses[mask] = literals
    return witnesses


def is_conjunctive(partition: Sequence[int], feature_names: Sequence[str] = FEATURES_FOUR) -> bool:
    witnesses = conjunction_witnesses(tuple(feature_names))
    return all(block in witnesses for block in canonical_partition(partition))


@lru_cache(None)
def tree_partitions(feature_names: tuple[str, ...], balanced: bool = False, mask: int = UNIVERSE) -> frozenset[tuple[int, ...]]:
    """单叶递归划分树：每一词项恰为一个叶；可另要求每次等分。

    非等分模式允许3→1+2。它不等同于原文8→4→2→1的层级叙述。
    与基底评分所用、允许同一词项重复出现在不同叶的分类树不同。
    """
    output = {(mask,)}
    for name in feature_names:
        zero = mask & sum(1 << i for i, value in enumerate(FEATURES[name]) if value == 0)
        one = mask ^ zero
        if not zero or not one or (balanced and zero.bit_count() != one.bit_count()):
            continue
        for left in tree_partitions(feature_names, balanced, zero):
            for right in tree_partitions(feature_names, balanced, one):
                output.add(tuple(sorted(left + right)))
    return frozenset(output)


def is_partition_tree(partition: Sequence[int], feature_names: Sequence[str] = FEATURES_FOUR, balanced: bool = False) -> bool:
    return canonical_partition(partition) in tree_partitions(tuple(feature_names), balanced)


def partition_tree_witness(partition: Sequence[int], feature_names: Sequence[str] = FEATURES_FOUR, mask: int = UNIVERSE, root: str | None = None, minimum_feature_depths: dict[str, int] | None = None) -> dict | None:
    """返回单叶递归树的一个具体见证；root可固定当前节点的特征。

    子树叶必须恰为一个完整词项，不能把词项拆到多个叶后再合并。
    返回一个见证不宣称该表示唯一；无见证返回None。
    """
    blocks = canonical_partition(partition)
    names = tuple(feature_names)
    depth_limits = minimum_feature_depths or {}
    if any(block & mask and block & (UNIVERSE ^ mask) for block in blocks):
        return None

    @lru_cache(None)
    def solve(node_mask: int, required_root: str | None = None, depth: int = 0):
        if node_mask in blocks:
            return None if required_root is not None else {"leaf": [KINTYPES[i] for i in range(8) if node_mask & (1 << i)]}
        choices = (required_root,) if required_root is not None else names
        for name in choices:
            if name not in names:
                continue
            if depth < depth_limits.get(name, 0):
                continue
            zero = node_mask & sum(1 << i for i, value in enumerate(FEATURES[name]) if value == 0)
            one = node_mask ^ zero
            if not zero or not one:
                continue
            if any(block & zero and block & one for block in blocks):
                continue
            left, right = solve(zero, None, depth + 1), solve(one, None, depth + 1)
            if left is not None and right is not None:
                return {"feature": name, "zero": left, "one": right}
        return None

    return solve(mask, root)


def tree_representation_count(partition: Sequence[int], feature_names: Sequence[str] = FEATURES_FOUR, minimum_feature_depths: dict[str, int] | None = None) -> int:
    """精确计数合法单叶递归树；特征取值固定左右方向，不重复计镜像。"""
    blocks = canonical_partition(partition)
    names = tuple(feature_names)
    limits = minimum_feature_depths or {}

    @lru_cache(None)
    def solve(mask: int, depth: int) -> int:
        if mask in blocks:
            return 1
        total = 0
        for name in names:
            if depth < limits.get(name, 0):
                continue
            zero = mask & sum(1 << i for i, value in enumerate(FEATURES[name]) if value == 0)
            one = mask ^ zero
            if not zero or not one or any(block & zero and block & one for block in blocks):
                continue
            total += solve(zero, depth + 1) * solve(one, depth + 1)
        return total

    return solve(UNIVERSE, 0)


def feature_tree_depth_options(partition: Sequence[int], feature: str = "s", feature_names: Sequence[str] = FEATURES_FOUR) -> dict:
    """枚举所有单叶递归表示中的某特征深度集合；根深度为0。

    空集合表示整棵树省略此特征。保留可选表示与必需表示的区别，
    不把某一任意选中树的深度称为该语言的唯一语义层级。
    """
    blocks = canonical_partition(partition)
    names = tuple(feature_names)

    @lru_cache(None)
    def solve(mask: int) -> frozenset[tuple[int, ...]]:
        if mask in blocks:
            return frozenset({()})
        choices = set()
        for name in names:
            zero = mask & sum(1 << i for i, value in enumerate(FEATURES[name]) if value == 0)
            one = mask ^ zero
            if not zero or not one or any(block & zero and block & one for block in blocks):
                continue
            for left in solve(zero):
                for right in solve(one):
                    depths = {depth + 1 for depth in left + right}
                    if name == feature:
                        depths.add(0)
                    choices.add(tuple(sorted(depths)))
        return frozenset(choices)

    options = sorted(solve(UNIVERSE))
    allowed = [depths for depths in options if not depths or min(depths) >= 2]
    unrestricted_count = tree_representation_count(blocks, names)
    compatible_count = tree_representation_count(blocks, names, {feature: 2})
    status = "outside_single_leaf_tree_domain" if not options else "compatible" if allowed else "incompatible_all_trees_require_early_feature"
    return {"feature": feature, "feature_names": list(names), "tree_exists": bool(options), "possible_depth_sets": [list(depths) for depths in options], "representation_without_feature_exists": () in options, "representation_only_tertiary_or_unused_exists": bool(allowed), "representation_with_primary_or_secondary_exists": any(depths and min(depths) < 2 for depths in options), "all_tree_representations_violate_only_tertiary": bool(options) and not allowed, "status": status, "total_tree_representation_count": unrestricted_count, "compatible_tree_representation_count": compatible_count, "representation_ambiguous": unrestricted_count > 1, "compatible_tree_witness": partition_tree_witness(blocks, names, minimum_feature_depths={feature: 2})}


def minimum_classification_tree_nodes(labels: Sequence[object], basis: Sequence[str]) -> int:
    """允许重复词项叶的精确最小二叉特征分类树内部节点数。

    所有内部节点成本为1；叶成本为0。因为输出划分固定，任何非空
    特征切分都可选；重复词项叶的额外测试由内部节点数体现。
    """
    labels = tuple(labels)
    if len(labels) != 8 or len(basis) != 3:
        raise ValueError("基底评分要求八个标签和三维完备基底")
    feature_names = tuple(basis)
    coordinates = tuple(tuple(FEATURES[name][i] for name in feature_names) for i in range(8))
    if len(set(coordinates)) != 8:
        raise ValueError("三个特征必须唯一标识八个位置")

    @lru_cache(None)
    def solve(mask: int) -> int:
        indices = tuple(i for i in range(8) if mask & (1 << i))
        if len({labels[i] for i in indices}) == 1:
            return 0
        candidates = []
        for name in feature_names:
            zero = sum(1 << i for i in indices if FEATURES[name][i] == 0)
            one = mask ^ zero
            if zero and one:
                candidates.append(1 + solve(zero) + solve(one))
        return min(candidates)

    return solve(UNIVERSE)


def basis_score(labels: Sequence[object], basis: Sequence[str]) -> int:
    """描述长度规则：每条分类树边成本1，故等于2×最小内部节点数。"""
    return 2 * minimum_classification_tree_nodes(labels, basis)


def evaluate_partition(labels: Sequence[object], basis: Sequence[str]) -> dict:
    """返回指定基底下的最小描述边数、四条最小对及其条件作用侧。

    separated_count的4/2/1仅为边界覆盖代理；2条边须共享另一特征
    的固定取值才记录secondary_side。分类树节点深度不由此自动推出。
    """
    labels = tuple(labels)
    partition = labels_to_partition(labels)
    feature_names = tuple(basis)
    score = basis_score(labels, feature_names)
    profiles = {}
    for name in feature_names:
        others = tuple(other for other in feature_names if other != name)
        edges = []
        for context in product((0, 1), repeat=2):
            endpoints = tuple(i for i in range(8) if all(FEATURES[other][i] == value for other, value in zip(others, context)))
            assert len(endpoints) == 2
            edges.append({"context": dict(zip(others, context)), "kintypes": [KINTYPES[i] for i in endpoints], "separated": labels[endpoints[0]] != labels[endpoints[1]]})
        selected = [edge for edge in edges if edge["separated"]]
        secondary_side = {}
        if len(selected) == 2:
            for other in others:
                values = {edge["context"][other] for edge in selected}
                if len(values) == 1:
                    secondary_side[other] = next(iter(values))
        proxy = {0: "unused", 1: "one_edge", 2: "two_edges", 3: "irregular_three_edges", 4: "full_edge_coverage"}[len(selected)]
        if len(selected) == 2 and not secondary_side:
            proxy = "irregular_two_contexts"
        profiles[name] = {"separated_count": len(selected), "secondary_side": secondary_side, "coverage_proxy": proxy, "edges": edges}
    return {"basis": list(feature_names), "minimaledgecount": score, "minimum_internal_nodes": score // 2, "basis_score": score, "secondary_side": {name: profile["secondary_side"] for name, profile in profiles.items()}, "features": profiles, "conjunctive_in_basis": is_conjunctive(partition, feature_names), "single_leaf_partition_tree": is_partition_tree(partition, feature_names)}


def select_bases(labels: Sequence[object]) -> list[dict]:
    """最短基底均保留；并列展示权重各1/2，单独最短者权重1。"""
    evaluations = [evaluate_partition(labels, basis) for basis in (BASIS_RAW, BASIS_RELATIVE)]
    best = min(value["basis_score"] for value in evaluations)
    selected = [value for value in evaluations if value["basis_score"] == best]
    return [{**value, "display_weight": 1 / len(selected)} for value in selected]


def prediction_directions(labels: Sequence[object]) -> dict:
    """给出边覆盖描述方向，每个系统每项预测只有一个记录。

    P2/P3在r基底、P4在q基底按命题定义评估，不因基底评分删掉
    某项命题的可观察对象。P5报告最短基底的集合值；冲突标模糊。
    它们是透明的描述对照，不能冒充已识别唯一理论层级。
    """
    raw = evaluate_partition(labels, BASIS_RAW)
    relative = evaluate_partition(labels, BASIS_RELATIVE)
    def side(evaluation, target, conditioning):
        value = evaluation["secondary_side"][target].get(conditioning)
        return "predicted_side" if value == 0 else "opposite_side" if value == 1 else "not_applicable"
    selected = select_bases(labels)
    counts = sorted({value["features"]["s"]["separated_count"] for value in selected})
    states = {"unused" if count == 0 else "tertiary_proxy" if count == 1 else "beyond_tertiary_proxy" for count in counts}
    state = next(iter(states)) if len(states) == 1 else "basis_ambiguous"
    return {"P2": side(raw, "r", "a"), "P3": side(raw, "a", "r"), "P4": side(relative, "a", "q"), "P5": state, "P5_separated_counts": counts, "system_weight_per_prediction": 1, "selected_bases": [{"basis": value["basis"], "display_weight": value["display_weight"], "basis_score": value["basis_score"]} for value in selected]}


def secondary_structure_witness(labels: Sequence[object], parent: str, target: str, basis: Sequence[str], feature_names: Sequence[str] = FEATURES_FOUR) -> dict:
    """返回二级方向的分项证据与严格结构判定，而非不透明classic布尔值。

    主strict方向要求目标恰两条分离边且同侧；所有词项不跨父根，
    指定侧的词项不跨目标2+2子根，且两侧能递归得到词项叶。
    对侧树另外禁用目标特征，只表示该坐标可省略，不推断语义不存在。
    """
    partition = labels_to_partition(labels)
    evaluation = evaluate_partition(labels, basis)
    profile = evaluation["features"][target]
    parent_zero = sum(1 << i for i, value in enumerate(FEATURES[parent]) if value == 0)
    parent_one = UNIVERSE ^ parent_zero
    root_compatible = not any(block & parent_zero and block & parent_one for block in partition)
    parent_full_edges = evaluation["features"][parent]["separated_count"] == 4
    edge_side = profile["secondary_side"].get(parent)
    candidates = {}
    possible_sides = []
    for side in (0, 1):
        branch = parent_zero if side == 0 else parent_one
        other = parent_one if side == 0 else parent_zero
        target_zero = branch & sum(1 << i for i, value in enumerate(FEATURES[target]) if value == 0)
        target_one = branch ^ target_zero
        branch_compatible = not any(block & target_zero and block & target_one for block in partition)
        candidate_tree = partition_tree_witness(partition, feature_names, branch, target) if root_compatible and branch_compatible else None
        other_tree = partition_tree_witness(partition, tuple(name for name in feature_names if name != target), other) if root_compatible else None
        full_tree = None
        if candidate_tree is not None and other_tree is not None:
            full_tree = {"feature": parent, "zero": candidate_tree if side == 0 else other_tree, "one": other_tree if side == 0 else candidate_tree}
            possible_sides.append(side)
        candidates[str(side)] = {"branch_size": branch.bit_count(), "target_split_sizes": [target_zero.bit_count(), target_one.bit_count()], "target_branch_compatible": branch_compatible, "target_rooted_subtree_exists": candidate_tree is not None, "other_branch_without_target_exists": other_tree is not None, "tree_witness": full_tree}
    edge_direction = "predicted_side" if edge_side == 0 else "opposite_side" if edge_side == 1 else "not_applicable"
    parent_filtered_direction = edge_direction if parent_full_edges else "not_applicable"
    strict_side = edge_side if edge_side is not None and root_compatible and candidates[str(edge_side)]["tree_witness"] is not None else None
    strict_direction = "predicted_side" if strict_side == 0 else "opposite_side" if strict_side == 1 else "not_applicable"
    return {"parent": parent, "target": target, "basis": list(basis), "parent_full_edge_coverage": parent_full_edges, "root_compatible": root_compatible, "target_separated_count": profile["separated_count"], "edge_secondary_side": edge_side, "unfiltered_edge_direction": edge_direction, "parent_filtered_edge_direction": parent_filtered_direction, "strict_direction": strict_direction, "tree_possible_sides_without_edge_filter": possible_sides, "tree_direction_ambiguous_without_edge_filter": len(possible_sides) > 1, "candidates": candidates}


def strict_prediction_directions(labels: Sequence[object]) -> dict:
    """P2–P4严格根兼容结构见证，另保留边代理；每系统每命题一记录。"""
    specs = {"P2": ("a", "r", BASIS_RAW), "P3": ("r", "a", BASIS_RAW), "P4": ("q", "a", BASIS_RELATIVE)}
    diagnostics = {name: secondary_structure_witness(labels, parent, target, basis) for name, (parent, target, basis) in specs.items()}
    edge = prediction_directions(labels)
    tree_options = feature_tree_depth_options(labels_to_partition(labels))
    return {**{name: value["strict_direction"] for name, value in diagnostics.items()}, "P5_edge_proxy": edge["P5"], "P5_tree_status": tree_options["status"], "P5_separated_counts": edge["P5_separated_counts"], "P5_tree_depth_options": tree_options, "system_weight_per_prediction": 1, "selected_bases": edge["selected_bases"], "secondary_diagnostics": diagnostics, "P5_interpretation": "edge_proxy_and_all_single_leaf_tree_depth_options_reported_separately"}


def block_shape(partition: Sequence[int]) -> tuple[int, ...]:
    return tuple(sorted(block.bit_count() for block in partition))


def shape_universe_count(shape: Sequence[int]) -> int:
    denominator = 1
    for size in shape:
        denominator *= factorial(size)
    for multiplicity in Counter(shape).values():
        denominator *= factorial(multiplicity)
    return factorial(8) // denominator


# 直接对照A06 PDF15/19、印刷502的方括号及第一比例，未从TXT猜数。
# 2-3-3没有方括号；0只由Table2三词项汇总43反推，并另行标记。
PAPER_TABLE = {
    (8,): (1, 1), (4, 4): (6, 4),
    (1, 3, 4): (16, 0), (2, 2, 4): (27, 18), (2, 3, 3): (0, 0),
    (1, 1, 2, 4): (50, 32), (1, 1, 3, 3): (8, 0),
    (1, 2, 2, 3): (32, 0), (2, 2, 2, 2): (22, 16),
    (1, 1, 1, 1, 4): (12, 8), (1, 1, 1, 2, 3): (64, 0),
    (1, 1, 2, 2, 2): (88, 68), (1, 1, 1, 1, 1, 3): (8, 0),
    (1, 1, 1, 1, 2, 2): (89, 72),
    (1, 1, 1, 1, 1, 1, 2): (18, 16), (1, 1, 1, 1, 1, 1, 1, 1): (1, 1),
}


def known_examples() -> dict[str, tuple[object, ...]]:
    labels = {}
    labels["english_referent_sex"] = tuple(r for s, a, r in ATOMS)
    labels["age_by_referent_sex"] = tuple((a, r) for s, a, r in ATOMS)
    labels["relative_sex_only"] = tuple(s ^ r for s, a, r in ATOMS)
    labels["sex_split_only_elder"] = tuple((a, r if a == 0 else None) for s, a, r in ATOMS)
    labels["age_split_only_male"] = tuple((r, a if r == 0 else None) for s, a, r in ATOMS)
    labels["age_split_only_same_sex"] = tuple((s ^ r, a if (s ^ r) == 0 else None) for s, a, r in ATOMS)
    # Faris483 Table1表面同形；484 Table2按原作者多义重分析区分词义。
    # 这是文献中两个理论表示；不用于人工重编码数据库。
    labels["faris_surface_1_1_3_3"] = tuple((a, "tu" if s == 0 and r == 1 else "wau") for s, a, r in ATOMS)
    labels["faris_polysemy_1_1_1_1_2_2"] = tuple((s, a, r if s == 0 else None) for s, a, r in ATOMS)
    partition = partition_from_groups((("mome", "fofe"), ("momy",), ("fome", "mofe"), ("fofy", "fomy", "mofy")))
    labels["kronenfeld_491_nonconjunctive"] = partition_to_labels(partition)
    labels["two_diagonal_contexts"] = tuple(int(s == 1 and a == r) for s, a, r in ATOMS)
    labels["older_r_younger_q"] = tuple((a, r if a == 0 else s ^ r) for s, a, r in ATOMS)
    labels["older_q_younger_merged"] = tuple((a, s ^ r if a == 0 else None) for s, a, r in ATOMS)
    labels["older_female_versus_rest"] = tuple(int(a == 0 and r == 1) for s, a, r in ATOMS)
    return labels


def rational_rank(rows: Sequence[Sequence[int]]) -> int:
    matrix = [[Fraction(value) for value in row] for row in rows]
    rank = 0
    for column in range(len(matrix[0])):
        pivot = next((i for i in range(rank, len(matrix)) if matrix[i][column]), None)
        if pivot is None:
            continue
        matrix[rank], matrix[pivot] = matrix[pivot], matrix[rank]
        scale = matrix[rank][column]
        matrix[rank] = [value / scale for value in matrix[rank]]
        for i in range(rank + 1, len(matrix)):
            if matrix[i][column]:
                scale = matrix[i][column]
                matrix[i] = [left - scale * right for left, right in zip(matrix[i], matrix[rank])]
        rank += 1
    return rank


def endpoint_design_report() -> dict:
    """八个理论端点的28对；有理数高斯消元，不使用观测共享结果。"""
    rows = {"M0": [], "M1": [], "M2": [], "M4": []}
    for i, j in combinations(range(8), 2):
        ds, da, dr, dq = (FEATURES[name][i] ^ FEATURES[name][j] for name in ("s", "a", "r", "q"))
        main = [1, ds, da, dr]
        interaction = main + [ds * da, ds * dr, da * dr]
        elder = int(FEATURES["a"][i] == FEATURES["a"][j] == 0)
        male_relative = int(FEATURES["r"][i] == FEATURES["r"][j] == 0)
        same_sex = int(FEATURES["q"][i] == FEATURES["q"][j] == 0)
        male_ego = int(FEATURES["s"][i] == FEATURES["s"][j] == 0)
        rows["M0"].append(main)
        rows["M1"].append(main + [dq])
        rows["M2"].append(interaction)
        rows["M4"].append(interaction + [elder, male_relative, same_sex, male_ego, dr * elder, da * male_relative, da * same_sex])
    saturated = [[int(i == j) for j in range(28)] for i in range(28)]
    saturated_rank = rational_rank(saturated)
    joint_rank = rational_rank([left + right for left, right in zip(saturated, rows["M4"])])
    return {"n_theoretical_pairs": 28, "models": {name: {"columns": len(values[0]), "rank": rational_rank(values)} for name, values in rows.items()}, "M3_pair_indicator_rank": saturated_rank, "M3_M4_joint_rank": joint_rank, "M4_nested_in_M3": joint_rank == saturated_rank, "M4_column_names": ["intercept", "D_s", "D_a", "D_r", "D_sD_a", "D_sD_r", "D_aD_r", "E", "B", "S", "M", "D_rE", "D_aB", "D_aS"]}


def enumeration_report() -> dict:
    partitions = enumerate_partitions()
    feature_sets = {"three": BASIS_RAW, "four": FEATURES_FOUR, "six": FEATURES_SIX}
    hits = {name: [partition for partition in partitions if is_conjunctive(partition, feature_names)] for name, feature_names in feature_sets.items()}
    shape_counts = {name: Counter(block_shape(partition) for partition in values) for name, values in hits.items()}
    all_shapes = sorted(set(map(block_shape, partitions)), key=lambda shape: (len(shape), shape))
    table = []
    for shape in all_shapes:
        paper_six, paper_four = PAPER_TABLE.get(shape, (0, 0))
        table.append({"shape": list(shape), "all_partitions": shape_universe_count(shape), "three": shape_counts["three"][shape], "four": shape_counts["four"][shape], "six": shape_counts["six"][shape], "paper_four": paper_four, "paper_six": paper_six, "four_minus_paper": shape_counts["four"][shape] - paper_four, "six_minus_paper": shape_counts["six"][shape] - paper_six, "paper_cell_explicit": shape != (2, 3, 3)})
    examples = {}
    for name, labels in known_examples().items():
        partition = labels_to_partition(labels)
        examples[name] = {"partition": partition_codes(partition), "shape": list(block_shape(partition)), "conjunctive_four": is_conjunctive(partition), "conjunctive_six": is_conjunctive(partition, FEATURES_SIX), "tree_four": is_partition_tree(partition), "raw": evaluate_partition(labels, BASIS_RAW), "relative": evaluate_partition(labels, BASIS_RELATIVE), "predictions": prediction_directions(labels), "strict_predictions": strict_prediction_directions(labels)}
    first_non_tree = next(partition for partition in hits["four"] if not is_partition_tree(partition))
    return {"source_type": "pure_theory_no_empirical_files", "author_definition_choice": "pending", "kintype_bit_order": list(KINTYPES), "feature_values": {name: list(values) for name, values in FEATURES.items()}, "bell_number": len(partitions), "by_word_count": {str(k): value for k, value in sorted(Counter(len(p) for p in partitions).items())}, "conjunctive_counts": {name: len(values) for name, values in hits.items()}, "single_leaf_tree_counts": {name: len(tree_partitions(tuple(features))) for name, features in feature_sets.items()}, "balanced_single_leaf_tree_counts": {name: len(tree_partitions(tuple(features), True)) for name, features in feature_sets.items()}, "paper_counts": {"four": 236, "six": 442}, "table_1_comparison": table, "four_feature_non_tree_count": sum(not is_partition_tree(p) for p in hits["four"]), "first_four_feature_non_tree_example": partition_codes(first_non_tree), "examples": examples, "endpoint_design": endpoint_design_report(), "uniform_baselines": {name: {"numerator": len(values), "denominator": len(partitions), "probability": len(values) / len(partitions)} for name, values in hits.items()}}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--compact", action="store_true", help="只输出计数与理论设计秩")
    arguments = parser.parse_args()
    report = enumeration_report()
    if arguments.compact:
        report = {key: report[key] for key in ("source_type", "author_definition_choice", "bell_number", "conjunctive_counts", "single_leaf_tree_counts", "balanced_single_leaf_tree_counts", "paper_counts", "endpoint_design")}
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
