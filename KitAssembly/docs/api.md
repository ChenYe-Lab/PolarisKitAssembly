# KitServer API 文档

本文档根据 `kitapp/kitserver/urls.py` 与 `kitapp/kitserver/views.py` 生成，覆盖 KitAssembly 当前暴露的页面、JSON API、文件下载与组装接口。

## 基本约定

| 项目 | 说明 |
| --- | --- |
| Base URL | 以 Django 部署根路径为准，本地开发通常为 `http://127.0.0.1:8000/` |
| JSON API | 请求体使用 `application/json` |
| 文件上传 | `/gg_assemble` 使用 `multipart/form-data` |
| Visitor Cookie | 默认 cookie 名为 `kitapp_visitor_id` |
| 下游服务 | 数据接口依赖 `WEBDATABASE_URL`，组装任务依赖 `LABDATABASE_URL` |

常见错误响应：

```json
{
  "success": false,
  "message": "method not allowed"
}
```

## 路由总览

| 路径 | 方法 | 类型 | 说明 |
| --- | --- | --- | --- |
| `/landing` | GET | HTML | 渲染入口页 |
| `/index` | GET | HTML | 渲染主应用页 |
| `/register_visitor` | POST | JSON | 注册访客 |
| `/register_vistor` | POST | JSON | `register_visitor` 的兼容拼写 |
| `/track_visit` | POST | JSON | 记录访问日志 |
| `/submit_feedback` | POST | JSON | 提交反馈 |
| `/initdata` | GET | JSON | 获取固定列表的 part/backbone/plasmid 初始数据 |
| `/assembly` | POST | JSON | 提交自动组装任务 |
| `/task_status/<taskID>` | GET | JSON | 查询组装任务状态 |
| `/getAssembly/<taskID>/<name>` | GET | File | 下载组装结果 `.gb` 文件 |
| `/gg_assemble` | POST | File | 上传 GenBank 文件并执行 Golden Gate 组装 |
| `/getTutorial` | GET | File | 下载 `StarterDocumentation.pdf` |
| `/getZip` | GET | File | 下载 `PaperSI.zip` |
| `/toturial` | GET | HTML/File | 浏览已构建 MkDocs 站点首页 |
| `/toturial/<doc_path>` | GET | HTML/File | 浏览已构建 MkDocs 站点文件 |

## 页面接口

### GET `/landing`

返回 `landing.html`。该视图使用 `ensure_csrf_cookie`，会确保响应中包含 CSRF cookie。

### GET `/index`

返回 `index.html`。该视图使用 `ensure_csrf_cookie`，会确保响应中包含 CSRF cookie。

## 访客与反馈

### POST `/register_visitor`

注册访客资料。`/register_vistor` 是同一接口的旧拼写兼容路由。

请求体：

```json
{
  "institution": "Example University",
  "lab_name": "Synthetic Biology Lab",
  "person_name": "Alice"
}
```

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `institution` | string | 是 | 机构名称 |
| `lab_name` | string | 是 | 实验室名称 |
| `person_name` | string | 是 | 联系人姓名 |

成功响应：

```json
{
  "success": true,
  "data": {
    "visitor_id": 1,
    "profile": {}
  }
}
```

错误状态：

| 状态码 | 场景 |
| --- | --- |
| `400` | JSON 非法或必填字段缺失 |
| `403` | 服务端登录 WebDatabase 失败 |
| `405` | 非 POST 请求 |
| `502` | 下游请求失败或响应缺少 visitor id |

### POST `/track_visit`

记录访客访问日志。`visitor_id` 可来自请求体，也可来自 cookie。

请求体：

```json
{
  "visitor_id": 1,
  "path": "/index",
  "method": "GET",
  "ip": "127.0.0.1",
  "user_agent": "Mozilla/5.0",
  "referer": "http://127.0.0.1:8000/landing"
}
```

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `visitor_id` | string/int | 否 | 缺省时读取 visitor cookie |
| `path` | string | 否 | 缺省为当前请求路径 |
| `method` | string | 否 | 缺省为当前请求方法 |
| `ip` | string | 否 | 缺省为客户端 IP |
| `user_agent` | string | 否 | 缺省为请求头 `User-Agent` |
| `referer` | string | 否 | 缺省为请求头 `Referer` |

成功响应透传 WebDatabase `createVisitorAccessLog` 的 JSON，并刷新 visitor cookie。

### POST `/submit_feedback`

提交问题或建议反馈。

请求体：

```json
{
  "visitor_id": 1,
  "feedback_type": "issue",
  "title": "Cannot download result",
  "content": "The generated GenBank file cannot be downloaded.",
  "contact_email": "user@example.com",
  "page_path": "/index"
}
```

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `visitor_id` | string/int | 否 | 缺省时读取 visitor cookie |
| `feedback_type` | string | 是 | 仅支持 `issue` 或 `suggestion` |
| `title` | string | 是 | 反馈标题 |
| `content` | string | 是 | 反馈内容 |
| `contact_email` | string | 否 | 联系邮箱 |
| `page_path` | string | 否 | 缺省为当前请求路径 |

成功响应透传 WebDatabase `createVisitorFeedback` 的 JSON，并刷新 visitor cookie。

## 数据初始化

### GET `/initdata`

获取前端初始数据。该接口通过固定名单从 WebDatabase 查询 E. coli 或 yeast 的 part、backbone、plasmid 信息。

Query 参数：

| 参数 | 类型 | 必填 | 允许值 |
| --- | --- | --- | --- |
| `currentCategory` | string | 是 | `ecoli`、`yeast` |
| `currentType` | string | 是 | `part`、`backbone`、`plasmid` |

示例：

```http
GET /initdata?currentCategory=ecoli&currentType=part
```

成功响应：

```json
{
  "success": true,
  "data": [
    {
      "name": "pEcP01",
      "status": true,
      "type": "promoter",
      "alias": "XRHL1-P020",
      "length": "123bp",
      "part": "parent-part-name",
      "user": "username"
    }
  ]
}
```

`part` 类型返回字段：

| 字段 | 说明 |
| --- | --- |
| `name` | 固定名单中的名称 |
| `status` | 是否查询成功 |
| `type` | `promoter`、`rbs`、`cds`、`terminator` |
| `alias` | 下游数据库 alias |
| `length` | 带 `bp` 后缀的长度 |
| `part` | 父 part 名称 |
| `ori` | yeast part 可能包含 |
| `marker` | yeast part 可能包含 |
| `user` | 数据所有者 |

`backbone` 类型返回字段：

```json
{
  "name": "pEcBB01",
  "status": true,
  "alias": "XSYB1",
  "length": "1234bp",
  "marker": "KanR",
  "ori": "pSC101",
  "user": "username",
  "scar": {
    "bbsi": "AB",
    "bsai": "CD"
  }
}
```

`plasmid` 类型返回字段：

```json
{
  "name": "pEcint01",
  "status": true,
  "alias": "BZC034",
  "length": "5000bp",
  "ori": "p15A",
  "marker": "AmpR",
  "user": "username",
  "scar": {
    "bbsi": "AB",
    "bsai": "CD"
  }
}
```

错误状态：

| 状态码 | 场景 |
| --- | --- |
| `400` | `currentCategory` 或 `currentType` 非法 |
| `403` | 服务端登录 WebDatabase 失败 |
| `405` | 非 GET 请求 |
| `502` | 下游请求失败 |

## 自动组装

### POST `/assembly`

提交组装任务。服务端会生成 UUID 作为任务名称，并调用 LabDatabase 的 `AssemblyWithoutRepo`。

请求体：

```json
{
  "part": ["pEcP01", "pEcR01"],
  "backbone": [3],
  "plasmid": ["pEcint01"]
}
```

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `part` | array | 是 | part 名称列表。若仅 1 个元素，会先查询其父 part id |
| `backbone` | array | 是 | backbone id 列表，原样传给 LabDatabase |
| `plasmid` | array | 是 | plasmid 名称列表 |

转发规则：

| 条件 | 发送给 LabDatabase 的内容 |
| --- | --- |
| `part` 长度为 1 | `part` 转为父 part id，`plasmid` 为空 |
| `part` 长度不为 1 | `part` 为空，`plasmid` 为 `part + plasmid` |

成功响应在 LabDatabase 响应基础上增加 `name` 字段：

```json
{
  "success": true,
  "name": "generated-uuid"
}
```

### GET `/task_status/<taskID>`

查询组装任务状态，响应内容和状态码透传 LabDatabase 的 `task_status/<taskID>`。

示例：

```http
GET /task_status/4a66f6bb-82ad-4ff7-9b90-7e4d83e26220
```

### GET `/getAssembly/<taskID>/<name>`

下载组装结果文件。服务端会请求 LabDatabase 的 `getAssembly/<name>?task_id=<taskID>`，并以 `.gb` 文件返回。

成功响应：

| Header | 值 |
| --- | --- |
| `Content-Type` | `application/octet-stream` |
| `Content-Disposition` | `attachment;filename=<name>.gb` |

## Golden Gate 文件组装

### POST `/gg_assemble`

上传至少两个 GenBank 文件，服务端执行 Golden Gate 组装并返回结果 GenBank 文件。

请求类型：`multipart/form-data`

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `files` | file[] | 是 | 至少 2 个 GenBank 文件 |
| `enzyme` | string | 否 | 默认为 `auto` |
| `output_name` | string | 否 | 输出文件名，默认为 `GG_Assembly_Result` |

示例：

```bash
curl -X POST http://127.0.0.1:8000/gg_assemble \
  -F "files=@part1.gb" \
  -F "files=@part2.gb" \
  -F "enzyme=bsai" \
  -F "output_name=my_assembly"
```

成功响应：

| Header | 值 |
| --- | --- |
| `Content-Type` | `chemical/seq-na-genbank` |
| `Content-Disposition` | `attachment; filename="<output_name>.gb"` |

错误状态：

| 状态码 | 场景 |
| --- | --- |
| `400` | 文件少于 2 个，或组装失败 |
| `405` | 非 POST 请求 |

## 文件下载与文档站点

### GET `/getTutorial`

下载 `kitapp/kitserver/static/StarterDocumentation.pdf`。文件不存在时返回 `{"success": false}`，状态码为 `400`。

### GET `/getZip`

下载 `kitapp/kitserver/static/PaperSI.zip`。文件不存在时返回 `{"success": false}`，状态码为 `400`。

### GET `/toturial`

返回已构建 MkDocs 站点的 `site/index.html`。

### GET `/toturial/<doc_path>`

返回 `site` 目录下的静态文档文件。服务端会校验解析后的路径必须位于 `site` 目录内，防止目录穿越。

示例：

```http
GET /toturial/kitassembly/overview/
GET /toturial/assets/kitassembly/image1.png
```

找不到文件时返回 `404`。

## 下游服务依赖

| 配置项 | 用途 |
| --- | --- |
| `WEBDATABASE_URL` | 查询 part/backbone/plasmid 元数据、访客和反馈接口 |
| `LABDATABASE_URL` | 提交组装任务、查询任务状态、下载组装结果 |
| `API_LOGIN_URL` | 登录下游服务，缺省为 `WEBDATABASE_URL + "login"` |
| `API_LOGIN_USERNAME` | 下游登录用户名 |
| `API_LOGIN_PASSWORD` | 下游登录密码 |
| `API_LOGIN_USERNAME_FIELD` | 登录表单用户名字段，默认 `username` |
| `API_LOGIN_PASSWORD_FIELD` | 登录表单密码字段，默认 `password` |
| `API_LOGIN_NEXT` | 可选登录跳转字段 |

