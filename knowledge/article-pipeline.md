# 本地韩语翻译流水线
主Agent只调度，读取本次目标、policy、本篇短交接；独立source→GA4→search→translate→review，operations按需直入。各角色独立Agent，首次fork_turns="none"，继承当前模型/推理，不设置降级模型，不合并角色；没有多Agent能力则报告环境缺口，不伪造独立审核。
实际顺序：轻量source候选/全量清单查重→GA4基数趋势→Semrush韩国需求（有记录的不可用/配额/核心不足才Planner）定题→同一source补完整原件→完整翻译、本土化、主图/真实正文图、Guide、Word/SEO→独立全稿首审→主Agent逐项修改回应→同员第二轮或更多复审→本地交付。
每篇work/<date>-<slug>/保存task.json和各阶段七项handoff.json。七项为goal/completed/decisions/artifacts(path+sha256)/validation/unresolved/next_context。选定source补件单独绑定，不覆盖候选。各角色只读自己的规则和必要原件，不传父会话/旧篇记录。大响应落文件并返回路径/散列；必要原件完整实际读。
协调者须实际调用独立Agent并记录真实ID，文件检查不能证明Agent独立。每轮review索引含round/reviewer/input hashes/前轮报告/逐项回应/变更证据；首轮无必改也要二轮。至少两轮不等于自动通过，必改未关闭不得完成。散列变化使对应旧通过失效；未变有效证据复用。同篇原译者/审核员续作，退出重建需记录原因；新篇新Agent。
operations只改本次范围，内容/事实/步骤/主图变化须相应复审，流量或关键词任务不重跑无关上游。完成即接续不空等，真实外部阻塞记错误/缺口/下一步。最终一次核对文件散列、审核、机械/视觉证据、七项交接，交付本地Word/SEO。任何CMS上传、保存、发布、HTML模板均不在本包范围。
