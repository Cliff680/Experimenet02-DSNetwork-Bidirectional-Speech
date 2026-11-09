# 实验二自动评分与记录

学生在个人Fork提交代码并创建教师PR后，提交触发器自动分派评分；无需教师审批每次运行。姓名学号须与教师配置的班级名单一致。成绩为实验70分加报告30分自动规则，无人工待评项。

## 工作流
1. submission.yml使用pull_request_target，仅处理PR元数据并调用workflow_dispatch，不检出或执行学生代码。
2. grade.yml仅使用main中的教师工作流、测试和依赖；collect_submission只提取指定任务文件、结果、报告和自拟测试。学生代码在禁网络、非root、只读文件系统、资源受限的Docker容器内执行，不传入教师凭据。
3. publish任务在另一台runner上解析教师评分报告，核对当前提交，更新PR机器人评论并输出CSV。旧提交不会覆盖新提交成绩。
4. 同一个评分工作流的board任务在反馈结束后自动重读全部PR，串行更新37人成绩看板。模拟与未匹配提交单独记录。board.yml仅保留为教师维护入口，日常评分不依赖手动运行。

## 一次性配置
启用Actions，允许上述受信任工作流使用声明的最小权限。变量TRACKING_ISSUE_NUMBER指向成绩看板Issue。Secret CLASS_ROSTER_JSON保存教师授权的班级名单，不进入公开代码；仅反馈和看板任务读取。按教师授权，公开表格及CSV、HTML显示完整姓名、学号和成绩；名单来源仍只保存在Secret。
GitHub公共仓库的pull_request_target事件策略必须明确允许本仓库的元数据触发器；该触发器不能改为运行学生代码。
无需学生申请仓库写权限，无需提供个人访问令牌给学生，无需为每个PR手工批准。

## 日常查看
查看成绩看板和PR机器人评论；下载student-grades中的student_grades.csv。CSV、HTML为运行时快照，班级未评分项为空白。评分服务故障会标明运行失败，并保留Actions日志。
不将绿色流程等同于100分，不将未完成功能与基础设施故障混为一谈。

## 官方依据
https://docs.github.com/en/actions/reference/security/securely-using-pull_request_target
https://docs.github.com/en/actions/concepts/security/github_token
https://docs.github.com/en/rest/actions/policies
