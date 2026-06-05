package com.fGnucash.service;
import com.fGnucash.common.AccountConstants;
import com.fGnucash.common.BookContext;
import com.fGnucash.dao.BankStatementMapper;
import com.fGnucash.dao.SplitMapper;
import com.fGnucash.domain.BankStatement;
import com.fGnucash.domain.Splits;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.Calendar;
import java.util.Date;
import java.util.List;
/****
 * 对账的service
 */
@Service
public class ReconciliationService {

    @Autowired
    private BankStatementMapper bankStatementMapper;

    @Autowired
    private SplitMapper splitMapper;
    private String getCurrentBookId() {
        String bookId = BookContext.get();
        if (bookId == null) {
            throw new RuntimeException("操作失败：未选择账套！");
        }
        return bookId;
    }
    /**
     * 🧠 核心功能：执行自动对账
     * 逻辑：连连看
     * @return 对账成功的笔数
     */
    @Transactional
    public int autoReconcile() {
        int matchCount = 0;

        // 1. 找出所有还没对上账的银行流水
        List<BankStatement> unmtachedList = bankStatementMapper.findUnmatched();

        // 2. 遍历每一笔，去系统里找“另一半”
        for (BankStatement stmt : unmtachedList) {

            // 设定宽容度：允许日期有前后 3 天的误差
            // (因为银行转账有时会有延迟)
            Date startDate = addDays(stmt.getDate(), -3);
            Date endDate = addDays(stmt.getDate(), 3);

            // 假设我们只对 "银行存款(1002)" 这个科目的账
            // 在真实系统中，这个科目代码应该作为参数传入
            String targetAccount = AccountConstants.BANK_DEPOSIT; // "1002"

            // 3. 调用 Mapper 去捞数据
            // 拿着“金额”和“日期范围”去匹配
            Splits match = splitMapper.findPotentialMatch(
                    targetAccount,
                    stmt.getAmount(),
                    startDate,
                    endDate,getCurrentBookId()
            );

            // 4. 判定时刻
            if (match != null) {
                // 找到了！🎉
                // 更新银行流水的状态为 MATCHED，并记录是对上了哪一笔
                bankStatementMapper.markMatched(stmt.getId(), match.getId());
                matchCount++;
            }
        }

        return matchCount;
    }

    // 辅助工具：日期加减天数
    private Date addDays(Date date, int days) {
        Calendar cal = Calendar.getInstance();
        cal.setTime(date);
        cal.add(Calendar.DATE, days);
        return cal.getTime();
    }
}