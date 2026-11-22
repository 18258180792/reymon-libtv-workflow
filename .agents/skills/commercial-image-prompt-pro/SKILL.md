---
name: commercial-image-prompt-pro
description: >-
  Generates director-grade, hyper-detailed commercial photography, cinematic still,
  prop macro, and character turnaround image generation prompts using an 8-layer
  optical/lighting/PBR-material protocol with full feed-ad UI safe zones (top/bottom 18%
  + right sidebar 12%) and multi-SKU packaging/material locking for LibTV image models.
---

# 高精度商业摄影与影视静帧提示词专家技能（8 维光学协议 · V3 多SKU通用版）

本技能专为 `Lib Image 2.6 Pro`（`lib-image-2.6-s`）、`Seedream 5.5` 等高精度图像模型编写**拒绝 AI 塑料感、光影物理精确、多 SKU 包装与微观材质零漂移**的商业级生图提示词。

## 必读词元字典
编写提示词前，请读取 [optical_lighting_material_lexicon.md](./references/optical_lighting_material_lexicon.md) 以选取匹配的机身镜头、四点布光光比与微观 PBR 材质描述；针对对话中新输入的产品/SKU，结合其 `product_brief.md` 提取专属器型与微观材质参数。

---

## 核心编写铁律：八维全要素结构（缺一不可，单条提示词建议 220~380 字）

每一条图片节点提示词（无论是环境空镜、角色/宠物三视图定妆，还是带 `{{Node <nodeId>}}` 的分镜首尾关键帧），必须按以下 **黄金权重顺序** 展开，严禁使用“高质量、大师杰作、电影感”等无效空洞词：

1. **【前 20% 黄金权重区】画幅、实拍介质与多图参考职责锁（Anchor & Medium Lock）**
   - 若有上游引用（`left` 连线）：必须在第一句用精确的 **`{{Node <nodeId>}}`** 明确每个参考源的**唯一职责边界**（例如：`严格以 {{Node i-xxx}} 像素级锁定包装袋版式、全部印刷文字与真实单件手持尺寸比例，以 {{Node i-yyy}} 锁定空间透视与环境色温底光，以 {{Node i-zzz}} 锁定演员五官骨相与服饰纹理，各参考源色彩严格隔离互不串染`）。
   - 明确拍摄介质：剧情镜用 `ARRI Alexa Mini LF 配合 Cooke S7/i 全画幅定焦镜头实拍原片`；产品/内料微距镜用 `Hasselblad H6D-100c 或 Phase One XF IQ4 中画幅相机配合 80mm/120mm f/8 Macro 微距镜头，1/4000s 高速闪光同步快门凝结瞬间`。

2. **机位几何、空间构图与「全向信息流 UI 安全区」（Camera Geometry & Feed UI Safe Zones）**
   - 写明机位高度、俯仰角度、前中后三层景深关系；
   - **强制全向安全区**：竖屏 `9:16` 信息流广告画面，除了写明 **`上下各预留 18% 纯净标题/转化按钮安全区`** 外，还必须写明 **`画面最右侧边缘预留 12% 纯净交互图标避让区（关键人物正脸、手部核心动作与产品包装主文字严禁贴靠右边缘，主体核心视觉重心居左中黄金区）`**！

3. **主体微观细节与物理承重定格（Subject Micro-Anatomy & Pose）**
   - 人物：具体到眉弓肌肉走向、瞳孔高光落点、手指握持真实克重产品时指腹微陷的物理受力感、原生皮肤毛孔肌理（严禁网红磨皮蜡像感）。
   - 宠物/动物：胡须弧度、瞳孔反光、毛发分簇蓬松度与肉垫纹理。
   - 多 SKU 产品与内料：严格按当前 SKU 档案描述器型立体折角、封口工艺，以及内料/膏体/颗粒的真实粒径比例与几何形态。

4. **四层专业影视布光方案（4-Point Cinematography Lighting Rig）**
   - 必须写明**主光（Key）+ 辅光（Fill）+ 轮廓逆光（Rim/Kicker）+ 环境反射光（Practical/Bounce）**的方向、色温（K）与明暗光比（产品包装特写必须强调**柔光漫反射补光，避开死白镜面眩光遮挡袋面文字**）。

5. **PBR 物理表面材质纹理（Micro-Texture & Surface Materiality）**
   - 明确不同材质的反光率与微观截面差异（如丝绸漫反射、哑光复合PE包装膜、多孔植物纤维豆腐砂条 vs 矿物粉感膨润土圆粒 vs 半透明晶粒等）。

6. **色彩科学与胶片调色（Color Science & Grading）**
   - 指定全片贯穿的 Base 色调（如 `Kodak Vision3 500T 暖调胶片色彩科学`）与产品包装视觉锤的高纯净度色彩反差。

7. **光学景深与空气洁净度（Optical Depth & Atmosphere）**
   - 指定焦点平面（产品特写须保持包装正平面四角至中心全域清晰 `Deep Focus Zone`；低尘/纯净测试镜须强调 `逆光暗部空气清澈通透，零丁达尔烟雾零悬浮粉尘噪点`）。

8. **硬性负向排斥约束（Hard Negative Constraints）**
   - 结尾固定收口：`严禁CG游戏渲染感、严禁过度磨皮塑料脸、严禁包装文字重影变形或新增乱码字幕水印、严禁多手指肢体畸变。`
