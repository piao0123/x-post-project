# X帖子创作发布工作流 - 快速开始

## 配置状态

✅ **X平台认证**: 已配置
✅ **免费图片网站**: 已配置
✅ **自定义图片**: 已配置
⚠️ **Pexels API Key**: 未配置（可选）

## 快速开始

### 1. 运行工作流

```bash
/zcf:x-post-workflow
```

### 2. 工作流步骤

1. **获取热门分类**: 自动从X平台获取热门话题
2. **选择分类**: 从列表中选择感兴趣的分类
3. **获取热门帖子**: 自动获取每个分类下的热门帖子
4. **选择帖子**: 选择要仿写的帖子
5. **仿写内容**: 自动生成仿写内容
6. **人性化处理**: 自动去除AI写作痕迹
7. **字数检查与配图**:
   - 自动检查字数限制
   - 自动搜索并下载配图（使用免费图片网站）
8. **定时发布**: 设置定时时间发布到X

## 图片配置

### 方案1: 使用免费图片网站（推荐）

无需API Key，直接使用以下网站搜索图片：

1. **Unsplash** (https://unsplash.com)
   - 高质量摄影图片
   - 免费商用
   - 搜索关键词后下载图片

2. **Pixabay** (https://pixabay.com)
   - 照片、矢量图、插画
   - 免费商用
   - 支持多种格式

3. **Pexels** (https://pexels.com)
   - 照片和视频
   - 免费商用
   - 高质量内容

**使用方法**:
1. 访问上述网站
2. 搜索相关关键词（如 "technology", "social media"）
3. 选择合适的图片
4. 复制图片URL
5. 在工作流中选择 "使用自己的图片" 选项
6. 粘贴图片URL

### 方案2: 设置Pexels API Key（可选）

如需自动搜索和下载图片：

1. 访问 https://www.pexels.com/api/
2. 注册账号并获取API Key
3. 设置环境变量：
   ```bash
   export PEXELS_API_KEY="your_api_key_here"
   ```
4. 添加到 `~/.zshrc`：
   ```bash
   echo 'export PEXELS_API_KEY="your_api_key_here"' >> ~/.zshrc
   ```

### 方案3: 使用自己的图片

1. 准备好图片文件
2. 在工作流中选择 "使用自己的图片" 选项
3. 提供图片URL或本地路径

## 测试配置

运行测试脚本验证配置：

```bash
/Users/piaoxian/x-post-project/scripts/test-workflow.sh
```

## 常见问题

### Q: 如何获取Pexels API Key？

A: 
1. 访问 https://www.pexels.com/api/
2. 点击 "Get Started"
3. 填写基本信息
4. 获取API Key

### Q: 如何使用免费图片网站？

A:
1. 访问 Unsplash、Pixabay 或 Pexels
2. 搜索相关关键词
3. 选择合适的图片
4. 复制图片URL
5. 在工作流中粘贴URL

### Q: 如何配置X平台认证？

A:
1. 运行 `bird login`
2. 按提示完成认证
3. 运行 `bird check` 验证

### Q: 工作流失败怎么办？

A:
1. 检查网络连接
2. 验证X平台认证
3. 检查图片URL是否有效
4. 查看错误日志

## 配置文件

- **主配置**: `/Users/piaoxian/x-post-project/config/main.json`
- **免费图片网站**: `/Users/piaoxian/x-post-project/config/free-sites.json`
- **自定义图片**: `/Users/piaoxian/x-post-project/config/custom-images.json`
- **Pexels配置**: `/Users/piaoxian/x-post-project/config/pexels.json`（如已设置）

## 下一步

1. 运行工作流：`/zcf:x-post-workflow`
2. 选择分类和帖子
3. 生成仿写内容
4. 添加配图
5. 定时发布

## 获取帮助

- 查看配置指南：`/Users/piaoxian/x-post-project/CONFIG-GUIDE.md`
- 查看快速开始：`/Users/piaoxian/x-post-project/QUICK-START.md`
- 运行测试：`/Users/piaoxian/x-post-project/scripts/test-workflow.sh`
