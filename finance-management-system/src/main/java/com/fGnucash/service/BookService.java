package com.fGnucash.service;

import com.fGnucash.dao.AccountMapper;
import com.fGnucash.dao.BookMapper;
import com.fGnucash.domain.Account;
import com.fGnucash.domain.Book;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.util.Date;
import java.util.List;
import java.util.UUID;

@Service
public class BookService {
    @Autowired
    private BookMapper bookMapper;
@Autowired
    private AccountMapper accountMapper;
    public List<Book> getAll() {
        return bookMapper.findAll();
    }

    @Transactional
    public void create(Book book) {
        book.setId(UUID.randomUUID().toString());
        book.setCreatedAt(new Date());
        bookMapper.insert(book);
        initDefaultAccounts(book.getId());
    }

    @Transactional
    public void delete(String id) {
        bookMapper.delete(id);
    }


//    private void initDefaultAccounts(String bookId) {
//        // 1. 资产类 (ASSET)
//        createAcc("1001", "库存现金", "ASSET", null, bookId);
//        createAcc("1002", "银行存款", "ASSET", null, bookId);
//        createAcc("1122", "应收账款", "ASSET", null, bookId);
//        createAcc("1123", "预付账款", "ASSET", null, bookId);
//        createAcc("1221", "其他应收款", "ASSET", null, bookId);
//        createAcc("1403", "原材料", "ASSET", null, bookId);
//        createAcc("1405", "库存商品", "ASSET", null, bookId);
//        createAcc("1601", "固定资产", "ASSET", null, bookId);
//
//        // 2. 负债类 (LIABILITY)
//        createAcc("2001", "短期借款", "LIABILITY", null, bookId);
//        createAcc("2202", "应付账款", "LIABILITY", null, bookId);
//        createAcc("2203", "预收账款", "LIABILITY", null, bookId);
//        createAcc("2211", "应付职工薪酬", "LIABILITY", null, bookId);
//        createAcc("2221", "应交税费", "LIABILITY", null, bookId);
//        createAcc("2241", "其他应付款", "LIABILITY", null, bookId); // 重要：报销用
//
//        // 3. 权益类 (EQUITY)
//        createAcc("4001", "实收资本", "EQUITY", null, bookId);
//        createAcc("4002", "资本公积", "EQUITY", null, bookId);
//        createAcc("4103", "本年利润", "EQUITY", null, bookId); // 重要：期末结账用
//        createAcc("4104", "利润分配", "EQUITY", null, bookId);
//
//        // 4. 成本类 (暂时归为 EXPENSE 或单独处理，这里简单归为 EXPENSE)
//        createAcc("5001", "生产成本", "EXPENSE", null, bookId);
//
//        // 5. 损益类 - 收入 (INCOME)
//        createAcc("6001", "主营业务收入", "INCOME", null, bookId);
//        createAcc("6051", "其他业务收入", "INCOME", null, bookId);
//        createAcc("6301", "营业外收入", "INCOME", null, bookId);
//
//        // 6. 损益类 - 费用/支出 (EXPENSE)
//        createAcc("6401", "主营业务成本", "EXPENSE", null, bookId);
//        createAcc("6403", "税金及附加", "EXPENSE", null, bookId);
//        createAcc("6601", "销售费用", "EXPENSE", null, bookId);
//        createAcc("6602", "管理费用", "EXPENSE", null, bookId);
//        createAcc("6603", "财务费用", "EXPENSE", null, bookId); // 比如银行手续费
//        createAcc("6711", "营业外支出", "EXPENSE", null, bookId);
//        createAcc("6801", "所得税费用", "EXPENSE", null, bookId);
//    }
private void initDefaultAccounts(String bookId) {
    // --- 第一步：创建 5 大根节点 (Root) ---
    // 我们用简单的数字或特殊字符作为根节点的 Code，方便排序
    createAcc("ROOT_1", "资产类 (ASSET)", "ASSET", null, bookId);
    createAcc("ROOT_2", "负债类 (LIABILITY)", "LIABILITY", null, bookId);
    createAcc("ROOT_4", "权益类 (EQUITY)", "EQUITY", null, bookId);
    createAcc("ROOT_6_IN", "收入类 (INCOME)", "INCOME", null, bookId);
    createAcc("ROOT_6_EX", "费用类 (EXPENSE)", "EXPENSE", null, bookId);

    // --- 第二步：创建子科目 (挂在对应的根节点下) ---

    // 1. 资产类子科目 -> 挂在 ROOT_1 下
    createAcc("1001", "库存现金", "ASSET", "ROOT_1", bookId);
    createAcc("1002", "银行存款", "ASSET", "ROOT_1", bookId);
    createAcc("1122", "应收账款", "ASSET", "ROOT_1", bookId);
    createAcc("1123", "预付账款", "ASSET", "ROOT_1", bookId);
    createAcc("1221", "其他应收款", "ASSET", "ROOT_1", bookId);
    createAcc("1403", "原材料", "ASSET", "ROOT_1", bookId);
    createAcc("1405", "库存商品", "ASSET", "ROOT_1", bookId);
    createAcc("1601", "固定资产", "ASSET", "ROOT_1", bookId);

    // 2. 负债类子科目 -> 挂在 ROOT_2 下
    createAcc("2001", "短期借款", "LIABILITY", "ROOT_2", bookId);
    createAcc("2202", "应付账款", "LIABILITY", "ROOT_2", bookId);
    createAcc("2203", "预收账款", "LIABILITY", "ROOT_2", bookId);
    createAcc("2211", "应付职工薪酬", "LIABILITY", "ROOT_2", bookId);
    createAcc("2221", "应交税费", "LIABILITY", "ROOT_2", bookId);
    createAcc("2241", "其他应付款", "LIABILITY", "ROOT_2", bookId); // 报销挂这里

    // 3. 权益类子科目 -> 挂在 ROOT_4 下
    createAcc("4001", "实收资本", "EQUITY", "ROOT_4", bookId);
    createAcc("4002", "资本公积", "EQUITY", "ROOT_4", bookId);
    createAcc("4103", "本年利润", "EQUITY", "ROOT_4", bookId);
    createAcc("4104", "利润分配", "EQUITY", "ROOT_4", bookId);

    // 4. 收入类子科目 -> 挂在 ROOT_6_IN 下
    createAcc("6001", "主营业务收入", "INCOME", "ROOT_6_IN", bookId);
    createAcc("6051", "其他业务收入", "INCOME", "ROOT_6_IN", bookId);
    createAcc("6301", "营业外收入", "INCOME", "ROOT_6_IN", bookId);

    // 5. 费用类子科目 -> 挂在 ROOT_6_EX 下
    createAcc("6401", "主营业务成本", "EXPENSE", "ROOT_6_EX", bookId);
    createAcc("6403", "税金及附加", "EXPENSE", "ROOT_6_EX", bookId);
    createAcc("6601", "销售费用", "EXPENSE", "ROOT_6_EX", bookId);
    createAcc("6602", "管理费用", "EXPENSE", "ROOT_6_EX", bookId);
    createAcc("6603", "财务费用", "EXPENSE", "ROOT_6_EX", bookId);
    createAcc("6711", "营业外支出", "EXPENSE", "ROOT_6_EX", bookId);
    createAcc("6801", "所得税费用", "EXPENSE", "ROOT_6_EX", bookId);
}
    private void createAcc(String code, String name, String type, String pCode, String bookId) {
        Account acc = new Account();
        acc.setCode(code);
        acc.setName(name);
        acc.setType(type);
        acc.setParent_code(pCode);
        acc.setBookId(bookId);          // ✅ 关键：绑定到当前账套
        acc.setBalance(BigDecimal.ZERO); // 初始余额 0

        // 简单的防重检查：如果这个账套下还没这个代码，就插入
        // 注意：AccountMapper 必须支持带 bookId 的查询
        if (accountMapper.findByCode(code, bookId) == null) {
            accountMapper.insert(acc);
        }
    }
}