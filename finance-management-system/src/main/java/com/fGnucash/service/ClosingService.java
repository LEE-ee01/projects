package com.fGnucash.service;

import com.fGnucash.common.AccountConstants;
import com.fGnucash.common.BookContext;
import com.fGnucash.dao.AccountMapper;
import com.fGnucash.dao.SplitMapper;
import com.fGnucash.domain.Account;
import com.fGnucash.domain.Splits;
import com.fGnucash.domain.Transaction;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.util.ArrayList;
import java.util.Date;
import java.util.List;

/*****
 * 期末结账用的
 */
@Service
public class ClosingService {
    @Autowired
    private AccountMapper accountMapper;

    @Autowired
    private SplitMapper splitMapper; // 用来算原始余额

    @Autowired
    private TransactionService transactionService; // 用来保存结账凭证
    private String getCurrentBookId() {
        String bookId = BookContext.get();
        if (bookId == null) {
            throw new RuntimeException("操作失败：未选择账套！");
        }
        return bookId;
    }
    /**
     * ✨ 执行期末结账
     * 逻辑：将所有损益类科目的余额清零，差额转入“本年利润”
     */
    @Transactional
    public void performClosing() {
        // 1. 检查“本年利润”科目是否存在
        String retainedEarningsCode = AccountConstants.RETAINED_EARNINGS;
        if (accountMapper.findByCode(retainedEarningsCode,getCurrentBookId()) == null) {
            throw new IllegalStateException("结账失败：找不到 [4103 本年利润] 科目，请先创建。");
        }

        // 2. 找出所有损益类科目 (收入 + 费用)
        List<Account> pnlAccounts = accountMapper.findPnLAccounts(getCurrentBookId());
        if (pnlAccounts.isEmpty()) {
            throw new IllegalStateException("没有找到任何收入或费用科目，无需结账。");
        }

        // 3. 准备结账凭证
        Transaction tx = new Transaction();
        tx.setDate(new Date()); // 通常应该是年底最后一天，这里暂用当前时间
        tx.setDescription("期末损益结转");

        List<Splits> splits = new ArrayList<>();
        BigDecimal totalOffset = BigDecimal.ZERO; // 用于计算最后要把多少钱转入权益

        // 4. 遍历每个科目，生成“反向”分录
        for (Account account : pnlAccounts) {
            // 获取原始净余额 (正数=借方余额，负数=贷方余额)
            // ⚠️ 注意：这里不调 AccountService，因为我们需要原始的正负号来判断方向
            BigDecimal rawBalance = splitMapper.calculateNetDebitBalance(account.getCode(),getCurrentBookId());

            // 如果余额为0，跳过
            if (rawBalance.compareTo(BigDecimal.ZERO) == 0) {
                continue;
            }

            // --- 核心反转逻辑 ---
            if (rawBalance.compareTo(BigDecimal.ZERO) > 0) {
                // 情况 A：借方有余额 (比如 费用 100) -> 我们要 贷 100
                splits.add(Splits.createCredit(account.getCode(), rawBalance.toString()));

                // 记录：我们在这个科目“拿走”了正资产，总池子里要减掉
                totalOffset = totalOffset.subtract(rawBalance);
            } else {
                // 情况 B：贷方有余额 (比如 收入 -500) -> 这是一个负数 -> 我们要 借 500
                // 取绝对值
                BigDecimal absAmount = rawBalance.abs();
                splits.add(Splits.createDebit(account.getCode(), absAmount.toString()));

                // 记录：我们“拿走”了负债(或收入)，相当于总池子增加了
                totalOffset = totalOffset.add(absAmount);
            }
        }

        if (splits.isEmpty()) {
            throw new IllegalStateException("所有损益科目余额均为0，无需结账。");
        }

        // 5. 将差额挤入“本年利润” (Plug the difference)
        // totalOffset 现在代表了净利润 (如果是正数) 或 净亏损 (如果是负数)
        // 会计恒等式：Asset + Expense = Liability + Equity + Income
        // 我们消除了 Expense(借) 和 Income(贷)。
        // 这是一个纯数学配平：
        // 如果我们生成了一堆贷方(消费用) 和 一堆借方(消收入)，现在的 splits 是不平的。
        // 不平的差额，就是利润，记入 4103。

        // 简单做法：利用 TransactionService 的校验逻辑反推，
        // 或者直接看 splits 的借贷差。
        // 这里 totalOffset 的逻辑比较绕，我们换个最稳妥的方法：
        // 统计 splits 里目前的 借方总额 和 贷方总额，差多少就补多少。

        BigDecimal currentDebitSum = BigDecimal.ZERO;
        BigDecimal currentCreditSum = BigDecimal.ZERO;

        // 这里的 Direction 是你枚举里的 DEBIT/CREDIT
        for (Splits s : splits) {
            // 注意：这里需要在 Split 类里加个 getter 获取枚举，假设你有
            // 或者判断 getDirection().toString().equals("DEBIT") ...
            // 为了代码简洁，我假设你有 isDebit() 方法，或者直接判断
            if (s.getDirection().name().equals("DEBIT")) {
                currentDebitSum = currentDebitSum.add(s.getAmount());
            } else {
                currentCreditSum = currentCreditSum.add(s.getAmount());
            }
        }

        // 算出缺口
        if (currentDebitSum.compareTo(currentCreditSum) > 0) {
            // 借方多 -> 利润是正的 -> 贷：本年利润 (增加权益)
            BigDecimal diff = currentDebitSum.subtract(currentCreditSum);
            splits.add(Splits.createCredit(retainedEarningsCode, diff.toString()));
        } else if (currentCreditSum.compareTo(currentDebitSum) > 0) {
            // 贷方多 -> 亏损 -> 借：本年利润 (减少权益)
            BigDecimal diff = currentCreditSum.subtract(currentDebitSum);
            splits.add(Splits.createDebit(retainedEarningsCode, diff.toString()));
        }

        // 6. 保存
        tx.setSplits(splits);
        transactionService.saveTransaction(tx);
    }
}
