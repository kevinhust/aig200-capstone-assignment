# SleepInsight AI 项目方案文档

**项目名称**：SleepInsight AI  
**项目目标**：开发并部署一个基于可穿戴设备数据的睡眠质量分析 REST API，帮助用户从 Apple Watch 或其他北美常见穿戴设备导出的睡眠数据中获得量化睡眠分数、指标对比分析、个性化建议，并安全引导潜在健康问题求医。  
**适用课程**：AIG 200 - Machine Learning Model Deployment Assignment  
**作者**：Kevin（Toronto, Ontario）  
**日期**：2026 年 2 月

## 1. 项目概述与目标

### 核心价值
- 帮助用户解读 Apple Watch / Fitbit / Garmin 等设备导出的睡眠数据，提供直观、可行动的洞见。
- 焦点放在**部署和运营化**：预训练模型 + FastAPI + Docker + 云部署（GCP Cloud Run 或 AWS Elastic Beanstalk）。
- 强调 HCLS（Health Care & Life Sciences）主题：透明、可解释、安全（含免责声明与求医引导）。

### 项目范围（符合作业限制）
- 模型预训练并保存，不在推理时重新训练。
- API 通过 POST JSON 接收特征，返回结构化分析报告。
- 不使用 Streamlit/Gradio 等 GUI，仅 REST API。
- 数据手动导出 + 用户组装 JSON（不直接集成 HealthKit / Health Connect API）。

## 2. 问题定义

**机器学习任务**：回归问题  
- 预测目标：sleep_score（0–100 分，越高表示睡眠质量越好）  
- 基于一晚睡眠的生理与阶段特征进行预测  
- 输出：分数 + 分级 + 逐项指标对比 + 解释 + 建议 + 免责声明

**输入来源**：用户从 Apple Health / Google Fit / 设备 App 手动导出数据（CSV / XML），提取关键指标后组 JSON 调用 API。

## 3. 数据集选择与准备

### 主要数据集（混用提升规模与多样性）
1. **Sleep Health and Lifestyle Dataset**（Kaggle，主数据集）  
   - 样本量：~400 行  
   - 关键特征：Sleep Duration, Quality of Sleep (1–10), REM sleep percentage, Deep sleep percentage, Heart Rate, Stress Level, Age, Gender, Occupation, BMI 等  
   - 标签：Quality of Sleep（scale 到 0–100 作为目标）

2. **Sleep Efficiency Dataset**（Kaggle，补充）  
   - 样本量：~452 行  
   - 关键特征：Sleep efficiency %, REM sleep %, Deep sleep %, Light sleep %, Awakenings, Caffeine, Alcohol 等  
   - 标签：Sleep efficiency（可作为辅助或融合目标）

**总样本量**：融合后约 800–850 行（清洗后可能略少）  
**处理方式**：
- Pandas concat + 统一列名 + drop_duplicates / dropna
- 衍生特征：sleep_efficiency = total_sleep / time_in_bed
- 报告中说明：融合公开数据集提升泛化能力

## 4. 特征工程与预处理管道

### 输入特征（JSON）
**核心（强烈推荐）**：
- total_sleep_time_minutes
- time_in_bed_minutes
- rem_duration_minutes
- deep_duration_minutes
- awake_duration_minutes（或 awakenings_count）
- avg_heart_rate_bpm
- respiratory_rate

**推荐/可选**：
- hrv_sdnn
- core_light_duration_minutes
- age
- gender（"Male"/"Female"/"Other"）
- stress_level（0–10）
- caffeine_intake_mg

**呼吸干扰标志（触发求医）**：
- breathing_disturbances_elevated：bool 或 int（次数）
- apnea_notification_received：bool

### 预处理管道（Scikit-learn Pipeline）
- Imputer（均值填缺）
- 衍生特征：efficiency, stage_percentages（deep/rem / total_sleep）
- StandardScaler（数值特征）
- OneHotEncoder（gender 等类别）
- 保存：joblib.dump(preprocessor, 'preprocessor.pkl')

## 5. 模型训练

### 模型选择（至少两种）
- Baseline：Linear Regression 或 Ridge
- Advanced：XGBoost Regressor 或 RandomForest Regressor（推荐 XGBoost，处理非线性强）

### 训练流程
1. EDA：分布图、相关热图、异常值检查
2. Train-test split（80/20）
3. Pipeline fit + GridSearchCV 调参
4. 评估指标：MAE（目标 <10 分）、R²（目标 >0.7–0.8）
5. 保存最佳模型：joblib.dump(model, 'sleep_model.pkl')

## 6. API 设计（FastAPI）

### Endpoint
- POST /analyze_sleep
- 输入：JSON（如上特征）
- 认证：简单 API Key Header（作业要求基本安全）

### 输出结构（JSON）
```json
{
  "sleep_score": 78,
  "quality_tier": "良好",
  "key_insights": {
    "efficiency": 87.5,
    "deep_percentage": 18,
    "rem_percentage": 22,
    ...
    "breathing_disturbances_elevated": true
  },
  "detailed_analysis": [
    {
      "metric": "睡眠效率",
      "user_value": "87.5%",
      "normal_range": "85–95%（理想 >90%）",
      "interpretation": "良好水平，入睡效率较高，但仍有轻微提升空间。"
    },
    {
      "metric": "深睡比例",
      "user_value": "18%",
      "normal_range": "13–23%（平均 18–20%）",
      "interpretation": "处于正常区间，对身体修复支持较好。"
    },
    ...
  ],
  "summary_opinion": "总体睡眠质量良好（78 分），效率和 REM 阶段表现优秀，但深睡略低且有呼吸干扰信号。建议优化睡前习惯，若呼吸干扰持续出现，尽快咨询睡眠专科医生。",
  "recommendations": [
    "避免晚餐后咖啡因",
    "睡前 1 小时减少蓝光暴露",
    "如果 Apple Health 显示持续 Elevated Breathing Disturbances，强烈建议咨询医生（如 Toronto 的 Sunnybrook 或 Mount Sinai 睡眠诊所）"
  ],
  "disclaimer": "本分析基于可穿戴设备数据和通用参考范围，仅供参考，不是医疗诊断或建议。请咨询合格医疗专业人士。"
}
```

### 规则逻辑要点
- 逐项对比基于公开健康指南（AASM、NSF、商用设备标准）
- 总结意见：整合所有指标 + 自动语气调整（低分 + 呼吸 flag → 强烈求医）
- 呼吸干扰触发：专用一条求医建议（强调持续性 + 本地资源）

## 7. 部署架构

- **框架**：FastAPI + Uvicorn
- **容器化**：Dockerfile（python:3.10-slim，COPY model & preprocessor）
- **云平台**：推荐 GCP Cloud Run（serverless、免费 tier 够用、部署快）
  - 备选：AWS Elastic Beanstalk
- **可扩展性**：自动 scaling（Cloud Run 默认支持）
- **安全**：API Key 认证 + HTTPS（云平台默认）

## 8. 报告与交付物

- **PDF 报告**（必须含截图）：
  - Executive Summary
  - 问题描述与数据集
  - 模型开发过程（EDA、管道、训练曲线、指标）
  - 部署架构图（Draw.io）
  - Challenges & 解决方案（e.g., 数据融合、隐私处理、求医引导）
  - 结论与未来改进（e.g., 多天趋势分析、移动端集成）
- **代码仓库**：GitHub private
  - Jupyter Notebook（EDA & 训练）
  - main.py（FastAPI）
  - Dockerfile、requirements.txt
  - model.pkl、preprocessor.pkl
  - README.md（包含导出数据 → JSON → 调用 API 指南）
- **Live API**：部署 URL + 测试 Key

## 9. 风险与挑战应对

- 数据量有限 → 融合两个数据集 + 噪声增强
- 健康数据隐私 → 用户手动导出、不存储数据、强免责声明
- 医疗风险 → 不诊断、仅参考、强制求医引导
- Apple Health 导出复杂 → README 提供详细步骤 + 推荐第三方 CSV 导出 App

祝你项目顺利！如果在实现过程中遇到具体问题（数据集清洗、模型指标不理想、Docker 报错等），随时回来讨论，我们继续优化。加油 Kevin！🚀