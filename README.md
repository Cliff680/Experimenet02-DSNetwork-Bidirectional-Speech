# 实验二 数字交换网络与双向话路配置

在实验一比较资源服务方式的基础上，本次用T接线器改变时隙、用S接线器改变链路，建立真正执行字节传送的双向话路，为期末数字程控交换机提供交换数据面。

建议120分钟。教师提供帧、端口、时钟、绘图和测试；学生补全4个函数。无需网页、真实电话或麦克风。

配套[Word实验规范与操作指南](materials/实验二_PRD_数字交换网络与双向话路配置.docx)、[16页讲授课件](materials/实验二_数字交换网络与双向话路_教师讲授版.pptx)与[自动成绩看板](https://github.com/jwentong/Experimenet02-DSNetwork-Bidirectional-Speech/issues/1)。

## 1 获取与运行

先Fork本仓库，再Clone个人Fork，将YOUR-USERNAME替换为自己的账号。

```powershell
git clone https://github.com/YOUR-USERNAME/Experimenet02-DSNetwork-Bidirectional-Speech.git
cd Experimenet02-DSNetwork-Bidirectional-Speech
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m src.test_environment
.\.venv\Scripts\python.exe -m pytest grading/test_environment.py -q
```

上面2项环境测试应通过。核心函数初始为NotImplementedError，核心测试失败是待完成状态，不要删除或修改教师测试。所有命令在含src、grading、requirements.txt的项目根目录执行。

## 2 统一模型

- 两条输入、两条输出链路，每帧32个8 bit PCM样本，帧率8000帧/s，总码率每链路2.048 Mbit/s。
- TS0、TS16保留，其他为业务时隙；保留字节在本模型原位透传，不实现真实E1帧同步或信令。
- 控制表统一写“输出→输入”；链路号、时隙号从0开始。未连接业务输出填IDLE=0xD5，不能凭字节值判断资源是否空闲。
- T采用整帧缓存，输入帧k的结果在输出帧k+1可用，固定一帧125 μs；S不再追加一帧。本约定不是所有真实T接线器的物理延迟。
- 基础路径固定先T后S。端口空闲也可能发生内部T资源冲突，应拒绝本次连接，不要求自动寻找其他路径。

完整表项与冲突约定见docs/model_contract.md。

## 3 四个任务

|文件|函数|要求|
|---|---|---|
|src/t_switch.py|t_switch|同一链路按out_ts→in_ts重排|
|src/s_switch.py|s_switch|同一时隙选择输入链路|
|src/connections.py|connect_pair|先检查两个方向，再一起写表|
|src/connections.py|disconnect_pair|只释放指定连接，重复释放返回False|

教师提供的models、engine和run_experiment应保持不变。先读函数docstring，再手算，再使用AI辅助实现；一次只完成一个函数。

## 4 手算与验证

1. T单元交换TS1与TS3，写出输入和输出字节。
2. S单元在TS3交换链路0、1，解释为什么时隙号没变。
3. C1连接A=(0,1)、B=(1,5)：A→B需要T0[5]=1、S[(1,5)]=0；B→A需要T1[1]=5、S[(0,1)]=1。
4. 再建立C2：C=(0,2)、D=(1,6)。验证两对并存、争用已占端口时原表不变、释放C1后C2仍传送、资源可重用。

```powershell
.\.venv\Scripts\python.exe -m pytest grading/test_t.py -q
.\.venv\Scripts\python.exe -m pytest grading/test_s.py -q
.\.venv\Scripts\python.exe -m pytest grading/test_connect.py -q
.\.venv\Scripts\python.exe -m pytest grading/test_disconnect.py -q
.\.venv\Scripts\python.exe -m pytest grading/test_integration.py -q
.\.venv\Scripts\python.exe -m src.run_experiment
```

应生成results/switch_mapping.png、control_tables.json、transfer_check.json。4帧×2连接×2方向=16次校验，mismatches应为0。实现有误时框架会明确报错，不会生成假成功结果。

## 5 报告与自拟测试

可下载[学生实验报告模板（Word）](materials/实验二_学生实验报告模板.docx)组织完整报告；自动评分仍读取REPORT.md和AI_LOG.md，请将对应内容同步到这两个文件。

首次复制REPORT_TEMPLATE.md为REPORT.md、AI_LOG_TEMPLATE.md为AI_LOG.md；已有内容时不要重复覆盖。报告写明原理与手算、结果分析、反例与验证、局限，至少300字/字符量级；AI记录至少120字符并保留需求、建议与采纳、验证证据三节。未使用AI如实写独立实现过程。

在student_tests/test_my_case.py写自己的反例，含明确assert，实际调用实验函数；运行python -m pytest student_tests -q。不能只写assert True或照抄文件存在检查。

可本地预览公开规则的得分：

```powershell
.\.venv\Scripts\python.exe grading/run_grading.py --local
```

--local仅用于自己的可信代码。云端固定在隔离容器评分，不依赖学生自报成绩。

## 6 提交与全自动反馈

```powershell
git add src/t_switch.py src/s_switch.py src/connections.py REPORT.md AI_LOG.md student_tests/
git add -f results/*.png results/*.json
git diff --cached --stat
git commit -m "Complete experiment 02"
git push origin main
```

向教师仓库main创建PR：base为jwentong/Experimenet02-DSNetwork-Bidirectional-Speech，head为个人Fork的main。

**标题必须是：现代交换实验02-本人姓名-完整学号。姓名和学号必须与名单一致，不使用昵称。**

新建PR、追加代码、重新打开PR或修改标题都会自动启动教师评分，无需教师逐次点击批准。只Push个人Fork而未创建教师仓库PR不会评分。补交更新原分支，不重复建PR。

PR机器人评论显示最新提交的分项成绩。教师仓库Actions的“实验二自动评分”可下载grading-report与student-grades附件；成绩看板入口见docs/teacher_operations.md。身份不匹配时仍显示测试结果，但不关联班级成绩；修改标题会自动重新评分并关联。运行故障显示未完成，不冒充0分。绿色工作流不代表满分。

## 7 自动评分 实验70分加报告30分

|项目|分值|规则|
|---|---:|---|
|环境|4|2项测试按比例|
|T交换|14|6项测试按比例|
|S交换|10|5项测试按比例|
|双向连接|14|8项测试按比例|
|连接释放|10|5项测试按比例|
|整体验证|8|5项测试按比例|
|自拟测试|4|含函数调用、断言且实际运行通过|
|结果文件|6|两个JSON和图片各2分|
|实验小计|70|以上实验项合计|
|原理与手算|6|对应节去空白至少60字符|
|结果分析|6|对应节去空白至少60字符|
|反例与验证|6|对应节去空白至少60字符|
|局限|6|对应节去空白至少40字符|
|AI记录|6|至少120字符，三节各去空白至少20字符；未用AI如实记录|
|报告小计|30|REPORT.md至少300字符，含四节；报告和AI记录不得保留TODO或待填写|
|合计|100|无需教师逐次干预|

报告评分是结构与完整性检查，不自动判断论述质量；实验数据真实性由实验项测试核对。Word报告仍需同步REPORT.md与AI_LOG.md。本节为最新评分规则，替代早期课件和PRD中的分值。

[实时成绩表](https://github.com/jwentong/Experimenet02-DSNetwork-Bidirectional-Speech/issues/1)显示完整姓名、学号、提交信息、实验分、报告分及总分。Actions附件含CSV、HTML表格和Markdown快照。提交次数为关联PR中的提交记录数之和，不表示Push事件数；同一提交出现在多个PR时会分别计数。
