# 数据库测量字段核查记录

范围：只读已知的 `forum_descriptives.json`、冻结 `results.json`、三个例证语言的既有 CLDF 行、上游原始CSV及导出代码；没有写或运行新的S2共享结果统计、模型或违例判定。总结见 [数据测量复核](../outputs/数据测量复核.md)。

## 版本与文件身份

- Kinbank commit：`925cc0e702ae5481cfe0088aaa0e69c3991000f3`。
- 主要字段表：[forms.csv](../data/kinbank/kinbank/cldf/forms.csv)，SHA-256 `7d1238a69a8ac2f8e4b70b9bca797ad50bf85519fa26acc72fb571e067f01664`。
- 参数字典：[parameters.csv](../data/kinbank/kinbank/cldf/parameters.csv)。`meB/myB/meZ/myZ` 与女性参照者四类有相对年龄；`mB/fB/mZ/fZ` 不含年龄。代码名是比较网格，不保证每条注释完全同粒度。
- 既有描述：[forum_descriptives.json](../analysis/forum_descriptives.json)，SHA-256 `b4fdb778b2d056b53b971e0bfceaaf6f8c902dad06ff84304533d33d0197d8d8`。本次未运行生成脚本。
- 来源目录：[sources.bib](../data/kinbank/kinbank/cldf/sources.bib)。以下 bibliographic 条目是数据库自带元数据，不等于本项目已取得这些原始资料全文。

## 直接证据与其解释界限

| 证据 | 直接可核查事实 | 解释界限 |
|---|---|---|
| 法语 `meB/feB` 的 `ainé` | 两行 `Comment=first born son`，Source为Clifford2018 | 注释与older brother代码不同粒度；尚未确认哪个环节需要更正 |
| 法语 `meZ/feZ` 的 `ainée` | 两行 `Comment=first born daughter`，Source为Diniz1977 | 不能把整个年龄四格都归给Clifford2018 |
| 西班牙语八个细类 | `hermano/hermana mayor/menor`，Source为Blanco采访资料，注释含 `TRAD LIT` | 可说数据库记录了这些表达，不能据此量化语言的基本词数 |
| 西班牙语四个粗类 | `hermano/hermana`，Source为Diniz1977 | 不能事后自动补入其他来源的细类别 |
| 普通话八个细类 | 重复转写与哥哥／弟弟／姐姐／妹妹注释，Source为Chen2019 | 空格不等于描述短语；不执行人工词素切分 |
| 普通话四个粗类 | `xiong di/jie mei`，兄弟／姐妹注释，Source为空 | 不确认其精确指称，也不填入未经证实的来源 |
| 960含空格形式／179系统 | 原有JSON明确保存；生成脚本将每语言每类别的集合成员连成列表计数 | 不是全球唯一形式种数，也不是描述性短语计数 |

## 来源键逐项定位

| Source键 | `sources.bib`位置 | 数据库登记的作者／题名／年份 | 已确认事项 |
|---|---|---|---|
| `clifford_french_2018` | 第1164行起 | Isobel Clifford；*French (Stan1290) and Spanish (Stan1288) Kinship Terms Collected from a Speaker*；2018 | 数据库登记为说话者采集资料，未提供可在本复核中核对的发表页码 |
| `diniz_os_1977` | 第1634行起 | Beatriz Diniz；*Os termos do parentesco em armênio*；1977 | 法／西粗条目及部分法语细条目链接此键；书名不构成引文误配的证明，原书内容待核 |
| `blanco_stan1288_nodate` | 第553行起 | Hugo Garcia Blanco；*Stan1288 Terms Collected from an Interview with Speaker*；无年份字段 | 西班牙语细类链接此键；`nodate`不能改写成推测年份 |
| `Chen_2019` | 第17646行起 | Chen Chen；*A Comparative Study on English and Chinese Kinship Terms and Their Translation Strategies*；2019；*Theory and Practice in Language Studies* 9(9):1237–1242；DOI 10.17507/tpls.0909.22 | 这是数据库引文元数据，未在此任务新增该文全文或把它加入正式参考文献 |

注释中的 `[80]`／`[398]` 与上游 `source_raw=IE80/IE398`、引文关键词相对应，不能未经原资料核对就当印刷页码。普通话上游 `source_raw=1238` 也须按原字段保留，不能只因其落入文章页码范围就标为已核对页码。

## 上游路径、机制与证据强度

当前GitHub工作副本只保存分析必需的CLDF文件，未包含上游全部代码／raw文件。本次只读了同一锁定commit的既存完整镜像 `/workspace/kinship_research/data/kinbank`，用 `git rev-parse HEAD` 确认为上述commit；没有复制或修改上游代码。

- [锁定导出脚本](https://github.com/kinbank/kinbank/blob/925cc0e702ae5481cfe0088aaa0e69c3991000f3/kinbank/lexibank_kinbank.py)：第36–40行配置FormSpec；第60–76行逐行读取 `parameter`，优先 `ipa` 否则 `word`，并传入 `comment/source_bibtex`。SHA-256 `2353ebd06f0f7d06a3dc9ed5fc5f23fd679a451ff1983bd417521cb17b51bb49`。
- [锁定合并脚本](https://github.com/kinbank/kinbank/blob/925cc0e702ae5481cfe0088aaa0e69c3991000f3/merge_collections.py)：合并子项目已有文件与元数据；SHA-256 `c6710e33f3ad28137ff48469b0f52194a6b9c1cdce8dc1434340629da9ee4ba9`。这些代码不提供逐个细格“独立调查／源自展开”的标记。
- 上游法语raw：[Standard_French_stan1290.csv](https://github.com/kinbank/kinbank/blob/925cc0e702ae5481cfe0088aaa0e69c3991000f3/kinbank/raw/Indo-European/Standard_French_stan1290.csv)。所核查的年长兄行在导出前已写成 `meB/feB`，不是本项目清洗阶段新填入。
- 上游西班牙语raw：[Standard_Spanish_stan1288.csv](https://github.com/kinbank/kinbank/blob/925cc0e702ae5481cfe0088aaa0e69c3991000f3/kinbank/raw/Indo-European/Standard_Spanish_stan1288.csv)。八个年龄细类在raw中已有，注释与 `IE398` 等来源标识可直接复查。
- 上游普通话raw：[Mandarin_China_mand1415.csv](https://github.com/kinbank/kinbank/blob/925cc0e702ae5481cfe0088aaa0e69c3991000f3/kinbank/raw/Sino-Tibetan/Mandarin_China_mand1415.csv)。`ge ge` 与“哥哥”等注释在raw中已经并列。
- [Form处理说明](../data/kinbank/kinbank/FORMS.md)规定上游切分符号为 `;/,`，会处理括号、合并空白，未配置Unicode正规化；本项目随后仅作NFC与空白处理（`analysis/audit.py:12`）。本项目取同类全部有效Form成集合（`analysis/analyze.py:26`），不重新按粗类填值。

粗到细的展开有公开方法依据：A09（Passmore et al.2023）PDF第7页／印刷页7“Collection procedure”，说明粗类父亲的兄弟在无进一步信息时填入四个细格。该说明不能逐行识别本次样本中哪些兄弟姐妹条目经历过展开。

词项／词素／修饰构式区别的全文依据为A17（Kronenfeld2006）PDF第15页／印刷页216“Typological Base 6”。该段具体比较西班牙语 `herman-`、`-o/-a` 与芳蒂语修饰手段，支持测量层次区分，不支持对未核对的数据库词形人工纠正。

两处均在现有TXT定位后，读取现有PDF的相应单页输出作核对；准确命令如下，`-`表示写到标准输出，没有改写文件：

```bash
pdftotext -f 7 -l 7 -layout literature/A/A09_Passmore_2023_Kinbank_A_Global_Database_of_Kinship_Terminology.pdf -
pdftotext -f 15 -l 15 -layout literature/A/A17_Kronenfeld_2006_Issues_in_the_Classification_of_Kinship_Terminologies_Toward_a_New_Typology.pdf -
git -C /workspace/kinship_research/data/kinbank rev-parse HEAD
```

## 字段查验与后续抽查的边界

本任务只用 `pandas.read_csv(..., keep_default_na=False)` 读取原表，并按既知语言ID、十二个粗细类别筛行，显示 `ID/Language_ID/Parameter_ID/Value/Form/Comment/Source`；没有从这些行另生成共享结果或模型输入。下面“物理行号”由文本搜索获得，以锁定文件为准；稳定识别应使用记录ID而非CSV行号，因为CSV引用字段可能跨物理行。

S2至少20个违例系统的透明抽查规则见复核正文第7节，属于供协议采用的建议，不表示已经抽取或检查违例。仅凭现有字段，最终只能确认“数据库编码下的形式违例”及明确的质量线索；没有原资料语境、无法排除粒度问题或来源不完整时，必须记“无法判断”，不得声称已确认真实语义反例。

## 三个例证语言的原始记录明细

### 法语：`v_standardfrenchstan1290`

| 记录ID | 物理行 | 类别 | Value | Form | Comment | Source |
|---|---:|---|---|---|---|---|
| v_standardfrenchstan1290-meB-1 | 115631 | meB | ainé | ainé | first born son | clifford_french_2018 |
| v_standardfrenchstan1290-myB-1 | 115663 | myB | frère | frère | frère "brother" [80] | diniz_os_1977 |
| v_standardfrenchstan1290-meZ-1 | 115664 | meZ | ainée | ainée | first born daughter | diniz_os_1977 |
| v_standardfrenchstan1290-myZ-1 | 115665 | myZ | soeur | soeur | soeur "sister" [80] | diniz_os_1977 |
| v_standardfrenchstan1290-feB-1 | 115646 | feB | ainé | ainé | first born son | clifford_french_2018 |
| v_standardfrenchstan1290-fyB-1 | 115762 | fyB | frère | frère | frère "brother" [80] | diniz_os_1977 |
| v_standardfrenchstan1290-feZ-1 | 115763 | feZ | ainée | ainée | first born daughter | diniz_os_1977 |
| v_standardfrenchstan1290-fyZ-1 | 115764 | fyZ | soeur | soeur | soeur "sister" [80] | diniz_os_1977 |
| v_standardfrenchstan1290-mB-1 | 115661 | mB | frère | frère | frère "brother" [80] | diniz_os_1977 |
| v_standardfrenchstan1290-mZ-1 | 115662 | mZ | soeur | soeur | soeur "sister" [80] | diniz_os_1977 |
| v_standardfrenchstan1290-fB-1 | 115760 | fB | frère | frère | frère "brother" [80] | diniz_os_1977 |
| v_standardfrenchstan1290-fZ-1 | 115761 | fZ | soeur | soeur | soeur "sister" [80] | diniz_os_1977 |

### 西班牙语：`v_standardspanishstan1288`

| 记录ID | 物理行 | 类别 | Value | Form | Comment | Source |
|---|---:|---|---|---|---|---|
| v_standardspanishstan1288-meB-1 | 116294 | meB | hermano mayor | hermano mayor | TRAD LIThermano mayor "elder brother" [398] | blanco_stan1288_nodate |
| v_standardspanishstan1288-myB-1 | 116295 | myB | hermano menor | hermano menor | TRAD LIThermano menor "younger brother" [398] | blanco_stan1288_nodate |
| v_standardspanishstan1288-meZ-1 | 116296 | meZ | hermana mayor | hermana mayor | TRAD LIThermana mayor "elder sister" [398] | blanco_stan1288_nodate |
| v_standardspanishstan1288-myZ-1 | 116297 | myZ | hermana menor | hermana menor | TRAD LIThermana menor "younger sister" [398] | blanco_stan1288_nodate |
| v_standardspanishstan1288-feB-1 | 116303 | feB | hermano mayor | hermano mayor | TRAD LIThermano mayor "elder brother" [398] | blanco_stan1288_nodate |
| v_standardspanishstan1288-fyB-1 | 116304 | fyB | hermano menor | hermano menor | TRAD LIThermano menor "younger brother" [398] | blanco_stan1288_nodate |
| v_standardspanishstan1288-feZ-1 | 116305 | feZ | hermana mayor | hermana mayor | TRAD LIThermana mayor "elder sister" [398] | blanco_stan1288_nodate |
| v_standardspanishstan1288-fyZ-1 | 116306 | fyZ | hermana menor | hermana menor | TRAD LIThermana menor "younger sister" [398] | blanco_stan1288_nodate |
| v_standardspanishstan1288-mB-1 | 116317 | mB | hermano | hermano | hermano "brother" [80] | diniz_os_1977 |
| v_standardspanishstan1288-mZ-1 | 116318 | mZ | hermana | hermana | hermana "sister" [80] | diniz_os_1977 |
| v_standardspanishstan1288-fB-1 | 116413 | fB | hermano | hermano | hermano "brother" [80] | diniz_os_1977 |
| v_standardspanishstan1288-fZ-1 | 116414 | fZ | hermana | hermana | hermana "sister" [80] | diniz_os_1977 |

### 普通话：`v_mandarinchinamand1415`

| 记录ID | 物理行 | 类别 | Value | Form | Comment | Source |
|---|---:|---|---|---|---|---|
| v_mandarinchinamand1415-meB-1 | 200653 | meB | ge ge | ge ge | 哥哥 | Chen_2019 |
| v_mandarinchinamand1415-myB-1 | 200654 | myB | di di | di di | 弟弟 | Chen_2019 |
| v_mandarinchinamand1415-meZ-1 | 200655 | meZ | jie jie | jie jie | 姐姐 | Chen_2019 |
| v_mandarinchinamand1415-myZ-1 | 200656 | myZ | mei mei | mei mei | 妹妹 | Chen_2019 |
| v_mandarinchinamand1415-feB-1 | 200709 | feB | ge ge | ge ge | 哥哥 | Chen_2019 |
| v_mandarinchinamand1415-fyB-1 | 200710 | fyB | di di | di di | 弟弟 | Chen_2019 |
| v_mandarinchinamand1415-feZ-1 | 200711 | feZ | jie jie | jie jie | 姐姐 | Chen_2019 |
| v_mandarinchinamand1415-fyZ-1 | 200712 | fyZ | mei mei | mei mei | 妹妹 | Chen_2019 |
| v_mandarinchinamand1415-mB-1 | 200651 | mB | xiong di | xiong di | 兄弟 | 〔空〕 |
| v_mandarinchinamand1415-mZ-1 | 200652 | mZ | jie mei | jie mei | 姐妹 | 〔空〕 |
| v_mandarinchinamand1415-fB-1 | 200707 | fB | xiong di | xiong di | 兄弟 | 〔空〕 |
| v_mandarinchinamand1415-fZ-1 | 200708 | fZ | jie mei | jie mei | 姐妹 | 〔空〕 |

