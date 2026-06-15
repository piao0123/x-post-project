# X帖子创作发布工作流 - 配置指南

## 快速配置

### 1. Pexels API Key（推荐）

**用途**: 搜索和下载X帖子配图

**步骤**:
1. 访问 https://www.pexels.com/api/
2. 点击 "Get Started" 注册账号
3. 填写基本信息（姓名、邮箱、用途说明）
4. 获取API Key
5. 设置环境变量：

```bash
export PEXELS_API_KEY="your_api_key_here"
```

或添加到 `~/.zshrc`：
```bash
echo 'export PEXELS_API_KEY="your_api_key_here"' >> ~/.zshrc
source ~/.zshrc
```

**免费额度**: 200次请求/小时，无月度限制

### 2. X平台认证（已配置）

**状态**: ✅ 已通过bird CLI配置

**如需重新配置**:
```bash
bird login
```

**验证配置**:
```bash
bird check
```

## 详细配置

### 工作流配置

编辑 `/Users/piaoxian/x-post-project/config.env`：

```bash
# 默认国家/地区
WORKFLOW_DEFAULT_COUNTRY=united-states

# 默认获取分类数量
WORKFLOW_DEFAULT_CATEGORY_COUNT=10

# 默认每个分类获取帖子数量
WORKFLOW_DEFAULT_POST_COUNT=5
```

### 图片配置

```bash
# 图片方向（landscape/vertical/square）
IMAGE_DEFAULT_ORIENTATION=landscape

# 搜索图片数量
IMAGE_DEFAULT_COUNT=5
```

### 字数限制

```bash
# 普通用户字数限制
X_CHAR_LIMIT_NORMAL=280

# Premium用户字数限制
X_CHAR_LIMIT_PREMIUM=10000
```

## 配置验证

运行测试脚本验证配置：

```bash
/Users/piaoxian/x-post-project/scripts/test-workflow.sh
```

## 故障排除

### Pexels API Key问题

**错误**: `Error: Pexels API Key required`

**解决方案**:
1. 确认API Key已正确设置
2. 检查环境变量：`echo $PEXELS_API_KEY`
3. 重新设置：`export PEXELS_API_KEY="your_key"`

### X认证问题

**错误**: `bird check` 显示认证失败

**解决方案**:
1. 重新登录：`bird login`
2. 检查认证文件：`cat ~/.config/bird/credentials.env`

### 网络问题

**错误**: `SSL: UNEXPECTED_EOF_WHILE_READING`

**解决方案**:
1. 检查网络连接
2. 尝试使用代理
3. 稍后重试

## 高级配置

### 自定义图片搜索

如需使用其他图片网站，可修改 `fetch-image.py` 脚本：

1. **Unsplash API**:
   - 注册: https://unsplash.com/developers
   - 修改API端点和认证方式

2. **Pixabay API**:
   - 注册: https://pixabay.com/api/docs/
   - 修改API端点和认证方式

### 自定义帖子获取

如需使用其他搜索方式，可修改 `fetch-posts.py` 脚本：

1. **bird search**:
   - 确保bird CLI已正确配置
   - 修改搜索查询格式

2. **agent-reach**:
   - 使用mcporter调用Exa搜索
   - 修改搜索参数

## 配置文件位置

- 配置模板: `/Users/piaoxian/x-post-project/config.env.example`
- 实际配置: `/Users/piaoxian/x-post-project/config.env`（需手动创建）
- 环境变量: `~/.zshrc` 或 `~/.bash_profile`

## 下一步

配置完成后，运行工作流：

```bash
/zcf:x-post-workflow
```
