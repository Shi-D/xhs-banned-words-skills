# 小红书违禁词 Skills（xhs-banned-words-skills）

> 给 AI 写作助手用的「小红书违禁词」技能包：**检测违禁词** + **协助 AI 写文时自动避开违禁词**。
> 适用于 Claude Code、OpenAI Codex CLI，以及任何支持 [Agent Skills（SKILL.md）](https://agentskills.io) 标准的工具；不支持 skill 的 AI 工具也可以直接复制使用。

- 📚 **10 套词库，约 1100 条**：全平台通用红线 + 9 个行业专项
- 🏷️ 每个词都带 **风险等级（高危 / 中危 / 低危）** 和 **合规替换建议**
- 🔍 自带零依赖检测脚本：识别全角字符、**“微 信”“v·x” 这类拆分写法**，内置“第一次”“最近”等常见误报例外
- ✍️ 写作守则 + 改写示例：让 AI 一开始就写出合规文案，写完再自检

---

## 目录

- [包含哪些 Skill](#包含哪些-skill)
- [安装](#安装)
- [如何使用](#如何使用)
- [检测脚本命令行用法](#检测脚本命令行用法)
- [仓库结构](#仓库结构)
- [自定义与贡献词库](#自定义与贡献词库)
- [免责声明](#免责声明)

---

## 包含哪些 Skill

| Skill | 行业 | 覆盖内容 |
|---|---|---|
| **`xhs-banned-words`** | ⭐ 总 skill（全行业） | 包含下面全部词库，自动判断行业，适合多赛道博主或不确定行业时使用 |
| `xhs-banned-words-beauty` | 美妆个护 | 医疗术语、特殊化妆品功效、安全夸大、违规成分、婴儿/孕妇可用 |
| `xhs-banned-words-medical` | 医疗健康 / 医美 | 疾病治疗、疾病名、诊疗手段、医美项目、患者案例、“三品一械” |
| `xhs-banned-words-food` | 食品 / 滋补 / 保健品 | 疾病功效、保健功能（蓝帽子）、中医调理、珍稀食材、0 卡无糖 |
| `xhs-banned-words-maternal` | 母婴育儿 | 母乳替代、智力发育、医疗功效、医用级/防辐射、育儿焦虑、儿童隐私 |
| `xhs-banned-words-education` | 教育培训 | 保过包过、速成、就业收入承诺、内部押题、学历考证、K12 双减 |
| `xhs-banned-words-finance` | 金融理财 | 保本收益、贷款信贷、非法荐股、虚拟货币、暴富人设、引流拉群 |
| `xhs-banned-words-home` | 家居装修 / 清洁 | 零甲醛、杀菌抗菌、永久防霉、无法破解、零增项 |
| `xhs-banned-words-fashion` | 服饰珠宝 / 奢侈品 | 材质宣称、正品承诺、原单复刻平替、保值升值、迷信、线下交易 |
| `xhs-banned-words-pet` | 宠物经济 | 治病防病、兽医推荐、原料安全、发腮、包教会、活体交易 |

每个行业 skill 都**同时包含全平台通用词库**（极限词、承诺保证、虚假背书、站外导流、营销诱导、封建迷信、医疗功效、标题党），可以单独安装使用。

**怎么选？**

- 只做一个赛道 → 装对应的行业 skill，触发更精准
- 多个赛道 / 帮别人代写 / 不确定 → 装总 skill `xhs-banned-words`
- 全都装也没问题，AI 会按描述自动挑选

---

## 安装

先把仓库下载到本地：

```bash
git clone https://github.com/<your-name>/xhs-banned-words-skills.git
cd xhs-banned-words-skills
```

### 方式一：一键安装脚本（macOS / Linux）

```bash
./install.sh                     # 全部 skill → Claude Code（~/.claude/skills）
./install.sh codex               # 全部 skill → Codex CLI（~/.codex/skills）
./install.sh all                 # 同时装到 Claude Code 和 Codex
./install.sh project             # 装到当前项目的 .claude/skills（团队共享）
./install.sh claude beauty food  # 只装 美妆 + 食品 两个行业 skill
./install.sh claude overall      # 只装总 skill
./install.sh /任意/目录           # 装到自定义目录
```

安装后**重启** Claude Code / Codex 生效。

### 方式二：手动复制

每个 skill 文件夹都是自包含的（`SKILL.md` + `references/` + `scripts/`），直接复制即可：

| 工具 | 个人级（所有项目可用） | 项目级（随仓库共享） |
|---|---|---|
| **Claude Code** | `~/.claude/skills/<skill名>/` | `<项目>/.claude/skills/<skill名>/` |
| **Codex CLI** | `~/.codex/skills/<skill名>/` | 以 Codex 官方文档为准 |
| 其它支持 Agent Skills 的工具 | 按该工具文档放置 skill 文件夹 | — |

```bash
# 例：只给 Claude Code 装美妆 skill
cp -R skills/xhs-banned-words-beauty ~/.claude/skills/
```

Windows 用户：把 `skills\` 下需要的文件夹复制到 `%USERPROFILE%\.claude\skills\` 或 `%USERPROFILE%\.codex\skills\`。

### 方式三：不支持 Skill 的 AI 工具（ChatGPT 网页版、Cursor、Kimi、豆包等）

- **当作提示词**：把对应 `SKILL.md` 的正文粘贴进对话 / 自定义指令 / 项目规则（如 Cursor 的 `.cursor/rules`、仓库的 `AGENTS.md`），再把 `references/*.txt` 作为附件上传。
- **只用脚本**：不依赖任何 AI，直接用命令行检测（见下文）。

### 环境要求

- 检测脚本需要 **Python 3.8+**，无第三方依赖。
- 没有 Python 也能用：AI 会改为直接阅读 `references/*.txt` 人工对照（效果略差，速度略慢）。

---

## 如何使用

安装后**不需要记任何命令**，用自然语言跟 AI 说就行。AI 会根据 skill 的描述自动触发；也可以在 Claude Code 里输入 `/xhs-banned-words` 等 skill 名手动调用。

### 场景 1：检测已有文案

```
帮我检查这篇小红书笔记有没有违禁词：
【标题】全网最好用的美白精华！7天见效
【正文】……
```

AI 会：判断行业 → 运行检测脚本 → 语义复核（找脚本漏掉的隐性违规）→ 输出

1. **风险概览**：高危 / 中危 / 低危各几处
2. **问题清单**：原词 → 原因 → 建议替换
3. **改写后的完整文案**（保留你的语气、排版和 emoji）
4. **需要你确认的事项**（例如产品有没有备案、检测报告、品牌授权）

### 场景 2：让 AI 直接写合规文案

```
帮我写一篇小红书种草笔记，产品是一款黑芝麻丸，突出早餐场景，口语化一点，带 emoji
```

AI 会先读对应行业（这里是食品）的红线和替换表再动笔，写完**自动跑一次自检**，并告诉你结果，例如：

> 已自检（food）：0 高危，0 中危。

### 场景 3：问某个词能不能用

```
小红书上写"修复肌肤屏障"会被限流吗？
"零添加"在食品笔记里能用吗？
```

### 场景 4：批量检查 / 改写

```
把 drafts/ 目录下所有 md 文件都检查一遍，只列高危
把这 5 篇笔记的违禁词都改掉，保持原来的风格
```

### 示例效果

改写前：

> 全网最好用的美白精华！7天美白，还能消炎祛痘，敏感肌、孕妇都能用，100%纯天然无刺激！

检测结果（节选）：

| 风险 | 命中 | 分类 | 建议替换 |
|---|---|---|---|
| 高危 | 最好 | 通用·极限词 | 很好、蛮适合我、口碑不错 |
| 高危 | 7天美白 | 美妆·速效承诺 | 坚持使用有改善 |
| 高危 | 消炎 | 美妆·医疗术语 | 舒缓泛红、改善肌肤不适 |
| 高危 | 100%纯天然 | 美妆·安全夸大 | 天然原料、成分温和 |
| 高危 | 无刺激 | 美妆·安全夸大 | 温和亲肤（需有报告） |
| 中危 | 美白 | 美妆·需注册的功效词 | 提亮肤色、匀净肤色 |
| 中危 | 祛痘 | 美妆·需注册的功效词 | 舒缓痘肌、对痘痘友好 |

改写后：

> 最近蛮常用的一瓶提亮精华，坚持用了一段时间，我觉得肤色看起来更匀净了，用着也挺温和的。（个人肤质感受，仅供参考）

---

## 检测脚本命令行用法

脚本也可以脱离 AI 单独使用。仓库根目录的 `tools/xhs_check.py` 需要用 `--wordlist-dir wordlists` 指定词库；`skills/*/scripts/xhs_check.py` 会自动读取同一 skill 下的 `references/`。

```bash
cd skills/xhs-banned-words

python3 scripts/xhs_check.py 笔记.md                         # 检测文件（全行业）
python3 scripts/xhs_check.py --text "全网第一的面霜"           # 检测一段文字
cat 笔记.md | python3 scripts/xhs_check.py                   # 从标准输入读取
python3 scripts/xhs_check.py 笔记.md --industry beauty,food  # 只用 通用 + 指定行业
python3 scripts/xhs_check.py 笔记.md --annotate              # 在原文中用【】标出问题
python3 scripts/xhs_check.py 笔记.md --min-risk 高危          # 只看高危
python3 scripts/xhs_check.py 笔记.md --format markdown       # 输出 Markdown 表格
python3 scripts/xhs_check.py 笔记.md --format json           # 输出 JSON
python3 scripts/xhs_check.py *.md                            # 批量检测
python3 scripts/xhs_check.py --list-industries               # 查看可用词库
```

| 参数 | 说明 |
|---|---|
| `files` | 要检测的文件，可多个；不填则读 `--text` 或标准输入 |
| `--text` | 直接检测一段文字 |
| `--industry` | 只启用指定行业（逗号分隔）：`beauty` `medical` `food` `maternal` `education` `finance` `home` `fashion` `pet`；通用词库始终启用 |
| `--no-general` | 不启用通用词库 |
| `--min-risk` | `高危` / `中危` / `低危`（默认全部） |
| `--format` | `text`（默认）/ `markdown` / `json` |
| `--annotate` | 额外输出标注后的原文 |
| `--wordlist-dir` | 自定义词库目录 |

**退出码**：发现高危词返回 `1`，否则 `0`，可以接入 CI、Git pre-commit 或批量脚本。

---

## 仓库结构

```
xhs-banned-words-skills/
├── README.md
├── LICENSE
├── install.sh                  # 一键安装
├── skills/                     # ← 可直接分发的 skill（由 tools/build.py 生成）
│   ├── xhs-banned-words/       #   总 skill（SKILL.md 手写 + 全部词库）
│   │   ├── SKILL.md
│   │   ├── references/*.txt
│   │   └── scripts/xhs_check.py
│   ├── xhs-banned-words-beauty/
│   │   ├── SKILL.md
│   │   ├── references/general.txt
│   │   ├── references/beauty.txt
│   │   └── scripts/xhs_check.py
│   └── …（共 9 个行业）
├── wordlists/                  # ← 词库唯一源头，改词改这里
│   ├── README.md               #   词库格式说明
│   ├── general.txt
│   └── beauty.txt / medical.txt / food.txt / …
├── tools/
│   ├── xhs_check.py            # 检测脚本源文件
│   └── build.py                # 把词库和脚本同步到 skills/，并生成行业 SKILL.md
├── tests/test_checker.py
└── docs/sources/               # 词库整理所依据的原始笔记
```

---

## 自定义与贡献词库

1. 编辑 `wordlists/` 下对应的 `.txt`（格式见 [wordlists/README.md](wordlists/README.md)）：

   ```
   ## 分类名 [高危]
   违禁词 | 替换建议1、替换建议2 | 例外词1、例外词2
   re:正则表达式 | 替换建议
   ```

2. 想新增行业：新建 `wordlists/<行业>.txt`，并在 `tools/build.py` 的 `INDUSTRIES` 里加上该行业的标题、触发场景、核心规则、替换表和改写示例。
3. 重新生成并测试：

   ```bash
   python3 tools/build.py
   python3 -m unittest discover tests
   ```

4. 提交 PR。欢迎补充新词、新行业（如旅游出行、数码家电、汽车、本地生活），或报告误报 / 漏报。

> 行业 skill 的 `SKILL.md` 由 `build.py` 生成，请改 `build.py` 里的模板/配置，不要直接改生成的文件；总 skill 的 `skills/xhs-banned-words/SKILL.md` 是手写的，可直接编辑。

---

## 免责声明

- 词库根据《广告法》《化妆品监督管理条例》等公开法规、平台公开规则及创作者经验整理，**不是小红书官方清单**。
- 平台规则持续变化，审核也会结合语义、图片、账号资质综合判断，**本工具无法保证内容一定不被限流**。
- 涉及资质、功效、法律问题时，请以法规原文和小红书官方规则为准，必要时咨询专业人士。

## License

[MIT](LICENSE)
# xhs-banned-words-skills
