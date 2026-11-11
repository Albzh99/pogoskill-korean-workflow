# PoGoskill Korean Workflow
将PoGoskill繁中已发布文章本土化为韩语，交付可编辑Word、SEO、真实图片/Guide清单、事实证据与至少两轮独立审核。六个独立角色：source、GA4、search、translate、review、operations。保留当前宿主模型与推理设置、独立上下文、完整译审与图文门槛。**完全不包含CMS上传、保存、发布、HTML模板或图片发布流程。**

这是私有仓库。其他使用者先由仓库所有者邀请并接受邀请，再用自己的GitHub账号克隆；仓库访问权不会授予Google/Semrush/网站账号权限。

## 只需怎样对Codex说
克隆后在Codex打开这个目录，说：
> 帮我初始化这个韩语翻译工作流，检查连接，主动启动需要的授权；不要让我在聊天里贴任何key。连接好后，按完整流程制作一篇本地Word和SEO，不上传CMS。
也可以补指定繁中文章URL、选题范围和自己的要求。Codex首次读AGENTS会运行无网络doctor，按knowledge/connections.md主动安装/引导依赖、发现对应插件授权、或启动本地官方OAuth浏览器/安全输入流程。宿主没有连接弹窗、GUI/TTY、图像生成、多Agent或渲染能力时须如实说明并引导可行替代，不能承诺任何宿主都能一键完成。

## 你仍需亲自完成
使用自己的Google Cloud OAuth客户端、启用API、取得GA4属性读取权限，登录并同意OAuth。Ads回退另需自己的developer token/账户权限；Semrush需自己的API套餐和key。安装软件或操作系统凭据库可能需要你确认。Logo/参考图、文章权利、完整韩语已发布+草稿清单、Guide等由你提供或授权读取，包中没有原用户素材与业务数据。

Python 3.11–3.14，虚拟环境及依赖见requirements.txt；默认OS安全凭据库，不保存明文token。新设备从零连接，绝不使用原机器旧目录/环境/凭据。流程/语言/产品/媒体完整规则在knowledge/stages/和knowledge/portable-contract.md，不依赖缺失全局自定义技能。Word可用宿主documents能力或python-docx+LibreOffice真实渲染，主图可用宿主图像生成工具；工具缺失不降低标准。

## 流程与验证
轻量候选和完整清单查重→GA4完整近7/前7/28天→Semrush KR优先核需求（仅不可用/配额/核心数据不足才韩国韩语Planner）→同source补完整源文→完整翻译本土化/主图/真实正文图/Guide/Word/SEO→独立全稿首审→主Agent逐项修订→同员至少第二轮实审→本地交付。
每篇只在gitignored work/保存输入、真实原始响应、七项交接、轮次报告和SHA256。散列绑定版本，不能证明事实/视觉/独立Agent已实际核验；真实Agent ID与证据必须记录。未关闭必改和关键图片缺口不可通过。

本地无网络检查：
```
python scripts/connections.py doctor --json
python -m unittest discover -s tests -v
python scripts/secret_scan.py
python scripts/manifest.py --check
```
首次发布/维护改动后先运行secret_scan，再用manifest.py重建清单，独立审查后提交。manifest只覆盖明确白名单的流程文件，不加入.local/work/.git或数据。secret_scan是防误提交补充，不能保证识别所有秘密；必须人工核白名单与差异。不要把真实文章、API数据、账户ID、用户素材或任何凭据加入仓库。

离线测试只验证实现及拒绝边界，**尚未在新使用者账号上实测OAuth/API**。doctor的存在状态不等于live access。详见knowledge/connections.md了解真实开通、同意及数据边界。

## 本地交接门槛
`python scripts/workflow.py handoff work/task/source/handoff.json`核七项与每个artifact(path/sha256)。
`python scripts/workflow.py delivery work/task/final-handoff.json`核本地交付：validation必须给selected_source、word、seo、hero、body_images、guide_evidence、fact_evidence、mechanical_report、visual_report引用（单个path/sha256对象或对象数组）；给stage_agent_ids记录source/ga4/search/translate/review实际互不相同ID。
validation.review_rounds按round=1,2...记录同一reviewer_id、report引用，第2轮起给逐项responses引用。最后一轮status=passed、manuscript_sha256=最终word散列，且input_bindings逐项完整等于上述所有当前引用。改变任何适用交付或事实证据必须相应复审，不能只更新散列沿用旧结论。此脚本只验证文件声明，独立Agent身份、实际完整审读、事实与图像判断须由执行与审核真正完成。
