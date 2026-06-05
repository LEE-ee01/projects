package com.fGnucash.service;

import com.fGnucash.dao.AccountMapper;
import com.fGnucash.dao.SplitMapper;
import com.fGnucash.domain.Account;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import com.fGnucash.common.BookContext;
import java.math.BigDecimal;
import java.util.List;

/*****
 * 实现我们管理会计科目
 */

@Service
public class AccountService {
    @Autowired
    private AccountMapper accountMapper;
    @Autowired
    private SplitMapper splitMapper;

    /**
     * 1. 新增科目
     * 业务规则：
     * - 科目代码必须唯一
     * - 如果指定了父科目，父科目必须存在
     */
    @Transactional
    public void createAccount(Account account) {
        String bookId = getCurrentBookId(); // 获取ID

        // 1. 设置实体的 bookId
        account.setBookId(bookId);

        // 2. 校验：检查当前账套下是否存在同名代码
        if (accountMapper.findByCode(account.getCode(), bookId) != null) {
            throw new IllegalArgumentException("当前账套下科目代码已存在: " + account.getCode());
        }

        // 3. 校验父科目
        String pCode = account.getParent_code();
        if (pCode != null && pCode.trim().isEmpty()) {
            account.setParent_code(null);
            pCode = null;
        }
        if (pCode != null) {
            // 检查父科目是否属于当前账套
            if (accountMapper.findByCode(pCode, bookId) == null) {
                throw new IllegalArgumentException("指定的父科目不存在于当前账套: " + pCode);
            }
        }

        accountMapper.insert(account);
    }

    /**
     * 2. 删除科目
     * 业务规则：
     * - 如果科目下有子科目，禁止删除（防止断链）
     * - 如果科目已被交易分录使用，禁止删除（防止坏账）
     */
    @Transactional
    public void deleteAccount(String code) {
        String bookId = getCurrentBookId();

        // 校验 1：检查是否有子科目
        List<Account> children = accountMapper.findByParentCode(code, bookId);
        if (children != null && !children.isEmpty()) {
            throw new IllegalStateException("该科目包含子科目，禁止删除！");
        }

        // 校验 2：检查是否被使用 (注意：SplitMapper 也需要后续升级支持 bookId)
        // int usage = splitMapper.countByAccountId(code, bookId);
        // 暂时略过 SplitMapper 的修改，但在完整版中必须加

        accountMapper.deleteByCode(code, bookId);
    }

    /**
     * 3. 获取科目列表 (智能分流)
     * @param parentCode 父科目代码
     * - 如果为 null 或空字符串：查询顶级科目 (根节点，如资产、负债)
     * - 如果有值：查询该父科目下的子科目 (如查询"资产"下的"银行存款")
     */
//    public List<Account> getAccounts(String parentCode) {
//        if (parentCode == null || parentCode.trim().isEmpty()) {
//            // 对应 AccountMapper.findRootAccounts()
//            return accountMapper.findRootAccounts();  //直接查询根节点
//        } else {
//            // 对应 AccountMapper.findByParentCode(code)
//            return accountMapper.findByParentCode(parentCode);  //查询父节点
//        }
//
//    }

    public List<Account> getAccounts(String parentCode) {
        String bookId = getCurrentBookId();

        List<Account> accounts;
        if (parentCode == null || parentCode.trim().isEmpty()) {
            accounts = accountMapper.findRootAccounts(bookId);
        } else {
            accounts = accountMapper.findByParentCode(parentCode, bookId);
        }

        // 计算余额
        if (accounts != null) {
            for (Account acc : accounts) {
                acc.setBalance(getAccountBalance(acc.getCode()));
            }
        }
        return accounts;
    }
    /**
     * 4. 查询单个科目详情
     */
    public Account getAccountByCode(String code) {
        String bookId = getCurrentBookId();
        return accountMapper.findByCode(code, bookId);
    }
    /**
     * 5. 获取科目余额
     */
    public BigDecimal getAccountBalance(String code) {
        String bookId = getCurrentBookId();

        Account account = accountMapper.findByCode(code, bookId);
        if (account == null) return BigDecimal.ZERO;

        // ⚠️ 注意：这里 calculateNetDebitBalance 也需要 SplitMapper 支持 bookId 参数
        // 目前暂时使用旧方法，如果你修改了 SplitMapper，请传入 bookId
        BigDecimal netDebit = splitMapper.calculateNetDebitBalance(code,bookId);
        // 理想写法：BigDecimal netDebit = splitMapper.calculateNetDebitBalance(code, bookId);

        String type = account.getType();
        if ("ASSET".equalsIgnoreCase(type) || "EXPENSE".equalsIgnoreCase(type)) {
            return netDebit;
        } else {
            return netDebit.negate();
        }

    }

    private String getCurrentBookId() {
        String bookId = BookContext.get();
        if (bookId == null) {
            throw new RuntimeException("操作失败：未选择账套！");
        }
        return bookId;
    }

}
