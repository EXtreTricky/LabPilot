# API（本地演示）

| 方法 | 路径 | 用途 |
|---|---|---|
| GET | `/api/rooms` | 实验室列表 |
| GET | `/api/summary` | 概览数据 |
| GET | `/api/recommend?purpose=开发&participants=15` | 规则推荐 |
| GET | `/api/bookings` | 预约列表 |
| POST | `/api/bookings` | 申请预约 |
| POST | `/api/bookings/{id}/approve` | 演示审批 |
| GET | `/api/inspections` | 巡检列表 |
| POST | `/api/inspections` | 登记隐患及规则提示 |
| POST | `/api/inspections/{id}/close` | 关闭隐患 |

预约 JSON：`{"room_id":1,"applicant":"学生A","day":"2026-12-01","period":"上午","purpose":"开发","participants":12}`。

巡检 JSON：`{"room_id":1,"description":"插座冒烟"}`。

`409` 表示同一时段冲突；`400` 为表单校验失败。**审批与关单接口没有权限验证，不能用于正式环境。**
