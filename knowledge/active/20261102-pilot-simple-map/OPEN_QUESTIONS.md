# 待确认清单（pilot_simple_map）

- Q-01（resolved）：本单是否需要参考图？→ 不需要，见 Brief §2 原创方向声明。
- Q-02（assumed）：Cycles 同场景重渲是否逐位相同？→ **按"不保证"处理**，TEST-05 预先声明
  RMS 容差 ≤ 2/255 且尺寸一致，不要求 bit-identical。理由：本项目历史上同场景重渲出现过
  不同 SHA（v25 恢复轮），逐位相同不能作为通过条件。
- Q-03（resolved）：是否套用 P1 机械 gate？→ 不套用。`tools/static_map_quality_gate.py`
  的参考 SHA、六维权重、8 条硬门槛全部写死为 P1，对新业务无意义。
- Q-04（open, non-blocking）：这份 pilot 业务包在验证结束后保留还是删除？
  暂定保留（作为"新业务从零起步"的可运行样例），由用户在下一轮决定。
