# gnucash-web 财务管理系统 —— 面试准备完整版

> 技术栈：Vue3 + Element Plus（前端）+ Spring Boot 3.1.3 + MyBatis + MySQL（后端）  
> 项目性质：复式记账财务管理系统，支持多账簿隔离、科目树管理、凭证录入、财务报表

---

## 一、项目全景速览

### 1.1 一句话定义
> 基于 **Spring Boot + Vue3** 的复式记账财务管理系统，实现了多账簿隔离、会计科目层级管理、凭证录入（借贷平衡校验）、财务报表（试算平衡表/资产负债表/利润表）等核心功能。

### 1.2 技术栈一览

| 层级 | 技术 | 版本 |
|------|------|------|
| 后端框架 | Spring Boot | 3.1.3 |
| ORM | MyBatis | Spring Boot Starter 3.0.2 |
| 数据库 | MySQL | — |
| 连接池 | Druid（阿里） | 1.2.20 |
| 前端框架 | Vue3 + Element Plus | — |
| 构建工具 | Maven | — |
| Java 版本 | JDK 17 | — |

### 1.3 项目架构图

```
┌──────────────────────────────────────────────────┐
│                    前端 (Vue3)                     │
│  科目树 / 凭证录入 / 报表 / 客户供应商管理           │
│  每次请求 Header 自动注入 X-Book-Id                │
└──────────────────────┬───────────────────────────┘
                       │ HTTP RESTful API
                       ▼
┌──────────────────────────────────────────────────┐
│               Spring Boot 后端                     │
│                                                    │
│  ┌──────────┐  ┌──────────┐  ┌───────────────┐  │
│  │ BookFilter│→ │BookContext│  │ 多账簿隔离      │  │
│  │ (拦截器)  │  │(ThreadLocal)│ │ (通过Header传ID) │  │
│  └──────────┘  └──────────┘  └───────────────┘  │
│                                                    │
│  Controller → Service → Mapper(MyBatis) → MySQL    │
│                                                    │
│  核心模块：                                         │
│  - AccountController (科目 CRUD + 余额查询)         │
│  - TransactionController (凭证录入 + 借贷校验)       │
│  - ReportController (三大报表)                      │
│  - BookController (账套管理)                        │
│  - Customer/Supplier/Purchase/Sales/TaxController   │
└──────────────────────┬───────────────────────────┘
                       │ MyBatis / JDBC
                       ▼
┌──────────────────────────────────────────────────┐
│                   MySQL 数据库                     │
│  多账套逻辑隔离，每个账套独立的业务数据               │
└──────────────────────────────────────────────────┘
```

---

## ⭐ 二、项目介绍话术（三个版本，逐字背诵）

### 2.1 3分钟标准版

> 这个项目是基于 Spring Boot 和 Vue3 开发的一套复式记账财务管理系统，对标开源软件 Gnucash 的 Web 版本。
>
> 项目最大的技术亮点是**多账簿隔离设计**。Gnucash 允许用户同时管理多个独立账套（比如个人账、公司账），每个账套的数据完全隔离。我设计了一套基于 **ThreadLocal + Filter 拦截器** 的方案：前端每次请求时在 HTTP Header 中带上当前账套 ID（X-Book-Id），后端通过 Filter 拦截请求，把 ID 存入 ThreadLocal 上下文中，后续 Service 层和 Mapper 层自动从上下文获取当前账套 ID，SQL 查询自动带上账套过滤条件。请求结束后清理 ThreadLocal 防止内存泄漏。这个设计让业务代码不需要关心"当前是哪个账套"，实现了透明的多租户数据隔离。
>
> 第二个核心功能是**复式记账的凭证录入**。会计学的基本原理是"有借必有贷，借贷必相等"——每一笔交易至少涉及两个科目，一个记借方（增加），一个记贷方（减少），借方总额必须等于贷方总额。我在 TransactionService 中实现了这个校验逻辑：遍历每个 Split（分录），分别累加借方金额和贷方金额，用 BigDecimal 做精确比较，如果不相等则抛出 InvalidAccountingException 回滚事务。校验通过后，用 @Transactional 注解保证交易头和分项同时写入数据库。
>
> 第三个亮点是**会计科目的树形层级模型**。科目表是一个自引用的树形结构——每个科目有一个 parent_code 指向父科目。我在 Account 类中设计了 parent（父科目引用）和 children（子科目列表）两个字段，前端用 Element Plus 的 el-table 懒加载展示——首次加载根节点，点击展开时再发请求加载子节点。科目余额是实时计算的——通过 SQL 聚合所有的 Split 记录，按借贷方向汇总得到实时余额。
>
> 另外还实现了三张财务报表：**试算平衡表**列出所有非零余额的科目，验证借贷平衡；**利润表**按收入和费用类科目汇总，计算净损益；**资产负债表**按资产、负债、权益分类汇总。报表数据都是实时从数据库查询计算的。
>
> 整个项目采用标准的 **Controller → Service → Mapper** 分层架构，RESTful API 设计，统一返回 JSON 格式。虽然我的主力语言是 Python，但这个项目让我深入理解了 Spring Boot 的开发模式、MyBatis 的 SQL 映射、以及前后端协作的全流程。

### 2.2 1分钟极速版

> 我用 Spring Boot + Vue3 做了一个复式记账财务系统。核心亮点有三个：第一是多账簿隔离，用 Filter 拦截 HTTP Header 中的账套 ID，存到 ThreadLocal 中，实现透明的多租户数据隔离；第二是凭证录入的借贷平衡校验，用 BigDecimal 精确计算借方和贷方总额，不相等则回滚事务；第三是会计科目的树形层级模型，前端懒加载展示，余额通过 SQL 实时聚合计算。还实现了试算平衡表、资产负债表、利润表三张报表。整个项目是标准的 Controller-Service-Mapper 三层架构 + RESTful API。

### 2.3 STAR 法则完整版

**Situation（背景）：**
> Gnucash 是一款开源的个人/小企业财务软件，但它是桌面客户端版本，不方便多人使用和远程访问。需要一个 **Web 版本**，让用户通过浏览器管理账簿、录入凭证、查看财务报表。

**Task（任务）：**
> 我负责后端整体架构设计和核心模块开发，包括：多账簿隔离方案、科目层级管理、复式记账凭证录入（借贷平衡校验）、三大财务报表生成、以及客户/供应商/采购/销售/税务等辅助模块。

**Action（行动）：**
> 1. **架构设计**：采用 Spring Boot 3.x + MyBatis + MySQL，Controller-Service-Mapper 三层架构，RESTful API 设计
> 2. **多账簿隔离**：设计 Filter + ThreadLocal 方案，前端在请求 Header 中传递 X-Book-Id，后端自动拦截存入上下文，SQL 自动按账套过滤
> 3. **复式记账**：在 TransactionService 中实现借+贷校验逻辑，BigDecimal 精确计算，不相等回滚事务，使用 UUID 生成主键
> 4. **科目树**：自引用表结构（parent_code 外键），支持懒加载子节点，余额实时 SQL 聚合
> 5. **财务报表**：试算平衡表（所有非零余额科目）、资产负债表（资产=负债+权益）、利润表（收入-费用=净损益）
> 6. **其他模块**：客户/供应商管理、采购/销售订单、税务处理、银行对账等

**Result（成果）：**
> 实现了完整的复式记账 Web 端功能，支持多账簿隔离、科目层级展示、凭证录入借贷校验、三大报表实时生成。后端代码结构清晰，Controller/Service/Mapper 职责分明，可扩展性强。

---

## 三、技术亮点深度解析

---

### ⭐ 3.1 多账簿隔离设计（最核心的技术亮点）

#### 3.1.1 为什么需要？

> Gnucash 允许一个用户管理多个独立账套（比如"个人日常账"和"公司经营账"），两个账套的数据完全独立。如何让同一套代码同时服务多个账套，且数据不混淆？

#### 3.1.2 我的方案：Filter + ThreadLocal

**步骤 1：前端在请求 Header 中传递账套 ID**

```
每次 API 请求自动在 Header 中注入 X-Book-Id: {当前账套的ID}
```

**步骤 2：BookFilter 拦截器从 Header 提取并存到 ThreadLocal**

```java
@Component
@Order(1)
public class BookFilter implements Filter {
    @Override
    public void doFilter(ServletRequest request, ServletResponse response, FilterChain chain)
            throws IOException, ServletException {
        HttpServletRequest req = (HttpServletRequest) request;
        // 从 Header 获取前端传来的账套ID
        String bookId = req.getHeader("X-Book-Id");
        try {
            if (bookId != null && !bookId.trim().isEmpty()) {
                BookContext.set(bookId);  // 存入 ThreadLocal
            }
            chain.doFilter(request, response);  // 放行
        } finally {
            BookContext.clear();  // 请求结束清理，防止内存泄漏！
        }
    }
}
```

**步骤 3：BookContext 用 ThreadLocal 存储当前请求的账套 ID**

```java
public class BookContext {
    private static final ThreadLocal<String> currentBookId = new ThreadLocal<>();

    public static void set(String bookId) { currentBookId.set(bookId); }
    public static String get() { return currentBookId.get(); }
    public static void clear() { currentBookId.remove(); }
}
```

**步骤 4：Service 层自动获取当前账套 ID**

```java
private String getCurrentBookId() {
    String bookId = BookContext.get();
    if (bookId == null) throw new RuntimeException("操作失败：未选择账套！");
    return bookId;
}
```

**步骤 5：SQL 查询自动带上账套过滤条件**

```xml
<!-- MyBatis Mapper XML 中 -->
<select id="findAll" resultMap="TransactionMap">
    SELECT * FROM transactions WHERE book_id = #{bookId}
</select>
```

#### 3.1.3 为什么用 ThreadLocal？

| 方案 | 优点 | 缺点 |
|------|------|------|
| **ThreadLocal**（我的方案） | 线程安全、对业务代码透明、不侵入方法签名 | 需手动清理防内存泄漏 |
| 方法传参（每个方法加 bookId） | 显式、无需清理 | 侵入性强，所有方法都要改签名 |
| Session 存储 | Web 层方便 | 耦合 Servlet API，非 HTTP 场景用不了 |
| Spring Security Context | 适合认证用户场景 | 太重，这里只需要一个 ID |

> **关键点**：`finally` 块中的 `BookContext.clear()` 非常重要。ThreadLocal 如果只存不清，线程复用时（Tomcat 线程池）上次请求的数据会污染下次请求，导致数据泄露。而且 ThreadLocal 的 key 是弱引用，但 value 是强引用，不清理会导致内存泄漏。

---

### ⭐ 3.2 复式记账与借贷平衡校验

#### 3.2.1 什么是复式记账？

> 会计学的基本原则：**"有借必有贷，借贷必相等"**。
>
> 每一笔经济业务，至少涉及两个会计科目。一个科目记"借方"（Debit），另一个科目记"贷方"（Credit）。所有借方金额的合计，必须等于所有贷方金额的合计。
>
> 例如：公司用银行存款 10000 元购买设备。
> - 借：固定资产（设备） 10000 元（资产增加）
> - 贷：银行存款 10000 元（资产减少）
>
> 借方合计 = 贷方合计 = 10000，平衡。

#### 3.2.2 数据模型

```
Transaction（交易/凭证）
  ├── id (UUID)
  ├── date (日期)
  ├── description (摘要)
  ├── bookId (所属账套)
  └── splits: List<Splits> (分录列表，一对多)

Splits（分录）
  ├── id
  ├── transactionId (外键 → Transaction)
  ├── accountId (外键 → Account，哪个科目)
  ├── amount: BigDecimal (金额，精确计算)
  ├── direction: Direction枚举 (DEBIT=借方 或 CREDIT=贷方)
  └── description (分录说明)
```

#### 3.2.3 借贷平衡校验代码逻辑

```java
@Transactional  // 开启事务
public void saveTransaction(Transaction transaction) {
    String bookId = getCurrentBookId();
    transaction.setBookId(bookId);

    // 1. 遍历 Splits，分别累加借方和贷方金额
    BigDecimal totalDebit = BigDecimal.ZERO;
    BigDecimal totalCredit = BigDecimal.ZERO;

    for (Splits split : transaction.getSplits()) {
        if (split.getDirection() == Direction.DEBIT) {
            totalDebit = totalDebit.add(split.getAmount());
        } else {
            totalCredit = totalCredit.add(split.getAmount());
        }
    }

    // 2. 比较借贷是否相等
    if (totalDebit.compareTo(totalCredit) != 0) {
        throw new InvalidAccountingException(
            "试算不平衡！借方总额: " + totalDebit + ", 贷方总额: " + totalCredit
        );
    }

    // 3. 校验通过，生成 UUID，保存交易头
    transaction.setId(UUID.randomUUID().toString());
    transactionMapper.saveTransaction(transaction);

    // 4. 给每个分项设置交易ID，批量保存分项
    for (Splits split : transaction.getSplits()) {
        split.setId(UUID.randomUUID().toString());
        split.setTransactionId(transaction.getId());
    }
    transactionMapper.batchSaveSplits(transaction.getSplits());
}
```

#### 3.2.4 关键技术点

**为什么金额用 BigDecimal 而不是 double？**
> double 是浮点数，存在精度问题。例如 0.1 + 0.2 在 double 下等于 0.30000000000000004，在金额计算中会导致一分钱的误差——这在财务系统中是致命的。BigDecimal 是精确的十进制运算，`compareTo` 方法可以精确比较。

**为什么用 UUID 而不是自增 ID？**
> 分布式场景下自增 ID 会冲突（多个实例同时插入），UUID 全局唯一，生成不依赖数据库，适合未来扩展。

**为什么用 @Transactional？**
> 保证保存交易头 + 批量保存分项的原子性——要么全成功，要么全回滚。如果中途抛异常（如借贷不相等），数据库不会有任何脏数据。

**Direction 枚举的妙用**
```java
public enum Direction {
    DEBIT("借方"),
    CREDIT("贷方");

    private final String label;
    Direction(String label) { this.label = label; }
    public String getLabel() { return label; }

    // 静态方法：数据库存的"借方"/"贷方"字符串 → Java 枚举对象
    public static Direction fromLabel(String label) {
        for (Direction d : Direction.values()) {
            if (d.getLabel().equals(label)) return d;
        }
        return null;
    }
}
```
> 用枚举代替字符串常量的好处：类型安全（编译期检查）、可读性强、有 fromLabel 方法方便和数据库交互。

---

### ⭐ 3.3 会计科目树形模型

#### 3.3.1 数据表设计

```sql
CREATE TABLE accounts (
    code VARCHAR(20) PRIMARY KEY,    -- 科目代码，如"1001"(库存现金)、"1002"(银行存款)
    name VARCHAR(50),                -- 科目名称
    type VARCHAR(20),                -- 类型：ASSET(资产)/LIABILITY(负债)/EQUITY(权益)/INCOME(收入)/EXPENSE(费用)
    parent_code VARCHAR(20),         -- 父科目代码，自引用外键
    book_id VARCHAR(36)              -- 所属账套
);
```

#### 3.3.2 Java 领域模型

```java
public class Account {
    private String code;
    private String name;
    private String type;
    private Account parent;           // 自关联：多对一（找爸爸）
    private List<Account> children;   // 自关联：一对多（找孩子）
    private String parent_code;       // 用于 MyBatis 映射
    private BigDecimal balance;       // 实时计算的余额
    private String bookId;
}
```

#### 3.3.3 树形结构如何加载？

```
前端请求：GET /accounts                     → 返回一级科目（parent_code IS NULL）
用户点"1000 资产类"前的展开箭头：
  前端请求：GET /accounts?parent=1000       → 返回"1000"下的二级科目
用户再点"1001 流动资产"前的展开箭头：
  前端请求：GET /accounts?parent=1001       → 返回三级科目
```

> 这就是**懒加载**——不一次性加载全部科目（可能几千个），而是每次只加载用户当前要看的层级。前端 Element Plus 的 el-table 组件原生支持 tree-props 懒加载。

#### 3.3.4 余额如何计算？

```
一个科目的余额 = 该科目所有 Split 的 (借方总额 - 贷方总额) 的绝对值

资产类科目：借方增加，贷方减少 → 余额 = 借方 - 贷方（借方余额）
负债/权益类：贷方增加，借方减少 → 余额 = 贷方 - 借方（贷方余额）

SQL 实时聚合实现：
SELECT account_id,
       SUM(CASE WHEN direction='借方' THEN amount ELSE 0 END) AS total_debit,
       SUM(CASE WHEN direction='贷方' THEN amount ELSE 0 END) AS total_credit
FROM splits
WHERE book_id = #{bookId}
GROUP BY account_id
```

---

### ⭐ 3.4 三大财务报表

| 报表 | 英文 | 公式 | 作用 |
|------|------|------|------|
| 试算平衡表 | Trial Balance | Σ借方 = Σ贷方 | 验证所有科目记账正确性 |
| 资产负债表 | Balance Sheet | 资产 = 负债 + 权益 | 反映某个时间点的财务状况 |
| 利润表 | Income Statement | 收入 - 费用 = 净利润 | 反映某段时间的经营成果 |

**实现方式**：ReportService 中通过 SQL 聚合查询各科目的余额，按报表格式分类汇总。

```java
// 试算平衡表：列出所有非零余额的科目
@GetMapping("/trial-balance")
public List<Map<String, Object>> getTrialBalance() {
    return reportService.getTrialBalance();
}

// 资产负债表：资产 = 负债 + 权益
@GetMapping("/balance-sheet")
public Map<String, Object> getBalanceSheet() {
    return reportService.getBalanceSheet();
}

// 利润表：支持日期范围参数
@GetMapping("/income-statement")
public Map<String, Object> getIncomeStatement(
    @RequestParam @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate startDate,
    @RequestParam @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate endDate) {
    return reportService.getIncomeStatement(startDate, endDate);
}
```

---

## ⭐ 四、Java / Spring Boot 面试高频问答

### 4.1 Spring Boot 基础

**Q: @SpringBootApplication 做了什么？**
> 它是三个注解的合体：
> 1. `@Configuration`：标记该类为配置类
> 2. `@EnableAutoConfiguration`：自动配置，根据 classpath 中的 jar 自动配置 Spring（比如检测到 mybatis-spring-boot-starter 就自动配置 MyBatis）
> 3. `@ComponentScan`：扫描当前包及子包中的 @Component、@Service、@Repository、@Controller 等注解

**Q: @RestController 和 @Controller 有什么区别？**
> `@RestController` = `@Controller` + `@ResponseBody`。每个方法的返回值自动序列化为 JSON 写入 Response Body，不需要在每个方法上单独加 @ResponseBody。适用于 RESTful API。

**Q: @Autowired 是怎么工作的？**
> 按类型自动注入。Spring 容器启动时会扫描所有带 @Service/@Component/@Repository 的类，创建实例（Bean）。当看到 @Autowired 时，自动把这个类型的 Bean 注入进来。如果同类型有多个 Bean，则按名称匹配。

**Q: @Transactional 的原理？**
> Spring 通过 AOP（面向切面编程）实现事务管理。方法执行前开启事务，方法正常执行完则提交事务，方法抛异常则回滚事务。底层基于数据库连接的事务机制。

**Q: Spring Boot 3.x 和 2.x 有什么区别？**
> 最大的变化是 `javax.*` → `jakarta.*`。因为 Java EE 捐给了 Eclipse 基金会，改名为 Jakarta EE。代码中所有 `javax.servlet` 要改成 `jakarta.servlet`。项目中的 BookFilter 用的就是 `jakarta.servlet.*`。

### 4.2 MyBatis 基础

**Q: MyBatis 是什么？和 JPA/Hibernate 有什么区别？**
> MyBatis 是半自动的 ORM 框架——你需要自己写 SQL，它帮你做结果映射。JPA/Hibernate 是全自动的——SQL 由框架生成。
>
> MyBatis 优势：SQL 完全可控，复杂查询优化空间大，适合对 SQL 性能有要求的场景。
> JPA 优势：简单 CRUD 不用写一行 SQL，开发快。

**Q: #{} 和 ${} 的区别？**
> `#{}`：预编译占位符，防止 SQL 注入。`SELECT * FROM t WHERE id = #{id}` → 变成 `SELECT * FROM t WHERE id = ?`
> `${}`：直接字符串拼接，**有 SQL 注入风险**。只在动态表名、动态列名等无法预编译的场景使用。

**Q: MyBatis 的一级缓存和二级缓存？**
> 一级缓存：SqlSession 级别，同一个 SqlSession 内重复查询会走缓存（默认开启）。
> 二级缓存：Mapper 级别，不同 SqlSession 共享（默认关闭，需手动配置）。

### 4.3 Java 基础（结合项目）

**Q: ThreadLocal 的底层原理？**
> ThreadLocal 在每个线程内部维护一个 ThreadLocalMap。这个 Map 的 key 是 ThreadLocal 对象的弱引用，value 是存的值。
>
> 项目中用 ThreadLocal 存储当前请求的账套 ID，实现同一线程内的数据共享（Filter → Service → Mapper 都可以拿到），而不同线程之间数据隔离（不同请求互不干扰）。

**Q: 为什么要 finally 里 clear()？**
> 两个原因：
> 1. **内存泄漏**：ThreadLocalMap 的 key 是弱引用（GC 时会回收），但 value 是强引用（不会被回收）。只存不清理 → 大量 value 堆积在内存中。
> 2. **数据污染**：Tomcat 用线程池复用线程。线程 A 处理完请求 1（bookId=账套A），没有清理 ThreadLocal，线程 A 再处理请求 2（bookId 应该是账套B），但它读到的还是账套A → 数据串了。

**Q: BigDecimal 为什么要用 compareTo 而不是 equals？**
> `equals` 比较值和精度（scale）。`new BigDecimal("1.00").equals(new BigDecimal("1.0"))` = false（精度不同）。
> `compareTo` 只比较数值。`new BigDecimal("1.00").compareTo(new BigDecimal("1.0"))` = 0（数值相等）。
> 金额比较应该用 compareTo。

**Q: 枚举（Enum）有什么优势？**
> 1. 类型安全：编译期就能发现类型错误（Direction d = "借方" 编译不通过）
> 2. 可读性强：Direction.DEBIT 比 "借方" 字符串更清晰
> 3. 有限的取值：保证值只能是 DEBIT 或 CREDIT，防止非法值
> 4. 自带方法：values() 遍历、valueOf() 转换

---

## 五、项目与数据开发的关联话术

> **面试时可主动说的迁移逻辑：**

> 这个项目虽然是偏后端开发，但它和数据开发有很强的关联性：
>
> **第一，多账簿隔离 = 数据分区。** 我用 ThreadLocal + Filter 实现的账套隔离，本质上就是数据仓库中的分区概念——不同账套的数据物理上存在同一张表里，但逻辑上通过 book_id 分区隔离。这和数仓中按日期分区（dt=）的思想完全一致。
>
> **第二，科目余额计算 = SQL 聚合查询。** 实时计算科目余额的过程，就是对 splits 表做 GROUP BY + SUM 的聚合操作，按借贷方向分别汇总后相减。这和数仓中计算用户日活、GMV 的 SQL 聚合逻辑完全一致。
>
> **第三，财务报表 = 数据应用层（ADS）。** 试算平衡表、资产负债表、利润表就是数据仓库中的 ADS 层（应用数据层）——从底层交易明细数据（DWD）按规则聚合生成面向特定业务场景的结果表。
>
> **第四，三层架构 = ETL 的模块化思想。** Controller 负责接收数据（Extract），Service 负责业务逻辑和转换（Transform），Mapper 负责持久化（Load），这就是 ETL 思维在后端开发中的体现。
>
> **第五，前后端协作 = API 数据接口设计。** 我和前端约定 RESTful API 的请求格式、返回 JSON 结构、状态码含义，这和数据开发中设计数据接口、约定数据格式的工作是一致的。

---

## ⭐ 六、可能被问的 Java 技术问题

| 问题 | 标准回答 |
|------|---------|
| Java 是你的主力语言吗？ | 不是，主力是 Python。但这个 Spring Boot 项目是我写的，Controller/Service/Mapper 三层架构、MyBatis SQL 映射、多账簿隔离等功能都是独立实现的。我能用 Java 做后端开发，也理解 Spring Boot 的核心机制。 |
| 用过哪些设计模式？ | 项目中主要用了：①**单例模式**（Spring 容器管理的 Bean 默认都是单例，如 @Service 注解的类只创建一次实例）；②**工厂模式**（Spring 的 ApplicationContext 是一个巨大的工厂）；③**模板方法模式**（MyBatis 的 SqlSessionTemplate）；④**过滤器链模式**（BookFilter + CORS Filter 组成过滤链）。 |
| MVC 是什么？ | Model-View-Controller。Model 是数据模型（Account、Transaction 等 domain 类 + Mapper 数据访问），View 是视图（Vue3 前端），Controller 是控制器（AccountController 等 REST 接口）。用户请求 → Controller 处理 → Service 业务逻辑 → Mapper 查数据库 → 返回 JSON → 前端渲染。 |
| RESTful API 怎么设计？ | ① 用 URL 表示资源（/accounts、/transactions）；② 用 HTTP 方法表示操作（GET 查、POST 增、DELETE 删）；③ 统一返回 JSON 格式 {success, message, data}；④ 无状态，每次请求独立。 |
| 项目中怎么处理异常？ | ① Service 层抛自定义异常（InvalidAccountingException 借贷不平衡）；② Controller 层 try-catch 捕获，返回 {success: false, message: "具体原因"}；③ 异常信息直接返回给前端展示。 |

---

## ⭐ 七、项目速记卡

### 卡片 1：项目一句话

> Spring Boot + Vue3 复式记账系统，多账簿隔离（Filter+ThreadLocal）、借贷平衡校验（BigDecimal）、科目树形模型、三大财务报表。

### 卡片 2：多账簿隔离

```
前端 Header: X-Book-Id
    ↓
BookFilter: 提取 Header → BookContext.set(bookId)
    ↓
BookContext: ThreadLocal 存储
    ↓
Service: BookContext.get() → 获取当前账套ID
    ↓
SQL: WHERE book_id = #{bookId}
    ↓
finally: BookContext.clear() → 防止内存泄漏 + 数据污染
```

### 卡片 3：借贷平衡校验

```
Transaction.splits (分录列表)
    ↓
遍历累加：借方 totalDebit / 贷方 totalCredit
    ↓
compareTo != 0 → 抛出异常 (事务回滚)
    ↓
相等 → UUID 主键 → 先存交易头 → 再批量存分项
    ↓
@Transactional 保证原子性
```

### 卡片 4：技术栈速记

```
后端：Spring Boot 3.1.3 + MyBatis + MySQL + Druid + JDK 17
前端：Vue3 + Element Plus
关键注解：@SpringBootApplication / @RestController / @Autowired / @Transactional
关键设计：Filter + ThreadLocal（多账簿）/ UUID（主键）/ BigDecimal（金额）/ Enum（方向）
```

---

## 八、可能的面试追问

**Q: 为什么不直接用 Gnucash 的数据库，而要重新设计？**
> Gnucash 的 XML/数据库 schema 非常复杂，是桌面软件的设计思路。Web 版本需要更轻量、更适合 Web 交互的数据模型。我参考了 Gnucash 的会计逻辑（复式记账、科目树），但重新设计了更适合 RESTful API 的数据结构和接口。

**Q: 这个项目上线了吗？能支撑多少用户？**
> 目前是开发阶段，完成了核心功能的开发。由于用了 Spring Boot + Druid 连接池 + MySQL，单机支撑几百个并发用户没有问题。未来如果需要扩展，可以在 Controller 层加负载均衡、数据库做主从读写分离。

**Q: 如果让你重新设计这个项目，会做哪些改进？**
> 1. 引入 Spring Security + JWT 做用户认证和权限控制（目前没有做登录功能）
> 2. 科目余额不再每次实时计算，而是定期物化到余额表，提高查询性能
> 3. 加上审计日志（谁、什么时间、做了什么操作），这在财务系统中非常重要
> 4. 引入 Redis 缓存常用数据（如科目列表），减少数据库压力
> 5. 用 Docker 容器化部署，方便环境管理

**Q: 为什么交易记账不用"余额表"而用"实时聚合"？**
> 当前是开发阶段的简化方案。生产环境中应该有一个 `account_balances` 表，每录入一笔凭证就更新对应科目的余额。实时聚合在数据量大时性能很差（需要扫描所有历史 Split）。余额表是数仓中常见的"预计算"思路——用空间换时间。

---

> **使用建议**：项目介绍（3分钟版）和 4 张速记卡必须逐字背熟。Java 面试问答部分理解后用自己的话复述，关键是展示你"真的动手写过代码"而不是"背过概念"。
