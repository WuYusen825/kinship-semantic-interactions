"""S2 运行前的纯抽象设计审计：不读取数据、词形、共享结果或已有结果文件。

运行：python analysis/supplementary_s2/design_rank.py
仅枚举八类别的 28 个无序对，以有理数消元输出精确秩与列保留顺序。
"""

from fractions import Fraction
from itertools import combinations
import json


CATEGORIES = ("meB", "myB", "meZ", "myZ", "feB", "fyB", "feZ", "fyZ")
M2_COLUMNS = ("intercept", "Dr", "Da", "De", "DrDa", "DrDe", "DaDe")
M4_COLUMNS = M2_COLUMNS + ("E", "B", "S", "M", "DrE", "DaB", "DaS")
REDUNDANT_DROP_ORDER = ("M", "DrE", "DaB", "DaS", "E", "B", "S")
HIERARCHY = {"DrE": "E", "DaB": "B", "DaS": "S"}


def exact_rank(rows):
    """有理数高斯消元；不使用数值容差判定 0/1 设计的可识别性。"""
    work = [[Fraction(value) for value in row] for row in rows]
    if not work:
        return 0
    pivot_row = 0
    for column in range(len(work[0])):
        found = next((i for i in range(pivot_row, len(work)) if work[i][column]), None)
        if found is None:
            continue
        work[pivot_row], work[found] = work[found], work[pivot_row]
        divisor = work[pivot_row][column]
        work[pivot_row] = [value / divisor for value in work[pivot_row]]
        for i in range(len(work)):
            if i != pivot_row and work[i][column]:
                multiplier = work[i][column]
                work[i] = [a - multiplier * b for a, b in zip(work[i], work[pivot_row])]
        pivot_row += 1
        if pivot_row == len(work):
            break
    return pivot_row


def endpoint(category):
    s = int(category[0] == "f")
    a = int(category[1] == "y")
    r = int(category[2] == "Z")
    return {"s": s, "a": a, "r": r, "q": s ^ r}


def abstract_rows():
    rows = []
    for first, second in combinations(CATEGORIES, 2):
        x, y = endpoint(first), endpoint(second)
        dr, da, de = (int(x[key] != y[key]) for key in ("r", "a", "s"))
        older = int(x["a"] == y["a"] == 0)
        male_referent = int(x["r"] == y["r"] == 0)
        same_sex = int(x["q"] == y["q"] == 0)
        male_ego = int(x["s"] == y["s"] == 0)
        values = (1, dr, da, de, dr * da, dr * de, da * de,
                  older, male_referent, same_sex, male_ego,
                  dr * older, da * male_referent, da * same_sex)
        rows.append({"category_a": first, "category_b": second,
                     **dict(zip(M4_COLUMNS, values))})
    return rows


def matrix(rows, columns):
    return [[row[column] for column in columns] for row in rows]


def main():
    rows = abstract_rows()
    m4 = matrix(rows, M4_COLUMNS)
    m3 = [[int(i == j) for j in range(28)] for i in range(28)]
    m1 = [[row["intercept"], row["Dr"], row["Da"], row["De"],
           row["Dr"] ^ row["De"]] for row in rows]
    retained = list(M4_COLUMNS)
    deleted = []
    rank_full = exact_rank(m4)
    for column in REDUNDANT_DROP_ORDER:
        candidate = [name for name in retained if name != column]
        hierarchy_holds = all(term not in candidate or main in candidate
                              for term, main in HIERARCHY.items())
        if hierarchy_holds and exact_rank(matrix(rows, candidate)) == rank_full:
            retained = candidate
            deleted.append(column)
    ranks = {
        "M0": exact_rank(matrix(rows, M2_COLUMNS[:4])),
        "M1": exact_rank(m1),
        "M2": exact_rank(matrix(rows, M2_COLUMNS)),
        "M3": exact_rank(m3),
        "M4": rank_full,
        "M3_augmented_M4": exact_rank([a + b for a, b in zip(m3, m4)]),
    }
    result = {
        "scope": "仅枚举抽象类别对；未读取任何文件、词形或共享结果。",
        "categories": CATEGORIES,
        "unordered_pairs": len(rows),
        "ranks": ranks,
        "M4_column_order": M4_COLUMNS,
        "prefix_ranks": {column: exact_rank([row[:i + 1] for row in m4])
                         for i, column in enumerate(M4_COLUMNS)},
        "redundant_drop_order": REDUNDANT_DROP_ORDER,
        "dropped_columns": deleted,
        "retained_columns": retained,
        "M4_nested_in_M3": ranks["M3_augmented_M4"] == ranks["M3"],
        "strict_inclusion_M2_M4_M3": ranks["M2"] < ranks["M4"] < ranks["M3"],
        "abstract_design_rows": rows,
    }
    assert len(rows) == 28
    assert ranks == {"M0": 4, "M1": 5, "M2": 7, "M3": 28, "M4": 14,
                     "M3_augmented_M4": 28}
    assert not deleted
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
