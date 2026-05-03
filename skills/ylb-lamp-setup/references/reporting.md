# 坐姿检测报告 / 智能记录

## 1. 适用场景

当用户提到下面这些需求时，按本文件执行：
- 坐姿检测报告
- 坐姿报告
- 学习报告
- 姿势报告
- 最近七天坐姿
- 今天坐姿怎么样
- 看看孩子今天学习状态
- 读取 posture record / 智能记录

## 2. 关键原则

1. 不要直接使用文档中的示例 `playerId`。
2. 先拿真实 `groupId`，再拿真实 `playerId`，然后才能查坐姿记录。
3. 同一手机号下，`playerId` 可以复用；不要每次都重新查。
4. 查询某一天的坐姿记录时，`date` 传“当天 00:00 的毫秒时间戳”。
5. 如果用户没特别说明时间范围：
   - 默认优先给“今天报告”
   - 如果用户说“近一周/最近七天”，再走 last_seven_days 接口

## 3. 正确链路

### Step 1. 确认已有可用登录态 + 401 兜底

优先复用本地缓存中的：
- token
- phone
- device_sn
- env

**⚠️ token 失效 401 兜底规则（必须实现）：**
1. 调用任何 HTTP API 时，先做好 401 响应判断
2. 若返回 401 或 `code == 401`：token 已过期，需要重新走登录流程
3. 重新登录时，告诉用户"登录状态已过期，请重新提供验证码"，然后走 vercode → 用户给验证码 → 登录 → 重新执行原命令
4. **不要在 401 时直接告诉用户"token 过期了"然后停住，必须自动触发重新登录**

> 💡 注意：MQTT 连接对 token 失效的容忍度比 HTTP API 高，有时 MQTT 仍能用但 HTTP 已经 401。如果 HTTP API 报 401 但 MQTT 正常，也应重新登录以保持一致。

### Step 2. 先查 groupId

接口：
- `GET /l1/usercenter/v1/groups/user?roleType=1&isAll=false`

常用请求头：
- `AUTH-TOKEN: <token>`
- `SOURCE: APP`
- `SERVER-VERSION: 1.0.1`
- `Content-Type: application/json`

从返回里取真实 `groupId`。

**实际响应结构：**
```json
{
  "code": ...,
  "data": {
    "list": [
      {
        "id": ...,
        "groupId": "<groupId>",
        "name": ...,
        ...
      }
    ]
  }
}
```
取法：`data.list[0].groupId`（通常取第一条即可）

### Step 3. 再查 playerId

接口：
- `GET /l1/usercenter/v1/players?groupId=<groupId>`

常用请求头同上。

**实际响应结构：**
```json
{
  "code": ...,
  "data": {
    "list": [
      {
        "id": ...,
        "playerId": "<playerId>",
        "groupId": ...,
        ...
      }
    ]
  }
}
```
取法：`data.list[0].playerId`（通常取第一条即可）

### Step 4. 再查坐姿记录

#### 今天 / 某一天报告

接口：
- `GET /l1/usercenter/v1/players/<playerId>/posture/record?date=<当天00:00毫秒时间戳>`

重点关注返回字段：
- `todayPerformance`
- `fatigueDetail`
- `detailRecords`

#### 最近七天报告

接口：
- `GET /l1/usercenter/v1/players/<playerId>/posture/record/last_seven_days`

#### 实景开关（如用户明确需要）

接口：
- `GET /l1/usercenter/v1/players/<playerId>/posture/switch/real_scene`
- `POST /l1/usercenter/v1/players/<playerId>/posture/switch/real_scene`

## 4. 输出要求

1. 先给用户结论，再给温和解释。
2. 默认输出为面向家长/学习场景的自然语言，不要把原始接口字段直接甩给用户。
3. 若用户明确要“学习报告”，优先使用固定的微信报告模板输出。
4. 若用户明确要原始数据，再补充结构化信息。
5. 如果记录为空，不要说“失败”；应说“当前还没有可供生成报告的数据”。
6. 不要编造接口里没有的数据；拿不到的字段要用温和占位语说明。

## 5. 学习报告默认模板（微信报告）

当用户要“学习报告 / 今日学习报告 / 微信报告”时，默认按下面模板整理：

```text
微信报告：
亲爱的家长，您好！以下是孩子今日作业期间的详细学习情况：
✅ 今日作业完成情况：<根据上下文填写；如接口无此信息则写“暂未直接获取到完成项信息”>
📅 作业时段：<根据记录整理；如无法精确判断则写“今日已记录学习时段”>
💪 核心数据统计：
总学习时长：<aiAnalysisTime> 分钟（专注率 <focusRate%>，<评价语>）
专注时长：<focusTotalTime> 分钟（<如能对比昨日则写对比，否则写“整体表现稳定”>）
坐姿情况：共检测到坐姿错误 <提醒次数> 次（<可细分前倾/歪头等；拿不到就写“已进行坐姿提醒”>）
离座记录：<如 detailRecords 可统计则填写；拿不到则写“暂未识别到明显异常离座”>
🌟 今日亮点：<根据 todayPerformance / postureStandardRate / focusScore 生成一句亮点总结>
💡 远程控制：如需修改明日作业时间，直接给我发消息即可！
—— 元萝卜光翼灯・陪孩子高效学习，让家长更省心
```

### 模板填充原则

- `总学习时长`：优先用 `aiAnalysisTime`
- `专注时长`：优先用 `focusTotalTime`
- `专注率`：优先用 `focusRate`，转成百分比
- `坐姿情况`：优先结合 `postureReminderCount`、`detailRecords`
- `今日亮点`：优先结合 `todayPerformance`、`focusScore`、`postureStandardRate`
- `作业完成情况`、`作业时段`、`离座记录`：如果接口没有明确字段，不要硬编；用自然、温和的占位表述

## 6. 生成报告时的表达

优先风格：
- 更口语化
- 更像家长微信通知
- 先鼓励，再说明数据
- 避免技术味、避免接口味

避免生硬措辞，优先使用：
- “可以继续保持”
- “整体表现不错”
- “建议稍微留意”
- “如果后面能再稳定一点会更好”
- “从学习习惯角度看”
- “今天的状态还是挺不错的”

## 7. 已验证经验

- 智能记录接口必须先拿 `groupId`，再拿真实 `playerId`。
- 不换手机号时，`playerId` 通常可长期复用。
- `detailRecords` 中可拿到 `changePostureImg` 和 `postureRealSceneSwitch`，适合后续做异常片段回看。
- 不要把“查不到真实 playerId”的情况误判成“没有坐姿报告”。
