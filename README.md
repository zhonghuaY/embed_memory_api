# Embedding API Service

独立的文本嵌入向量服务，兼容 OpenAI `/v1/embeddings` 接口，使用 [sentence-transformers](https://www.sbert.net/) 本地模型推理。

## 快速开始

```bash
# 创建虚拟环境并安装依赖
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 启动服务
./run.sh
# 或直接运行
python3 main.py
```

服务默认运行在 `http://0.0.0.0:8786`。

## 配置

通过环境变量或 `config.env` 文件配置：

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `EMBED_HOST` | `0.0.0.0` | 监听地址 |
| `EMBED_PORT` | `8786` | 监听端口 |
| `EMBED_MODEL` | `all-MiniLM-L6-v2` | sentence-transformers 模型名 |
| `EMBED_LOG_LEVEL` | `INFO` | 日志级别 |

## API 接口

### POST /v1/embeddings

生成文本嵌入向量，兼容 OpenAI 格式。

**请求：**

```json
{
  "input": "Hello, world!",
  "model": "all-MiniLM-L6-v2"
}
```

支持批量输入：

```json
{
  "input": ["text1", "text2", "text3"]
}
```

**响应：**

```json
{
  "object": "list",
  "data": [
    {
      "object": "embedding",
      "index": 0,
      "embedding": [0.0123, -0.0456, ...]
    }
  ],
  "model": "all-MiniLM-L6-v2",
  "usage": {
    "prompt_tokens": 2,
    "total_tokens": 2
  }
}
```

### GET /v1/models

返回可用模型列表。

### GET /health

健康检查，返回服务状态和版本。

## 测试

```bash
# 自动启动服务并运行全部测试
python3 test_api.py --auto

# 如果服务已在运行
python3 test_api.py
```

## 使用示例

```bash
# 单文本嵌入
curl -X POST http://localhost:8786/v1/embeddings \
  -H "Content-Type: application/json" \
  -d '{"input": "Hello, world!"}'

# 批量嵌入
curl -X POST http://localhost:8786/v1/embeddings \
  -H "Content-Type: application/json" \
  -d '{"input": ["apple", "banana", "cherry"]}'
```

## Systemd 服务管理

### 一键安装（用户级服务，无需 sudo）

```bash
./install.sh
```

安装后服务会自动启动并设置为开机自启。

### 常用命令

```bash
# 查看状态
systemctl --user status embed-api

# 查看日志
journalctl --user -u embed-api -f

# 重启
systemctl --user restart embed-api

# 停止
systemctl --user stop embed-api

# 卸载
./uninstall.sh
```

### 注意事项

- 使用 `loginctl enable-linger` 确保用户服务在未登录时也能运行（install.sh 会自动执行）
- 服务配置文件位于 `~/.config/systemd/user/embed-api.service`
- 修改 `config.env` 后需 `systemctl --user restart embed-api` 生效

## 项目结构

```
embed_memory_api/
├── main.py              # FastAPI 服务主文件
├── test_api.py          # 测试用例 (33 cases)
├── requirements.txt     # Python 依赖
├── config.env           # 配置文件
├── embed-api.service    # systemd 服务单元
├── install.sh           # 安装脚本
├── uninstall.sh         # 卸载脚本
├── run.sh               # 手动启动脚本
└── README.md
```
