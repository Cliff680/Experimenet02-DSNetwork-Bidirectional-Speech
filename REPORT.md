# 实验二报告
姓名：李柏霖
学号：2024280042
班级：通信01
GitHub用户名：Cliff680
实验提交：d50d4f4（已推送至个人Fork的main分支）
教师仓库PR：[现代交换实验02-李柏霖-2024280042](https://github.com/jwentong/Experimenet02-DSNetwork-Bidirectional-Speech/pull/28)

## 原理与手算
本实验用T接线器在同一输入链路内改变时隙，用S接线器在同一时隙选择输入链路，基础路径顺序为先T后S。控制表按“输出→输入”解释。以C1的A=(0,1)、B=(1,5)为例，A→B写入T0[5]=1、S[(1,5)]=0；B→A写入T1[1]=5、S[(0,1)]=1。输入帧0的A端字节为3（0x03），通过这两项到达B端输出帧1的TS5；反向输入字节为116（0x74），到达输出帧1的TS1。T测试另以输入TS1=0x31、TS3=0x73验证映射{1:3,3:1}后输出TS1=0x73、TS3=0x31。TS0与TS16保持原位置透传；所有交换结果在本模型中于输出帧k+1可用。

## 结果分析
四项任务均已实现，整合入口生成了results/switch_mapping.png、results/control_tables.json和results/transfer_check.json。传输文件包含16条记录（4帧×2连接×2方向），mismatches为0，conflict_rejected、release_ok、survivor_ok均为true，latency_frames为1。C1第一条记录为输入帧0、可用帧1、source=[0,1]、destination=[1,5]、expected=3、actual=3；反向记录expected=actual=116。释放前T表为T0={5:1,6:2}、T1={1:5,2:6}；释放C1后仅保留T0={6:2}、T1={2:6}和C2的S表项，C2仍传送，C1两端恢复IDLE。结果图横轴为时隙、纵轴为PCM字节；link 0输出端TS1/TS2分别显示116/119，link 1输出端TS5/TS6分别显示3/6，与C1、C2的双向映射一致。本地评分预览`python grading/run_grading.py --local`为实验70/70、报告30/30，总分100/100；该结果仅为本地预览，不等同于教师仓库PR评分。

## 反例与验证
自拟用例`student_tests/test_my_case.py::test_t_switch_reorders_and_rejects_reserved_timeslots`直接调用t_switch。输入为0至31的uint8帧，控制表{1:3,3:1}，断言TS1/TS3交换、TS0/TS16透传、输入帧未改变；另以{16:2}确认非法保留时隙映射抛出ValueError，实际结果1 passed。教师测试及自拟测试联合运行命令为`python -m pytest grading/test_environment.py grading/test_t.py grading/test_s.py grading/test_connect.py grading/test_disconnect.py grading/test_integration.py grading/test_report.py student_tests -q`，结果37 passed。整合程序也独立运行成功并报告16项检查通过、冲突拒绝、C1释放及C2存活。

## 局限
本实验只验证固定的离线模型，不包含真实线路、音频设备、呼叫控制或E1帧同步与信令。基础路径固定先T后S，内部T资源冲突时拒绝连接，不自动寻找替代路径；整帧缓存的一帧125微秒是仿真约定，不代表所有真实T接线器的物理延迟。测试覆盖了给定模型的帧、表项、冲突与释放行为，但不能替代硬件时序、噪声和长期运行验证。