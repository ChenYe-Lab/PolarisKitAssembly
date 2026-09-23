# KitAssembly 配置

已有部署保留 `.env`，不要用示例覆盖凭据。仅首次部署复制 `.env.example`。
进程环境变量优先于 `.env`。修改配置后重启 Django 服务。

## 必需配置

- `SECRET_KEY`：独立生成的密钥；缺失、空值或示例占位值会阻止启动。
- `WEBDATABASE_URL`、`LABDATABASE_URL`：实际可访问的 HTTP(S) 服务地址。
  禁止空值、URL 内嵌凭据、查询参数和 fragment；自动补齐末尾 `/`。
- 服务登录功能需要 `API_LOGIN_USERNAME` 和 `API_LOGIN_PASSWORD`；两者必须一起设置。
  均为空时页面仍可启动，但需要服务登录的操作不可用。
- `API_LOGIN_URL` 未设置或为空时，由 WebDatabase 地址加 `login` 得到。

## 开发与生产

代码默认 `DEBUG=False`、仅允许 localhost、127.0.0.1 和 IPv6 本机地址，
且没有额外 CSRF 信任域名。生产环境应显式设置 `ALLOWED_HOSTS` 和需要的
`CSRF_TRUSTED_ORIGINS`（逗号分隔），不再自动信任 ngrok 通配域名。
本地 HTTP 开发请设置 `DEBUG=True`。示例文件采用本地开发配置。

`SESSION_COOKIE_SECURE`、`CSRF_COOKIE_SECURE`、`VISITOR_COOKIE_SECURE` 默认等于
`not DEBUG`，也可显式覆盖。布尔配置接受 true/false、1/0、yes/no、on/off；
非法值直接报配置错误。`VISITOR_COOKIE_SAMESITE=None` 要求 secure cookie。

`API_REQUEST_TIMEOUT` 为正数秒，应用于所有下游 Session 请求，而不仅是登录。
`VISITOR_COOKIE_MAX_AGE` 为正整数秒。

## 文件路径

- 教程文件：`TUTORIAL_ADDRESS`。
- ZIP 下载：`ZIP_ADDRESS`。
- 教程站点：`TUTORIAL_SITE_ROOT`，默认 `kitapp/site`。
- SQLite 文件：`SQLITE_PATH`，默认原来的 `kitapp/db.sqlite3`。

相对路径以包含 manage.py 的 kitapp 目录为基准。缺少可选下载文件返回 404。
旧拼写 `TUROERIAL_ADDRESS` 仍可读取；非空的新拼写优先，建议逐步迁移。
不自动移动或覆盖已有数据库与下载文件。静态资源 URL 为根路径
`/kitserver/static/`，避免页面路径不同导致相对地址错误。

本次只调整配置及其使用位置，未改动套件清单、组装算法或服务登录协议。
示例中的具体账号密码已移除；如果此前的示例凭据仍在使用，应在服务端更换。
