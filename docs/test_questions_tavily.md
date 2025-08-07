# Tavily域名过滤测试问题集

## 测试目标
验证deer-flow能够仅从配置的特定域名获取信息，确保搜索结果的可靠性和相关性。

## 配置的域名列表
- walmart.com, marketplace.walmart.com, sell.walmart.com
- amazon.com, sell.amazon.com, aboutamazon.com  
- junglescout.com, statista.com, pwc.com
- 等共22个域名

## 测试问题分类

### 1. 单一平台深度查询
**问题**: 沃尔玛在线商城最近推出了哪些新的热门商品类别？
- **预期来源**: walmart.com, marketplace.walmart.com
- **验证点**: 是否只返回沃尔玛官方站点的信息

**问题**: 亚马逊2024年Prime Day的销售数据和热销品类分析
- **预期来源**: amazon.com, aboutamazon.com, statista.com
- **验证点**: 数据是否来自官方或权威统计网站

### 2. 跨平台对比分析
**问题**: 比较沃尔玛和亚马逊在家居用品类别的定价策略
- **预期来源**: walmart.com, amazon.com, priceva.com
- **验证点**: 是否能从多个指定来源综合信息

**问题**: 分析JungleScout数据中显示的电商平台竞争格局
- **预期来源**: junglescout.com, statista.com
- **验证点**: 专业数据分析网站的信息整合

### 3. 行业趋势研究
**问题**: PWC最新报告中关于零售业数字化转型的关键发现
- **预期来源**: pwc.com
- **验证点**: 是否准确获取专业咨询公司的报告内容

**问题**: 欧洲央行货币政策对跨境电商的影响分析
- **预期来源**: ecb.europa.eu, pwc.com
- **验证点**: 官方机构信息的准确获取

### 4. 实操指南类
**问题**: 如何在Walmart Marketplace注册成为第三方卖家的详细步骤
- **预期来源**: sell.walmart.com, marketplace.walmart.com, goaura.com
- **验证点**: 官方指南和第三方经验的结合

**问题**: YouTube上关于优化亚马逊产品listing的最新教程推荐
- **预期来源**: youtube.com, junglescout.com
- **验证点**: 视频内容与专业工具的配合使用

### 5. 数据统计类
**问题**: Statista关于2024年全球电商市场规模的最新统计数据
- **预期来源**: statista.com
- **验证点**: 权威统计数据的准确性

**问题**: MarkWide Research对未来5年电商增长趋势的预测
- **预期来源**: markwideresearch.com
- **验证点**: 市场研究报告的获取能力

## 测试验证方法

1. **域名验证**: 检查返回结果的URL是否都在配置列表中
2. **内容相关性**: 验证搜索结果是否与问题直接相关
3. **信息完整性**: 评估是否获取了足够的信息来回答问题
4. **来源可靠性**: 确认信息来自官方或权威来源

## 异常测试

**问题**: 搜索一些配置域名之外的内容（如Twitter趋势、Reddit讨论）
- **预期结果**: 不应返回任何结果或提示无法找到相关信息
- **验证点**: 域名过滤的严格性

## 使用建议

1. 逐个测试问题，观察返回结果的来源
2. 记录每个问题的实际返回域名vs预期域名
3. 评估信息质量和完整度
4. 根据测试结果优化域名配置列表