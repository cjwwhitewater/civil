# 安装和使用指南

## 环境要求

- Python 3.7 或更高版本
- pip 包管理器

## 安装步骤

### 1. 检查Python环境

在命令行中运行以下命令检查Python是否已安装：

```bash
python --version
# 或者
py --version
```

如果显示版本号，说明Python已安装。如果提示命令不存在，请先安装Python。

### 2. 安装依赖包

在项目目录下运行：

```bash
pip install -r requirements.txt
```

如果遇到权限问题，可以尝试：

```bash
pip install --user -r requirements.txt
```

### 3. 启动应用

#### 方法一：直接运行
```bash
python app.py
```

#### 方法二：使用启动脚本（Windows）
双击 `start.bat` 文件

### 4. 访问应用

打开浏览器，访问：`http://localhost:5000`

## 常见问题

### Q: 提示 "ModuleNotFoundError: No module named 'flask'"
A: 请确保已正确安装依赖包：
```bash
pip install -r requirements.txt
```

### Q: 端口5000被占用
A: 可以修改 `app.py` 文件中的端口号：
```python
app.run(debug=True, host='0.0.0.0', port=5001)  # 改为5001或其他端口
```

### Q: 爬虫无法获取数据
A: 这可能是由于：
1. 网络连接问题
2. 目标网站结构发生变化
3. 被反爬虫机制阻止

建议检查网络连接，或稍后重试。

### Q: 页面显示异常
A: 请确保：
1. 浏览器支持现代CSS和JavaScript
2. 没有禁用JavaScript
3. 网络连接正常

## 测试建议

1. 首先尝试查询"北京"、"上海"等大城市
2. 检查控制台是否有错误信息
3. 如果某个城市查询失败，尝试其他城市

## 开发模式

如果需要修改代码，应用会自动重载（debug模式已启用）。

## 生产部署

在生产环境中，建议：
1. 关闭debug模式
2. 使用WSGI服务器（如Gunicorn）
3. 添加缓存机制
4. 配置反向代理（如Nginx） 