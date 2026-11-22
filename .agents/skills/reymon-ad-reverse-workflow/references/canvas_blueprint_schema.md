# LibTV 无限画布 V3 双模式分区拓扑与蓝图数据结构规范

本规范统一指导 **LibTV MCP 云端直连建图（主力路径）** 与 **`scripts/build_libtv_canvas.py` 离线脚本建图（降级路径）**，彻底对齐 V3.0 的「多 SKU 资产 + 双制作模式 + 音色/BGM 100% 统合 + 默认 `480p Flash` 抽卡」。

---

## 一、 云端无限画布物理分区拓扑（Mode A vs Mode B）

### 1. 模式 A：【全 AI 统合全片模式】完整画布分区

| 分区 / Group 名称 | 推荐 X 坐标列 | 包含节点类型与默认模型 | 自动运行 | 核心职责与先后顺序 |
| :--- | :--- | :--- | :--- | :--- |
| **`00A_官方交互式分镜脚本表`** | `X = -1650` | `script-v2`（原生分镜表格节点） | 否 | 结构化展示全片镜号、时长、景别、台词、资产与生图/生视频提示词 |
| **`00_总剧本与分级生成指南区`** | `X = -700` | `text`（总剧本卡 + **防空URL 4步操作指南卡**） | 否 | 置顶提醒用户**第 1 步必须先跑 05 音色/BGM 与 03/04 底座** |
| **`01_产品包装素材分类组`** | `X = 0` | `image`（上传的当前 SKU 正视图 / 囤货图）+ 上方 `📌` 标注卡 | 仅上传 | 像素级锁死当前 SKU 包装版式、文字与手持尺寸比例 |
| **`02_内料与微观材质分类组`** | `X = 650` | `image`（上传的纯内料微距图 / 实测完成态图）+ 上方 `📌` 标注卡 | 仅上传 | 锁死微观颗粒/膏体几何形态，支持随时替换实拍真图 |
| **`03_环境与道具基底分类组`** | `X = 1300` | `image`（`lib-image-2.6-s`）+ 上方 `📌` 标注卡 | **否（第1步点生图）** | 锁定全片统一空间建筑透视、2800K/5200K 光影底色与核心道具 |
| **`04_角色与宠物三视图分类组`** | `X = 1950` | `image`（`lib-image-2.6-s`）+ 上方 `📌` 标注卡 | **否（第1步点生图）** | 单图多视角设定板，跨镜头锁死演员五官骨相、发饰服装与宠物特征 |
| **`05_角色音色锁与全局BGM组`** | `X = 2550` | `audio`：<br>1. 角色专属音色锁/旁白（`speech-2.8-hd`，固定 `voiceId`+`speed`）<br>2. **全局唯一纯器乐BGM**（`vocal-music`，`instrumental=1`，`30s`） | **否（第1步最先点运行！）** | **核心统合枢纽**：一对多锁定全片人声音色与恒定语速，并提供唯一贯穿全片的背景配乐 |
| **右侧：`分镜01` ~ `分镜0N` 逐行分镜组** | 每行横向展开 (`Y` 步进 `1100`)：<br>- 导演卡 `X = 3300`<br>- 首帧静帧 `X = 3930`<br>- *(内料跳变镜)* 尾帧静帧 `X = 4560`<br>- **视频抽卡节点 `X = 5200`** | - 静帧：`lib-image-2.6-s`<br>- 视频：**`star-video2.5-flash`（Seedance 2.5 Flash）+ `resolution="480p"` + `ratio="9:16"` + `intent="reference"`** | **否（第2步跑静帧 → 第3步跑480p视频）** | 1 行 = 1 个独立分镜组；视频提示词用 `{{Node <id>}}` 同时接入首(尾)帧+角色+场景+产品真图+音色节点，且**强制单镜 No BGM** |

---

### 2. 模式 B：【轻量 AI 钩子 + 实拍混剪模式】精简画布分区

> **轻量化原则**：省去 `02_内料组`（除非钩子前 3 秒本身出现内料）、省去全局 BGM 生成节点（后期剪映统一铺热曲）、省去第 3 镜以后的全部后段分镜节点！

- **左侧精简底座区**：
  - `00_钩子剧本与实拍混剪对接表`（含切出时间点与实拍承接指南）；
  - `03_钩子场景空镜` + `04_钩子角色三视图`（及钩子若露包装时的 `01_包装真图`）；
  - `05_音色与实拍旁白组`：钩子角色音色锁（`speech-2.8-hd`）+ **（可选）同 `voiceId` 同 `speed` 的「后段实拍全句画外音 TTS 节点」**。
- **右侧钩子抽卡区（支持单钩子或多钩子赛马）**：
  - 若为单钩子：仅建 `分镜01`（或 `分镜01~02`，共 3~6s）1~2 行；
  - 若为**多钩子赛马裂变**：按行并列铺设 `赛马钩子A_行`、`赛马钩子B_行`、`赛马钩子C_行`（共享左侧同一角色/场景/音色底座，全部预设 `star-video2.5-flash` `480p` 待点抽卡）。

---

## 二、 提示词占位符引用铁律

1. **LibTV MCP 云端模式（首选）**：
   - 提示词中必须使用精确节点 ID 占位符 **`{{Node <nodeId>}}`**（例如 `以 {{Node i-Koi25N7CBb}} 锁定清宫暖阁环境`、`严格复刻 {{Node a-rn4uFhlTpW}} 的专属声线`）；
   - 同时在 `create_node` / `update_node` / `generate_video` 参数中将该 `nodeId` 加入 `left` 或 `referenceImageNodes` / `referenceAudioNodes`；服务端会自动原位转换编号，**宿主严禁手工硬算 `{{Mixed N}}` 序号**。
2. **离线 `canvas_blueprint.json` + CLI 降级模式**：
   - 见下方 JSON Schema，使用 `left_inputs` 列表顺序自动映射或校验占位符。

---

## 三、 离线降级蓝图 `canvas_blueprint.json` 标准结构（V3.0）

```json
{
  "project_name": "瑞梦迪5合1白茶款_爆款反推_V3双模式批次01",
  "sku_id": "reymon-cat-litter",
  "production_mode": "full_ai",
  "ab_hook_strategy": "single",
  "aspect_ratio": "9:16",
  "image_model": "Lib Image 2.6 Pro",
  "image_resolution": "2K",
  "video_model": "Seedance 2.5 Flash",
  "video_resolution": "480p",
  "speech_rate_target_cps": 4.1,
  "script_summary": [
    "【模式A：全AI统合全片 | 480p抽卡预连线】",
    "第1步必先运行：05_音色与全局BGM组 + 03/04视觉底座",
    "第2步运行：各镜首尾静帧（核对包装字与右侧12%/上下18%安全区）",
    "第3步运行：480p Flash 视频节点抽卡（单镜已禁BGM，成片统合全局BGM）"
  ],
  "uploaded_assets": [
    {
      "node_name": "包装_01_当前SKU单品正视图",
      "media_type": "image",
      "file_path": "products/reymon-cat-litter/assets/packshots/pack_front.png",
      "required": true,
      "description": "锁死包装版式、品牌文字与2.5kg真实手持尺寸比例"
    }
  ],
  "audio_nodes": [
    {
      "node_name": "音色_01_主角专属音色母本",
      "audio_role": "tts_voice_lock",
      "model": "Minimax-speech-2.8-hd",
      "voice_id": "Chinese (Mandarin)_Crisp_Girl",
      "speed": 1.05,
      "prompt": "瑞梦迪五合一混合猫砂，除臭结团样样扎实，省下的银子够猫咪体体面面用半年啦！"
    },
    {
      "node_name": "配乐_00_全局唯一纯器乐BGM_30s",
      "audio_role": "global_bgm",
      "model": "ElevenMusic V3",
      "instrumental": true,
      "duration_ms": 30000,
      "prompt": "轻快灵动的新国风影视短剧纯器乐背景配乐，前3秒微悬念弦乐拨奏，随后转为明快俏皮的琵琶与竹笛律动，无任何人声唱词，节奏干净适合信息流带货口播压底"
    }
  ],
  "anchor_image_nodes": [
    {
      "node_name": "环境_01_主场空间空镜底座",
      "role": "environment",
      "ratio": "9:16",
      "left_inputs": [],
      "prompt": "..."
    }
  ],
  "shots": [
    {
      "shot_id": "Shot01",
      "title": "黄金3秒冲突钩子",
      "time_range": "00:00 - 00:04",
      "duration_sec": 4,
      "shot_routing": "AI_HOOK_480P",
      "voiceover": "养猫最怕满屋尿骚糊盆底，开门简直没法进！",
      "keyframe_node": {
        "node_name": "Shot01_首帧静帧",
        "left_inputs": ["环境_01_主场空间空镜底座"],
        "prompt": "... {{Image 1}} ..."
      },
      "video_node": {
        "node_name": "Shot01_视频抽卡_480p",
        "duration": 5,
        "enable_sound": "on",
        "no_bgm_enforced": true,
        "left_inputs": ["Shot01_首帧静帧", "环境_01_主场空间空镜底座"],
        "prompt": "... {{Image 1}} ... {{Image 2}} ... 【禁配乐红线（No BGM）】全程严禁生成任何背景音乐 ..."
      }
    }
  ],
  "real_shoot_handoff": []
}
```
