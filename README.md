# FOFA Quake Hunter MCP Server

一个用于查询 FOFA、Quake 和 Hunter 网络空间测绘平台的 MCP (Model Context Protocol) 服务器。

[English](#english) | [中文](#中文)

---

## 中文

### 功能特性

- 🔍 **FOFA 查询**: 支持 FOFA 网络空间测绘系统的资产查询
- 🌐 **Quake 查询**: 支持 360 Quake 网络空间测绘系统的深度查询
- 🦅 **Hunter 查询**: 支持奇安信鹰图平台的资产查询
- 🤖 **AI 友好**: 所有参数支持自然语言对话设置
- ⚙️ **灵活配置**: 可按需配置单个或多个平台

### 安装

#### 使用 uvx (推荐)

```bash
uvx fofa-quake-hunter-mcp
```

#### 使用 pip

```bash
pip install fofa-quake-hunter-mcp
```

#### 从源码安装

```bash
git clone https://github.com/RuoJi6/fofa_quake_hunter_mcp.git
cd fofa_quake_hunter_mcp
pip install -e .
```

### 配置

#### 在 MCP 客户端中配置

在 MCP 配置文件中添加（例如 Claude Desktop 的 `claude_desktop_config.json` 或 Kiro 的 `.kiro/settings/mcp.json`）：

```json
{
  "mcpServers": {
    "fofa-quake-hunter": {
      "command": "uvx",
      "args": ["fofa-quake-hunter-mcp"],
      "env": {
        "FOFA_KEY": "your_fofa_api_key",
        "QUAKE_KEY": "your_quake_api_key",
        "HUNTER_KEY": "your_hunter_api_key"
      }
    }
  }
}
```

**注意**: 
- 你可以只配置需要使用的平台，未配置的工具在调用时会返回友好的配置提示
- FOFA_EMAIL 是可选的，大多数情况下只需要 FOFA_KEY

#### 获取 API Key

- **FOFA**: 登录 [https://fofa.info](https://fofa.info) → 个人中心 → API Key
- **Quake**: 登录 [https://quake.360.net](https://quake.360.net) → 个人中心 → 密钥管理
- **Hunter**: 登录 [https://hunter.qianxin.com](https://hunter.qianxin.com) → 个人中心 → API管理

### 功能说明

#### 1. FOFA 查询 (`fofa_search`)

**主要参数**:
- `query`: 查询语法（支持多种匹配和逻辑运算符）
- `size`: 返回条数（默认 100，最大 10000）
- `page`: 页码（默认 1）
- `fields`: 返回字段（默认：`host,ip,port,domain,title`）

**匹配运算符**:
- `=` - 匹配（模糊匹配），`=""`时可查询不存在字段或值为空的情况
- `==` - 完全匹配，`==""`时可查询存在且值为空的情况
- `!=` - 不匹配，`!=""`时可查询值为空的情况
- `*=` - 模糊匹配，使用 `*` 或 `?` 通配符（个人版及以上）

**逻辑运算符**:
- `&&` - 与（AND）
- `||` - 或（OR）
- `()` - 括号确认查询优先级

**查询示例**:
```
# 基础匹配
body="miner start"
domain="example.com"

# 完全匹配
server=="Microsoft-IIS/10"

# 不匹配
body="admin" && country!="CN"

# 模糊匹配（通配符）
banner*="mys??"

# 逻辑 AND（&&）
domain="example.com" && port="443"
title="login" && country="CN"

# 逻辑 OR（||）
title="admin" || title="后台"
port="80" || port="443"

# 优先级控制
(title="admin" || title="login") && country="CN"
```

#### 2. Quake 查询 (`quake_search`)

**主要参数**:
- `query`: 查询语法（使用冒号语法：`field:value`）
- `size`: 返回条数（默认 100）
- `include`: 包含字段（逗号分隔，见下方可用字段列表）
- `exclude`: 排除字段（逗号分隔）
- `pagination_id`: 深度翻页 ID（5分钟有效）
- `start_time` / `end_time`: 时间范围（UTC格式：2020-10-14 00:00:00）

**查询语法**:
- 使用冒号 `:` 连接字段和值，如 `port:443`、`title:"keyword"`
- 逻辑运算符：`AND`、`OR`、`NOT`（大写）
- 括号 `()` 控制优先级

**可用字段（注册用户 - 服务数据）**:
```
ip, port, hostname, transport, asn, org, service.name, 
location.country_cn, location.province_cn, location.city_cn, 
service.http.host, service.http.title, service.http.server
```

**可用字段（会员用户 - 额外服务数据字段）**:
```
time, domain, service.response, service.cert, 
components.product_catalog, components.product_type, 
components.product_level, components.product_vendor, 
location.country_en, location.province_en, location.city_en, 
location.district_en, location.district_cn, location.isp, 
service.http.body, components.product_name_cn, components.version, 
service.http.infomation.mail, service.http.favicon.hash, 
service.http.favicon.data, service.http.status_code
```

**查询示例**:
```
# 单条件查询
port:443
title:"后台管理"

# 逻辑 AND
port:3389 AND country:"China"
port:3389 AND country_cn:"中国" AND NOT province_cn:"广东"

# 逻辑 OR
port:3389 AND (country:"China" OR country:"United States")

# 逻辑 NOT
port:80 AND NOT response:"baidu"
service:http AND NOT response:"baidu"

# 优先级控制
port:3389 AND (country:"China" OR country:"United States") AND NOT province_cn:"广东"
```

**字段筛选示例**:
```
# 只返回 IP 和端口
include: "ip,port"

# 返回 IP、端口和网页标题
include: "ip,port,service.http.title"

# 返回基础信息和组织
include: "ip,port,service.http.title,org,asn"

# 返回完整信息（会员）- 注意使用具体的组件字段
include: "ip,port,service.http.title,service.http.server,domain,components.product_name_cn,components.version"
```

**⚠️ 常见字段错误**:
- ❌ `components` → ✅ 使用具体字段如 `components.product_name_cn`
- ❌ `as_org` → ✅ 使用 `asn` 和 `org`
- ❌ `as_organization` → ✅ 使用 `asn` 和 `org`

#### 3. Hunter 查询 (`hunter_search`)

**主要参数**:
- `query`: 查询语法（使用等号语法：`field="value"`）
- `page_size`: 每页条数（可选：10/50/100，默认 10）
- `page`: 页码（默认 1）
- `is_web`: 资产类型（1=web资产，2=非web资产，3=全部）
- `fields`: 返回字段
- `start_time` / `end_time`: 时间范围（格式：YYYY-MM-DD）

**匹配运算符**:
- `=` - 模糊查询，查询包含关键词的资产
- `==` - 精确查询，查询有且仅有关键词的资产
- `!=` - 模糊剔除，剔除包含关键词的资产。使用 `!=""` 可查询值不为空的情况
- `!==` - 精确剔除，剔除有且仅有关键词的资产

**逻辑运算符**:
- `&&` - 与（AND）
- `||` - 或（OR）
- `()` - 括号内表示查询优先级最高

**查询示例**:
```
# 模糊匹配
web.body="keyword"
domain="example.com"

# 精确匹配
web.title=="登录"
ip=="1.1.1.1"

# 模糊剔除
web.body="admin" && ip!="1.1.1.1"

# 精确剔除
domain!=="example.com"

# 查询值不为空
ip!=""

# 逻辑 AND（&&）
web.title="后台管理系统" && ip="1.1.1.1"
domain="example.com" && web.status_code="200"

# 逻辑 OR（||）
domain="example.com" || domain="test.com"
web.title="admin" || web.title="login"

# 优先级控制
(web.title="admin" || web.title="login") && ip!=""
```

### AI 对话示例

```
用户: 查询 FOFA，body="admin"，返回 50 条
AI: 将设置 query="body=\"admin\"", size=50

用户: 查询 Quake，标题为"后台管理"，只返回 IP 和端口
AI: 将设置 query='title:"后台管理"', include='ip,port'

用户: 查询 Hunter，web.title="登录"，只要 web 资产，每页 100 条
AI: 将设置 query='web.title="登录"', is_web=1, page_size=100
```

### 功能对比

| 功能 | FOFA | Quake | Hunter |
|------|------|-------|--------|
| 返回条数控制 | ✅ size (1-10000) | ✅ size (1-500) | ✅ page_size (10/50/100) |
| 字段控制 | ✅ fields | ✅ include/exclude | ✅ fields |
| 翻页 | ✅ page | ✅ pagination_id | ✅ page |
| 时间范围 | ❌ | ✅ start_time/end_time | ✅ start_time/end_time |
| 资产类型筛选 | ❌ | ❌ | ✅ is_web |

### 开发

```bash
# 克隆仓库
git clone https://github.com/RuoJi6/fofa_quake_hunter_mcp.git
cd fofa_quake_hunter_mcp

# 安装依赖
uv sync

# 运行服务器
uv run fofa-quake-hunter-mcp
```

### 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

### 贡献

欢迎提交 Issue 和 Pull Request！

---

## English

### Features

- 🔍 **FOFA Search**: Query FOFA cyberspace mapping platform
- 🌐 **Quake Search**: Query 360 Quake cyberspace mapping platform with deep pagination
- 🦅 **Hunter Search**: Query Qianxin Hunter (鹰图) platform
- 🤖 **AI-Friendly**: All parameters support natural language configuration
- ⚙️ **Flexible Config**: Configure only the platforms you need

### Installation

#### Using uvx (Recommended)

```bash
uvx fofa-quake-hunter-mcp
```

#### Using pip

```bash
pip install fofa-quake-hunter-mcp
```

#### From Source

```bash
git clone https://github.com/RuoJi6/fofa_quake_hunter_mcp.git
cd fofa_quake_hunter_mcp
pip install -e .
```

### Configuration

#### Configure in MCP Client

Add to your MCP configuration file (e.g., Claude Desktop's `claude_desktop_config.json` or Kiro's `.kiro/settings/mcp.json`):

```json
{
  "mcpServers": {
    "fofa-quake-hunter": {
      "command": "uvx",
      "args": ["fofa-quake-hunter-mcp"],
      "env": {
        "FOFA_KEY": "your_fofa_api_key",
        "QUAKE_KEY": "your_quake_api_key",
        "HUNTER_KEY": "your_hunter_api_key"
      }
    }
  }
}
```

**Note**: 
- You can configure only the platforms you need. Unconfigured tools will show friendly setup instructions when called.
- FOFA_EMAIL is optional and only needed for some API endpoints. Most users only need FOFA_KEY.

#### Get API Keys

- **FOFA**: Login to [https://fofa.info](https://fofa.info) → Personal Center → API Key
- **Quake**: Login to [https://quake.360.net](https://quake.360.net) → Personal Center → Key Management
- **Hunter**: Login to [https://hunter.qianxin.com](https://hunter.qianxin.com) → Personal Center → API Management

### Tools

#### 1. FOFA Search (`fofa_search`)

**Key Parameters**:
- `query`: Search query (e.g., `body="admin"`, `domain="example.com"`)
- `size`: Number of results (default: 100, max: 10000)
- `page`: Page number (default: 1)
- `fields`: Fields to return (default: `host,ip,port,domain,title`)

**Query Examples**:
```
body="miner start"
domain="example.com" && port="443"
title="login" && country="CN"
```

#### 2. Quake Search (`quake_search`)

**Key Parameters**:
- `query`: Search query (e.g., `title:"admin"`, `ip:1.1.1.1`)
- `size`: Number of results (default: 100)
- `include`: Fields to include (e.g., `ip,port,service.http.title`)
- `exclude`: Fields to exclude
- `pagination_id`: Pagination ID for deep paging (5-minute expiry)
- `start_time` / `end_time`: Time range (UTC format)

**Query Examples**:
```
title:"admin panel"
ip:1.1.1.1 AND port:80
service:http AND country:"china"
```

#### 3. Hunter Search (`hunter_search`)

**Key Parameters**:
- `query`: Search query (e.g., `web.body="admin"`, `ip="1.1.1.1"`)
- `page_size`: Results per page (options: 10/50/100, default: 10)
- `page`: Page number (default: 1)
- `is_web`: Asset type (1=web assets, 2=non-web assets, 3=all)
- `fields`: Fields to return
- `start_time` / `end_time`: Time range (format: YYYY-MM-DD)

**Query Examples**:
```
web.body="keyword"
web.title="admin panel"
domain="example.com" && web.status_code="200"
```

### Feature Comparison

| Feature | FOFA | Quake | Hunter |
|---------|------|-------|--------|
| Result Count | ✅ size (1-10000) | ✅ size (1-500) | ✅ page_size (10/50/100) |
| Field Control | ✅ fields | ✅ include/exclude | ✅ fields |
| Pagination | ✅ page | ✅ pagination_id | ✅ page |
| Time Range | ❌ | ✅ start_time/end_time | ✅ start_time/end_time |
| Asset Type Filter | ❌ | ❌ | ✅ is_web |

### Development

```bash
# Clone repository
git clone https://github.com/RuoJi6/fofa_quake_hunter_mcp.git
cd fofa_quake_hunter_mcp

# Install dependencies
uv sync

# Run server
uv run fofa-quake-hunter-mcp
```

### License

MIT License - see [LICENSE](LICENSE) file for details

### Contributing

Issues and Pull Requests are welcome!

### Links

- **Repository**: [https://github.com/RuoJi6/fofa_quake_hunter_mcp](https://github.com/RuoJi6/fofa_quake_hunter_mcp)
- **PyPI**: [https://pypi.org/project/fofa-quake-hunter-mcp/](https://pypi.org/project/fofa-quake-hunter-mcp/)
- **Issues**: [https://github.com/RuoJi6/fofa_quake_hunter_mcp/issues](https://github.com/RuoJi6/fofa_quake_hunter_mcp/issues)
