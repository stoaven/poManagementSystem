# Tasks

## 1. 工程骨架与本地开发环境

- [ ] 1.1 创建 `backend/` 目录结构（`app/{core,db,models,schemas,repositories,services,api/v1}`、`tests/`、`alembic/`），写入 `requirements.txt`（fastapi、uvicorn、sqlalchemy、alembic、pydantic-settings、pyjwt、pymysql、pytest、httpx），验证 `pip install -r requirements.txt` 成功且 `python -c "import fastapi, sqlalchemy, alembic"` 无报错
- [ ] 1.2 搭建 FastAPI 应用骨架 `app/main.py`（应用实例、`/api/v1` 路由挂载点、CORS 中间件允许前端来源、`/health` 健康检查），验证 `uvicorn app.main:app --reload` 启动后 `curl localhost:8000/health` 返回 200
- [ ] 1.3 实现 `app/core/config.py`（pydantic-settings 读取 `DATABASE_URL`、`JWT_SECRET`、`JWT_EXPIRE_MINUTES`、`CORS_ORIGINS`）与 `.env.example`，验证缺配置时启动报错并提示缺失项、配置齐全时正常启动
- [ ] 1.4 创建 `docker-compose.yml` 提供 MySQL 8（utf8mb4、root 密码、持久化卷、端口 3306），验证 `docker compose up -d` 后 `docker compose exec db mysql -uroot -p... -e "SELECT VERSION()"` 返回 8.x 且字符集为 utf8mb4
- [ ] 1.5 创建 `frontend/` 工程（Vite + Vue 3 + TS + Element Plus + Pinia + Vue Router + Axios + Vitest），验证 `npm install && npm run build` 成功产出 `dist/`，`npm test` 可运行
- [ ] 1.6 在根 `README.md` 写明本地启动步骤（docker-compose、后端 uvicorn、前端 npm run dev）与目录职责，验证按 README 从零执行可跑通 `/health` 与前端首页

## 2. 数据层：模型与数据库迁移

- [ ] 2.1 定义 `app/models/user.py`（`users` 表：`phone VARCHAR(20)` 唯一索引 `uk_users_phone`、`username VARCHAR(64)` 可重名、`authority VARCHAR(10)` 默认 `normal`、`is_active`，以及统一状态与审计字段 `status TINYINT` 默认 0（0 正常 / 1 已删除）、`operator VARCHAR(20)`（FK → users.phone，可空）、`created_at`、`updated_at`），验证迁移建表成功且 `SHOW CREATE TABLE users` 确认 phone 唯一、authority 默认值正确、status 与审计字段齐全
- [ ] 2.2 定义 `app/models/shipment.py`（`shipments` 表：**只有 shipment_num 一个业务字段**，含 `shipment_num VARCHAR(64)` 与唯一索引 `uk_shipments_shipment_num`、`lifecycle VARCHAR(20)` 默认 `draft`（业务状态：draft/confirmed/completed/cancelled），以及统一状态与审计字段 `status TINYINT` 默认 0、`operator VARCHAR(20)`（FK → users.phone）、`created_at`、`updated_at`），验证迁移建表成功且确认生命周期与状态两列语义分离
- [ ] 2.3 定义 `app/models/charge_info.py`（`charge_info` 表：shipment_id 外键、job_num、九个分类字段**全部为 VARCHAR 内容列，不设指向选项表的外键**、`os_cost_amt` 与 `os_sell_amt` 为 `DECIMAL(14,2)`、`local_cost_amt` 与 `local_sell_amt` 为 nullable DECIMAL，以及统一状态与审计字段 `status TINYINT` 默认 0、`operator VARCHAR(20)`（FK → users.phone）、`created_at`、`updated_at`），验证迁移建表成功且列类型与索引正确
- [ ] 2.4 定义 `app/models/options.py`（九张同构选项表：charge_codes、descriptions、departments、branches、currencies、cost_tax_ids、creditors、debtors、inv_types，字段均为 code 唯一、name 可空、is_active，以及统一状态与审计字段 `status TINYINT` 默认 0、`operator VARCHAR(20)`（FK → users.phone）、`created_at`、`updated_at`），验证迁移建表成功且九张表的唯一索引均生效、status 与审计字段与其它表一致
- [ ] 2.5 在迁移中加入 MySQL CHECK 约束（`os_cost_amt >= 0`、`os_sell_amt >= 0`、`authority IN ('admin','normal')`、所有表 `status IN (0,1)`）并建立 `operator` → `users.phone` 的外键（**带 `ON UPDATE CASCADE`**，使改号后历史审计记录同步跟随），验证插入负数金额、非法 authority 与非法 status 的行均被数据库拒绝、修改用户手机号后引用它的审计字段同步更新
- [ ] 2.6 实现 `app/db/session.py`（engine、`sessionmaker`、`get_db` 依赖，**一个请求一个事务**，service 不自行 commit）与 `app/db/base.py`，验证 `alembic downgrade base && alembic upgrade head` 可往返执行且数据表恢复
- [ ] 2.7 编写 `tests/conftest.py`（测试用 session fixture、独立测试库、`client` fixture、种子管理员/普通用户/货运订单/费用信息/选项项 fixture），验证 `pytest` 能跑通一条健康检查用例且不污染开发库

## 3. 认证能力（`auth`）

- [ ] 3.1 实现 `app/core/security.py`（JWT 签发与校验、令牌过期判定；**不含任何密码哈希逻辑**），验证单元测试覆盖：篡改令牌校验失败、过期令牌被拒绝、签发的令牌可解析出用户标识
- [ ] 3.2 实现 `app/schemas/auth.py` 与 `POST /api/v1/auth/login`、`GET /api/v1/auth/me`（**登录凭据只有手机号，不要求密码或验证码**），验证测试覆盖：只提交手机号即可登录成功并返回令牌与手机号/用户名称/权限级别、请求体不含任何密码或验证码字段、手机号未开通返回 401 且不签发令牌、已停用账号登录被拒
- [ ] 3.3 实现认证依赖 `app/core/deps.py`（从 `Authorization: Bearer` 提取令牌、校验签名与过期、查询用户并校验 `is_active`、未认证抛 401），验证单元测试覆盖：缺少令牌 / 令牌无效 / 账号已停用 三种情形均返回 401
- [ ] 3.4 验证权限实时生效：每次请求从数据库读取当前用户的 `authority`（不固化进令牌），验证测试覆盖：把某用户的权限由 normal 改为 admin 后，该用户既有令牌在下一次请求管理员接口时即被放行；停用后下一次请求即被拒
- [ ] 3.5 实现 CLI 脚本 `python -m app.cli create-admin --phone <手机号> --username <名称>`（**无密码参数**，创建时直接授予 admin），验证脚本执行后该账号可仅凭手机号登录且权限为 admin

## 4. 用户管理与权限（`user-management`）

- [ ] 4.1 实现 `app/schemas/user.py` 与 `app/services/user_service.py` 的用户创建（手机号 11 位数字格式校验且全局唯一、用户名称非空、权限级别枚举 admin/normal、**无密码字段**），验证测试覆盖：创建成功返回手机号/用户名称/权限级别/启用状态、手机号重复被拒、手机号格式非法被拒、权限级别非法被拒、缺少必填字段被拒、创建后用户记录中无任何凭据字段
- [ ] 4.2 实现用户列表 `GET /api/v1/users`（返回手机号、用户名称、权限级别、启用状态、创建时间；支持按手机号或用户名称关键字过滤、按权限级别过滤；**不含任何凭据材料**），验证测试覆盖：列表不含密码字段、关键字过滤生效、权限级别过滤生效
- [ ] 4.3 实现用户修改 `PATCH /api/v1/users/{id}`（可改手机号、用户名称、权限级别；改手机号时重新校验全局唯一性；**不提供重置密码一类的操作**），验证测试覆盖：修改生效且更新审计字段、改成已被占用的手机号被拒、权限级别变更后下一次请求即按新权限判定
- [ ] 4.4 实现启用停用 `PATCH /api/v1/users/{id}/status`，验证测试覆盖：停用后该用户登录被拒且既有令牌下次使用即被拒、重新启用后可再次登录、**停用自己被拒并说明不能停用当前登录账号**
- [ ] 4.5 实现用户软删除 `DELETE /api/v1/users/{id}`（把 status 置为 1、更新 operator 与 updated_at），验证测试覆盖：删除后该用户不再出现在列表中且无法登录、该用户此前创建的货运订单与费用信息照常显示与编辑
- [ ] 4.6 实现 admin-only 依赖 `require_admin`（在 `get_current_user` 之上判 authority）并挂到全部用户管理路由上，验证测试覆盖：普通用户调用用户列表、创建、修改、启停用、删除全部返回 403 且数据不变

## 5. 选项表能力（`option-lists`）

- [ ] 5.1 实现 `app/repositories/option.py`：定义「分类字段标识 → 选项表」的映射（费用代码、描述、应付部门、应付分支机构、币种、应付税率、应付对象、应收对象、账单类型）与九类共用的查询助手，验证测试覆盖：九类选项各自独立、每个字段标识映射到正确的表
- [ ] 5.2 实现选项项的创建 `POST /api/v1/options/{kind}`（kind 仅接受九类固定值，非法的 kind 返回 404 或 422），验证测试覆盖：新增成功返回 code/name/is_active、同一选项表内 code 重复被拒、缺少 code 被拒、名称省略时以 code 呈现
- [ ] 5.3 实现选项项的编辑 `PATCH /api/v1/options/{kind}/{id}`（可改名称与排序，**code 不可修改**），验证测试覆盖：改名生效且更新审计字段、改排序生效、尝试改 code 被拒并说明代码不可更改
- [ ] 5.4 实现软删除 `DELETE /api/v1/options/{kind}/{id}`（把 status 置为 1、更新 operator 与 updated_at）与删除前的引用计数查询，验证测试覆盖：删除后不再出现在候选列表、status 与审计字段被更新、该选项仍可在管理列表中查询到、删除前返回引用它的费用信息条数
- [ ] 5.5 实现启用停用 `PATCH /api/v1/options/{kind}/{id}/status`，验证测试覆盖：停用后不出现在候选列表、重新启用后重新出现、停用项本身仍可被费用信息保存
- [ ] 5.6 实现管理列表 `GET /api/v1/options/{kind}`（可按参数包含已停用与已软删除的项并标明状态）与候选列表 `GET /api/v1/options/{kind}/options`（仅启用未删除，支持关键字过滤），验证测试覆盖：管理列表能区分启用/停用/已删除三种状态、候选列表不含停用与已删除项、关键字过滤生效
- [ ] 5.7 实现一次取回九类候选的接口 `GET /api/v1/options/candidates`（返回九组候选及各字段标识，并标注哪些字段允许直接输入），验证测试覆盖：响应含九组候选、描述被标记为可自由输入、其余八组未标记、该路由不会被 `{kind}` 抢占
- [ ] 5.8 把 admin-only 依赖挂到选项的**写**路由上（新增、编辑、删除、启停用），而候选列表与管理列表按各自权限开放，验证测试覆盖：普通用户调用选项写接口返回 403 且数据不变、普通用户可读候选列表
- [ ] 5.9 实现 CLI 种子脚本 `python -m app.cli seed-options`，预置费用代码 `DHLF`/`OCUC`/`OINSUR`、部门 `FIS`/`FES`/`FIA`/`FEA`、分支机构 `SHL`、币种 `USD`/`CNY`/`EUR`/`HKD`、账单类型 `FIN`/`CUR`/`NON-pending`，验证脚本执行后对应候选列表中能查到这些项且其余选项表为空

## 6. 货运订单状态机（`shipment-management`）

- [ ] 6.1 在 `app/services/shipment_service.py` 实现流转矩阵与校验（draft→confirmed、draft→cancelled、confirmed→completed、confirmed→cancelled；其余一律 409），验证测试覆盖：四条合法流转各自成功、completed/cancelled 为终态拒绝再流转、非法流转返回 409
- [ ] 6.2 实现三个动作端点 `POST /api/v1/shipments/{id}/confirm|complete|cancel`，流转在单个事务内以 `SELECT ... FOR UPDATE` 锁定订单行后执行并更新 operator 与 updated_at，验证测试覆盖：流转成功且 lifecycle 落库、并发对同一订单的冲突流转只有一个生效
- [ ] 6.3 验证状态流转不产生任何审批实体或审批人字段（数据库中无相关表/列，接口响应中无审批字段），且**终态订单下的费用信息仍可编辑**

## 7. 货运订单能力（`shipment-management`）

- [ ] 7.1 实现 `app/services/shipment_service.py` 的货运订单号唯一性校验（非空、去除首尾空格、全局唯一且比较不区分大小写），验证测试覆盖：正常值通过、与已有订单重复被拒、`SH-001` 与 `sh-001` 判定为重复、带首尾空格的同值判定为重复、空值与纯空白值被拒
- [ ] 7.2 实现 `app/schemas/shipment.py` 与 `POST /api/v1/shipments`（shipment_num 必填、默认不要求任何金额或明细、记录 operator/created_at/updated_at），验证测试覆盖：创建成功返回标识与货运订单号、缺少 shipment_num 返回 422、不附带明细也能创建成功
- [ ] 7.3 实现货运订单编辑 `PATCH /api/v1/shipments/{id}`（可改 shipment_num，改时重新校验全局唯一性），验证测试覆盖：修改生效且更新审计字段、改成已被占用的值被拒并说明原因、编辑不影响其下的费用信息、编辑不存在的订单返回 404
- [ ] 7.4 实现软删除 `DELETE /api/v1/shipments/{id}`（把 status 置为 1、更新 operator 与 updated_at，不做物理删除），验证测试覆盖：删除后详情返回 404、status 变为 1 且 operator 与 updated_at 被更新、数据库中订单与其费用信息记录仍存在
- [ ] 7.5 实现 `app/repositories/shipment.py` 查询助手（统一注入 `status = 0` 过滤、集中定义筛选条件、订单合计的单订单聚合查询——对某订单的费用信息按币种做一次 `GROUP BY`），验证测试覆盖：合计按币种分组正确（USD 1200 与 EUR 300 分别成组、不合并）、无明细订单合计为空、已删除的费用信息不计入合计
- [ ] 7.6 实现 `GET /api/v1/shipments`（分页 page/page_size、默认按 created_at 倒序、响应 `{items,total,page,page_size}`、每项仅附带费用信息条数，**不返回任何金额**），验证测试覆盖：默认分页返回与总数正确、响应中不含应付/应收金额、page_size 上限生效
- [ ] 7.7 实现货运订单列表的筛选（shipment_num 关键字模糊匹配、应付侧币种与合计金额区间、应收侧币种与合计金额区间），验证测试覆盖：关键字模糊匹配生效、应付侧区间按该币种下的合计筛选（用 `EXISTS ... GROUP BY ... HAVING` 实现且不产生行数膨胀）、未指定币种时不应用金额区间、组合筛选无结果时返回空列表与 total=0
- [ ] 7.8 实现货运订单详情 `GET /api/v1/shipments/{id}`（返回标识、shipment_num、审计信息与其下全部未删除费用信息），验证测试覆盖：详情包含全部费用信息、不存在或已删除的订单返回 404

## 8. 费用信息能力（`charge-info`）

- [ ] 8.1 实现 `app/schemas/charge_info.py`（应付侧与应收侧字段均 Required、金额用 `condecimal(max_digits=14, decimal_places=2)`、`description` 非空文本、九个分类字段为内容字符串、`local_*` 字段可空且忽略客户端传值），验证 schema 单元测试覆盖：缺任一应付侧字段被拒、缺任一应收侧字段被拒、缺账单类型被拒、三位小数金额被拒、负数金额被拒
- [ ] 8.2 实现 `POST /api/v1/shipments/{id}/charge-infos`（校验所属货运订单存在且未软删除、把父订单的 shipment_num 写入 job_num、对八个封闭集合字段做取值校验、写入审计字段，全部在同一事务内），验证测试覆盖：创建成功并返回全部字段、任务码自动带出为父订单号、客户端传入不同 job_num 被忽略、所属订单不存在返回 404
- [ ] 8.3 实现分类字段的三态校验（取值不存在 → 拒绝并说明无效；取值已停用 → 新建拒绝、编辑时保留原值接受、编辑改为该值拒绝；取值已软删除 → 拒绝并说明已被删除），验证测试覆盖上述每一种情形
- [ ] 8.4 实现描述的可直接输入（description 不参与选项校验），验证测试覆盖：输入不在描述选项表中的描述被接受并保存、描述为空被拒
- [ ] 8.5 实现 `PATCH /api/v1/charge-infos/{id}`（可改九个分类字段与两侧金额；job_num 不可改；重新执行取值校验与金额约束校验；更新审计字段），验证测试覆盖：修改生效、修改币种后在新币种下参与合计、job_num 保持不变、改成非法取值被拒、编辑不存在的记录返回 404
- [ ] 8.6 实现软删除 `DELETE /api/v1/charge-infos/{id}`（把 status 置为 1、更新 operator 与 updated_at），验证测试覆盖：删除后不出现在货运订单详情中、所属订单的应付与应收合计相应减少、status 与审计字段被更新
- [ ] 8.7 实现 `app/repositories/charge_info.py` 查询助手（统一注入 `status = 0` 过滤、所属货运订单未删除的 JOIN 条件），验证测试覆盖：已删除记录与已删除货运订单下的记录不出现在任何查询中

## 9. 金额口径（`amount-rules`）

- [ ] 9.1 实现应付与应收两侧的币种校验（各自取自币种选项表中启用且未删除的项、允许两侧币种不同），验证测试覆盖：两侧币种不同被接受、两侧相同被接受、币种不存在或已停用被拒
- [ ] 9.2 实现本地金额字段的处理（`local_cost_amt` 与 `local_sell_amt` 恒为 null，客户端传入的值被忽略且不保存），验证测试覆盖：读取时两字段均为 null、创建时传入被忽略后落库仍为 null
- [ ] 9.3 实现货运订单列表的金额区间筛选口径（必须指定币种；未指定币种时不应用区间条件），验证测试覆盖：指定币种时按该币种下的合计筛选生效、未指定币种时区间被忽略而非报错、币种与区间不匹配时无结果

## 10. 前端基础设施与登录（`auth`）

- [ ] 10.1 配置前端路由与守卫（未登录访问业务路由跳登录页、已登录访问登录页跳货运订单列表、**普通用户访问用户管理页与选项维护页时被路由拦截**），验证 Vitest 测试覆盖三种跳转与拦截行为
- [ ] 10.2 实现 `src/api/client.ts` Axios 封装（自动注入 Authorization 头、**401 跳登录、403 提示无权限且不跳登录**、统一错误提示）与 `src/stores/auth.ts`（登录、登出、持久化令牌、当前用户含 authority），验证 Vitest 测试覆盖：请求自动带令牌、401 触发跳转、403 只提示不跳转
- [ ] 10.3 实现登录页 `src/views/LoginView.vue`（**只有手机号一个输入框**，无密码框；提交即登录），验证 Vitest 测试覆盖：只填手机号即可提交并跳转货运订单列表、页面不存在密码输入框、手机号未开通时显示服务端错误信息
- [ ] 10.4 由后端 OpenAPI 生成前端 TypeScript 类型至 `src/types/`（`openapi-typescript`），验证 `npm run generate:types` 执行成功且生成文件进入版本控制

## 11. 前端可选值接入

- [ ] 11.1 实现 `src/stores/options.ts`（应用启动时拉取一次 `/api/v1/options/candidates` 并缓存，提供按字段标识取候选与「是否允许自由输入」的查询），验证 Vitest 测试覆盖：首次访问触发请求、再次访问命中缓存不再请求
- [ ] 11.2 实现分类字段下拉组件 `src/components/OptionSelect.vue`（按字段标识渲染选项、可搜索、是否允许新建由接口下发的标记驱动），验证 Vitest 测试覆盖：八个封闭集合字段不可输入表外值、描述字段可输入表外值并回传新值

## 12. 前端货运订单列表与详情（`shipment-management`）

- [ ] 12.1 实现货运订单筛选栏组件 `src/components/ShipmentFilterBar.vue`（货运订单号关键字、业务状态、应付侧币种+区间、应收侧币种+区间，含重置；**字段标签中英双语**），验证 Vitest 测试覆盖：筛选参数正确拼装为查询串、重置后参数清空、未选币种时不发出金额区间参数、筛选标签同时显示中文与上游英文名
- [ ] 12.2 实现按币种分组合计的展示组件 `src/components/CurrencyTotalsCell.vue`（渲染 `[{currency, amount}]` 为「USD 1,200；EUR 300」，空数组时显示占位；**仅用于订单详情页的合计带，列表页不使用**），验证 Vitest 测试覆盖：多币种分号分隔渲染、单个币种正确渲染、空数组渲染占位
- [ ] 12.3 实现货运订单列表页 `src/views/ShipmentListView.vue`（表格列：货运订单号、费用信息条数、业务状态、操作人、创建时间、更新时间、操作；**不展示应付/应收合计**；**所有字段标签中英双语，英文取上游字段名**；分页；加载态与空态），验证 Vitest 测试覆盖：接口返回后正确渲染行与总数、页面不渲染任何金额列、空结果显示空态、表头同时显示中文与上游英文名
- [ ] 12.4 实现货运订单新建/编辑表单页 `src/views/ShipmentFormView.vue`（仅货运订单号一个字段，失焦与提交时做唯一性预检，比较语义与后端一致：不区分大小写、忽略首尾空格），验证 Vitest 测试覆盖：新建提交成功、编辑回填数据、重复的货运订单号阻止提交并给出与后端同一套措辞的提示
- [ ] 12.5 实现订单详情页 `src/views/ShipmentDetailView.vue` 的**状态流转按钮**（草稿显示「确认」「取消」、已确认显示「完成」「取消」、已完成与已取消不显示流转按钮），验证 Vitest 测试覆盖：各业务状态下按钮的可用性正确、点击后调用对应端点并刷新列表与状态标签

## 13. 前端费用信息录入（`charge-info`）

- [ ] 13.1 实现金额格式化工具 `src/utils/money.ts`（字符串绑定、两位小数格式化、前端两位小数校验），验证 Vitest 测试覆盖：`"100.1"` 格式化为 `"100.10"`、三位小数输入被拒、格式化不产生浮点误差
- [ ] 13.2 实现费用信息表格组件 `src/components/ChargeInfoTable.vue`（描述、费用代码、任务码、应付部门、应付分支机构、应付币种、应付金额、应付税率、应付对象、应收币种、应收金额、应收对象、账单类型、操作；**所有字段标签中英双语，英文取上游字段名 `Description`/`Charge Code`/`Job No.`/`Department`/`Branch`/`Cost Currency`/`OS Cost Amt`/`Cost Tax ID`/`Creditor`/`Sell Currency`/`OS Sell Amt`/`Debtor`/`Inv. Type`**），验证 Vitest 测试覆盖：各列正确渲染、任务码只读展示、表头同时显示中文与上游英文名
- [ ] 13.3 实现费用信息弹窗 `src/components/ChargeInfoDialog.vue`（字段按三组分组：费用组 费用代码/描述/应付部门/应付分支机构；应付组 应付币种/应付金额/应付税率/应付对象；应收组 应收币种/应收金额/应收对象/账单类型；任务码在顶部只读展示并由父订单带出；八个封闭集合字段用 OptionSelect、描述用可新建的 OptionSelect；**所有字段标签与分组标题中英双语**），验证 Vitest 测试覆盖：新增提交成功、编辑回填数据、任务码只读且不可编辑、描述可直接输入表外的新值、其余分类字段不可输入表外值、字段标签同时显示中文与上游英文名
- [ ] 13.4 实现货运订单详情页 `src/views/ShipmentDetailView.vue`（货运订单信息 + **按币种分组的应付/应收合计带** + 费用信息表格 + 就地新增/编辑/删除），验证 Vitest 测试覆盖：新增后表格与条数立即刷新、合计带随明细增删同步刷新、删除需二次确认、详情加载失败时显示 404 提示

## 14. 前端用户管理与选项维护页（`user-management` + `option-lists`）

- [ ] 14.1 实现用户管理页 `src/views/UserManagementView.vue`（用户表格 + 新增/编辑弹窗 + 权限级别用 `el-radio-group` 二选一 + 启用停用开关 + 删除二次确认，**无重置密码入口**），验证 Vitest 测试覆盖：新增用户成功、编辑生效、停用后从列表中标为停用、删除有二次确认
- [ ] 14.2 实现「不能停用自己」的前端表现（当前登录用户对应的停用开关禁用并给出说明），验证 Vitest 测试覆盖：停用开关对当前登录用户不可用
- [ ] 14.3 实现选项维护页 `src/views/OptionListView.vue`（顶部九类选项的切换器，切换时加载对应数据；表格 + 新增/编辑弹窗 + 启用停用开关 + 删除二次确认），验证 Vitest 测试覆盖：切换类型时加载对应 kind 的数据、新增项成功入表、编辑生效、停用后该项从候选列表中消失、删除有二次确认
- [ ] 14.4 实现「code 创建后不可修改」的前端表现（编辑弹窗中 code 置灰只读）与「删除前展示引用数量」（二次确认弹窗中显示该选项被多少条费用信息引用），验证 Vitest 测试覆盖：编辑弹窗中 code 不可编辑、删除弹窗展示引用数量
- [ ] 14.5 按当前用户权限隐藏导航入口与页面（普通用户看不到「用户管理」「选项维护」），验证 Vitest 测试覆盖：普通用户的导航中无 admin 入口
- [ ] 14.6 在货运订单列表页导航中加入用户管理与选项维护入口，验证手动点击可跳转

## 15. 契约一致性与整体验证

- [ ] 15.1 增加 CI 步骤校验前端生成的类型与后端 OpenAPI 无差异（重新生成后 `git diff --exit-code`），验证故意改动一个接口字段后该步骤失败
- [ ] 15.2 端到端冒烟验证（主链路）：以管理员登录 → 录入货运订单号创建货运订单（重复号应被拒绝、大小写变体也应被拒绝）→ 为其添加一条费用信息（应付 USD 1200、应收 CNY 8600，各分类字段从下拉选择、描述直接输入一个表外新值）→ 确认任务码自动等于货运订单号 → 确认分类字段打错值（如 `FIS5`）被后端拒绝 → 在详情页核对按币种分组的合计为 USD 1200 与 CNY 8600 → 软删除该记录后合计归零 → 软删除货运订单后记录不再可见
- [ ] 15.3 端到端冒烟验证（权限）：用普通用户账号登录 → 确认导航中无「用户管理」「选项维护」入口、直接访问这两个页面被拦截 → 直接调用用户管理接口返回 403、调用选项写接口返回 403 → 改用管理员登录 → 成功维护选项与用户 → 把某普通用户改为 admin 后该用户下一次请求即获得管理员权限 → 管理员停用自己被拒
- [ ] 15.4 端到端冒烟验证（选项维护）：在选项维护页新增一个部门值 → 回到费用信息录入确认该值出现在下拉且可保存 → 停用该值后确认它从下拉消失 → 确认引用了该值的已有记录仍能正常编辑保存 → 删除该值前确认弹窗显示引用数量 → 删除后确认引用它的记录再保存被拒绝
- [ ] 15.5 运行全量校验：后端 `pytest` 与前端 `npm test` 全部通过、`npm run build` 成功产出 `dist/`，验证 CI 与本地结果一致
- [ ] 15.6 更新根 `README.md` 补充完整接口清单、权限矩阵、九类选项表说明与初始数据/管理员初始化命令，验证 README 中每条命令均可在干净环境下执行成功

## Workflow follow-up

- 归档本变更：在项目评审要求满足后执行 `/opsx:archive`，将六份 delta spec 同步进 `openspec/specs/`。
- 归档后验证：确认 `openspec/specs/` 下 `auth`、`user-management`、`shipment-management`、`charge-info`、`amount-rules`、`option-lists` 六个主 spec 已生成且内容完整。
- 上线前必须补齐四组选项的初始内容：费用代码、应付税率、应付对象、应收对象——这些选项表为空时对应字段无法录入任何值（描述例外，可直接输入）。
- 上线前确认两件事：其一，业务方是否需要「已结算金额 / 支付状态」来跟踪款项是否到账（本期字段清单未包含）；其二，是否需要禁止停用「最后一个管理员」（当前只禁止停用自己）。
- 首个真实货运订单录入后，核对货运订单号、两侧金额、币种与各分类取值与线下账目一致，再向其他同事开放使用。
