# 首次连接：Codex主动引导
AGENTS要求Codex第一次先doctor，缺依赖则用本地虚拟环境安装requirements，缺连接则主动发现和启动宿主对应插件授权；宿主工具须确实支持对应GA4/地区查询，不能拿Google Drive授权或美国英语Planner冒用。若没有充分插件能力，运行下方本地流程。doctor无网络，只报告依赖与凭据存在，不表示已验证可用。

Python 3.11–3.14（当前google-ads 35要求Python<3.15）；`python -m venv .venv` 后使用虚拟环境python执行 `-m pip install -r requirements.txt`。Windows建议py -3，必须实际版本检查。Linux的OS凭据库需要已解锁的Secret Service/兼容后端；无安全后端脚本失败关闭，不写明文令牌。Word渲染另需LibreOffice或宿主原生文档工具，图像生成及独立多Agent需宿主对应能力。

## 使用者仍必须完成的步骤
Google Cloud：用自己的项目启用Google Analytics Data API，配置OAuth同意屏幕/测试用户，创建Desktop app OAuth client并下载JSON。GA4账号需要目标属性读取权；属性ID、host、属性时区由使用者提供，包中无原用户ID。仅known property读Data API，不强制启用Analytics Admin。Google Ads另需Google Ads API启用、自己的developer token相应访问级别、可用Ads客户账户/管理账户权限，OAuth adwords授权；测试级developer token或账户限制可能无法取真实量，不能宣称已可用。
Codex运行 `python scripts/connections.py configure --property YOUR_ID --host tw.pogoskill.com --timezone YOUR_IANA_TIMEZONE`（非秘密配置）；Ads配置 `configure --ads-customer YOUR_CUSTOMER_ID`，管理账户可加 `--ads-login-customer YOUR_MANAGER_ID`。
Codex主动运行 `connect ga4` 打开本地文件选择器（无GUI则TTY输入文件路径），选择使用者自己的Desktop client JSON。官方OAuth库会启动默认浏览器、state验证、PKCE及随机回环端口。真人登录并同意；关闭/取消或权限不足是明确阻塞，不循环授权。OAuth令牌连同客户端信息只入OS凭据库，不进入聊天、仓库或原目录。不接受原用户client JSON。
Semrush没有本包可用OAuth；真人需自己开通API套餐/额度，Codex主动运行 `connect semrush`，本地隐藏输入框接收key并存OS凭据库。无GUI时只在安全交互TTY用getpass；不支持GUI/TTY的宿主应说明具体限制并引导用户本机终端执行，绝不要求把key贴聊天。Ads developer token同理运行 `connect ads-token`，随后 `connect ads` 选择自己的client JSON并浏览器同意。不要把任何秘密作为CLI参数、环境命令或聊天消息传入。

## 实际只读查询
`python scripts/connections.py query ga4 --paths /example.html --out work/task/ga4.json`
GA4先取实际属性timezone并和个人配置核对；按完整昨日7/前7/28、hostName精确过滤、pagePath候选，screenPageViews分页原始响应。必须人工查看metadata阈值/采样/缺行和域名覆盖；仅HTTP成功不足以宣布核查通过。
`python scripts/connections.py query semrush --keywords "포켓몬고 관련 검색어" --out work/task/semrush.json`
真实phrase_this/database=kr，逐词原始列/月趋势留证据。无结果不当0，错误只留安全代码。记录连接不可用/配额或核心数据不足的真实证据后才可运行：
`python scripts/connections.py query ads --keywords "포켓몬고 관련 검색어" --fallback-reason semrush_data_insufficient_for_core_keywords --out work/task/planner.json`
另两种合法理由semrush_unavailable、semrush_quota_exhausted。脚本要求声明理由，不能自动证明声明真实，search Agent须核证据。Ads真实历史量和月份曲线，韩国2410/韩语1012/GOOGLE_SEARCH，广告竞争不当SEO难度。Google不代表Naver。
所有响应仅允许work/或.local/输出。脚本抑制原始异常、OAuth URL及秘密值；错误输出仅安全类别，日志中不应记录HTTP完整URL。API失败并非0量；未实际查询不能说连接验证成功。doctor不读网络；connect/query会联网且需要本次用户授权范围。

## CMS与私有输入
本包不连接或写入CMS。查重由使用者提供完整已发布+草稿清单；Guide用合法只读导出或官方公开韩语指南。原用户资产、文章、私有清单、API响应、key/token/config均不继承。完整清单缺失不能宣称草稿已查重；仍可进行有证据的其他检查。

依赖维护：2026-11-11公开PyPI核google-ads最新35.0.0，本包固定>=35,<36。Google Ads会日落旧API，维护时核官方支持/SDK并更新及实测；不以离线测试保证长期在线可用。
