# 技术设计概要

## 范围与架构
浏览器 → Python `ThreadingHTTPServer` → `process()` 业务路由 → SQLite。规则模块负责推荐与关键词标注；它不是大模型服务。零依赖便于教学运行。

## 核心数据表
- `rooms(id,name,capacity,tags,status)`
- `bookings(id,room_id,applicant,day,period,purpose,participants,status,created_at)`
- `inspections(id,room_id,description,risk_level,status,created_at)`

## 业务约束
- 按房间/日期/上午下午晚上进行冲突判断；记录申请与审批状态
- 根据用途标签、容量形成可解释推荐分数
- 根据隐患关键词标注“高”或“待人工核验”，不替代专业风险评级

## 待扩展
身份认证与 RBAC、日志审计、事务与唯一索引、真实 LLM 服务的输入审核/脱敏/评测、通知提醒、手机端鸿蒙 ArkUI 适配。
