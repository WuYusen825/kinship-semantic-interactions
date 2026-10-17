# 八位置、划分编码与描述成本

以下位序完整沿用S2的`ATOMS`与`KINTYPES`。s/a/r的0依次表示男性参照者、所指者年长、男性所指者；q=s XOR r，q=0表示同性。mask中的第i位为位置i。数据表的排列次序不作为逻辑位置次序。

| 位置i | s | a | r | q | Kinbank类别 | S2类别 |
|---:|---:|---:|---:|---:|---|---|
| 0 | 0 | 0 | 0 | 0 | meB | mome |
| 1 | 0 | 0 | 1 | 1 | meZ | mofe |
| 2 | 0 | 1 | 0 | 0 | myB | momy |
| 3 | 0 | 1 | 1 | 1 | myZ | mofy |
| 4 | 1 | 0 | 0 | 1 | feB | fome |
| 5 | 1 | 0 | 1 | 0 | feZ | fofe |
| 6 | 1 | 1 | 0 | 1 | fyB | fomy |
| 7 | 1 | 1 | 1 | 0 | fyZ | fofy |

## 划分ID与块表示

RGS按首次出现的块依次编号0、1、…，以八位字符串保存；全部合法RGS按字典序分配partition_id=0–4139。块mask按整数升序保存，因而与S2的canonical_partition一致；labels为上述位序的RGS，s2_labels另保存旧函数按mask升序编号的类标签。两种标签的数字名称可以不同，同类关系完全相同。读取CSV应强制rgs为字符串，保留前导零。

例：仅按所指者性别区分的RGS为01010101，块mask为85与170；仅按同性／异性区分的RGS为01011010，块mask为90与165。不要将RGS中的类编号误作亲属属性。

## 四种描述语言和成本

L_abs={s,a,r}；L_rel_r={q,a,r}；L_rel_s={q,a,s}；L_all={s,a,r,q}。精确DL为各词项块最短DNF的文字数之和；真式即全集的文字数为0。合取项允许重叠，文字成本按每项的特征取值数相加，不另给括号、连接符或词项名称计费。该DNF成本与旧S2最小分类树边数是不同指标。

## 三种系统映射与分折

strict是625个每类单词形系统；equal_sets对939系统取完整词形集合相等的等价类；components对939系统取D1共享图的连通分量。后两者都不是把非传递D1关系直接当作划分。每行保留按类别存储的forms_json、定义文本与来源样本标识。

fold_family和fold_language从原939系统的冻结primary预测读取并逐系统继承，不对625子样本重新平衡。macroarea/Macroarea_first均为首个原始宏观区域，缺失保持空串；Macroarea与macroarea_raw保存原字段。地域缺失系统只从地域验证排除。

类别对索引见results/t1/pair_design_metadata.csv，其pair_index按旧pair_type字符串排序；atom_i/atom_j连接本表位置。旧七差异单元的位次仍为Dr、Da、De，M2列仍为intercept、Dr、Da、De、DrDa、DrDe、DaDe。
