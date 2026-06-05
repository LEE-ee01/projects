package com.fGnucash.service;

import com.fGnucash.common.BookContext;
import com.fGnucash.dao.AccountMapper;
import com.fGnucash.domain.Account;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.time.LocalDate;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/****
 * 我们用来实现报表生成服务的
 */
@Service
public class ReportService {
    @Autowired
    private AccountMapper accountMapper;

    //需要使用其计算账户额余额的方法，用于试算平衡
    @Autowired
    private AccountService accountService;
    private String getCurrentBookId() {
        String bookId = BookContext.get();
        if (bookId == null) {
            throw new RuntimeException("操作失败：未选择账套！");
        }
        return bookId;
    }
    public List<Map<String, Object>> getTrialBalance(){
        List<Map<String, Object>> report = new ArrayList<>();
        //获取所有的account
        List<Account> allAccounts = accountMapper.findAll(getCurrentBookId());
        for (Account account:allAccounts) {
            BigDecimal balance = accountService.getAccountBalance(account.getCode());
            // 过滤掉余额为 0 的科目 (可选，这样报表更干净)
            if (balance.compareTo(BigDecimal.ZERO) != 0) {
                Map<String, Object> row = new HashMap<>();
                row.put("code", account.getCode());
                row.put("name", account.getName());
                row.put("type", account.getType());
                row.put("balance", balance);

                report.add(row);
            }
        }
        return report;
    }

    /**
     * 生成利润表 (Income Statement)
     * 范围：收入、费用
     * 结果：净利润
     */
    public Map<String, Object> getIncomeStatement() {
        List<Account> allAccounts = accountMapper.findAll(getCurrentBookId());

        List<Map<String, Object>> revenues = new ArrayList<>();
        List<Map<String, Object>> expenses = new ArrayList<>();

        BigDecimal totalRevenue = BigDecimal.ZERO;
        BigDecimal totalExpense = BigDecimal.ZERO;

        for (Account account : allAccounts) {
            BigDecimal balance = accountService.getAccountBalance(account.getCode());
            if (balance.compareTo(BigDecimal.ZERO) == 0) continue; // 跳过0余额

            Map<String, Object> row = new HashMap<>();
            row.put("code", account.getCode());
            row.put("name", account.getName());
            row.put("balance", balance);

            // 分类汇总
            if ("INCOME".equalsIgnoreCase(account.getType())) {
                revenues.add(row);
                totalRevenue = totalRevenue.add(balance);
            } else if ("EXPENSE".equalsIgnoreCase(account.getType())) {
                expenses.add(row);
                totalExpense = totalExpense.add(balance);
            }
        }

        // 计算净利润 = 总收入 - 总费用
        // 注意：在会计恒等式中，收入通常是贷方(正)，费用是借方(正)。
        // 这里的 getAccountBalance 已经处理了正负号，返回的都是“绝对值”概念的正数
        // 所以直接相减即可。
        BigDecimal netIncome = totalRevenue.subtract(totalExpense);

        Map<String, Object> report = new HashMap<>();
        report.put("revenues", revenues);          // 收入明细列表
        report.put("expenses", expenses);          // 费用明细列表
        report.put("totalRevenue", totalRevenue);  // 总收入
        report.put("totalExpense", totalExpense);  // 总费用
        report.put("netIncome", netIncome);        // 净利润 (赚了多少钱)
        return report;
    }

    /**
     * 生成资产负债表 (Balance Sheet)
     * 范围：资产、负债、权益
     * 核心校验：资产总额 = 负债总额 + 权益总额 (含净利润)
     */
    public Map<String, Object> getBalanceSheet() {
        List<Account> allAccounts = accountMapper.findAll(getCurrentBookId());

        List<Map<String, Object>> assets = new ArrayList<>();
        List<Map<String, Object>> liabilities = new ArrayList<>();
        List<Map<String, Object>> equity = new ArrayList<>();

        BigDecimal totalAsset = BigDecimal.ZERO;
        BigDecimal totalLiability = BigDecimal.ZERO;
        BigDecimal totalEquity = BigDecimal.ZERO;

        for (Account account : allAccounts) {
            BigDecimal balance = accountService.getAccountBalance(account.getCode());
            if (balance.compareTo(BigDecimal.ZERO) == 0) continue;

            Map<String, Object> row = new HashMap<>();
            row.put("code", account.getCode());
            row.put("name", account.getName());
            row.put("balance", balance);

            String type = account.getType();
            if ("ASSET".equalsIgnoreCase(type)) {
                assets.add(row);
                totalAsset = totalAsset.add(balance);
            } else if ("LIABILITY".equalsIgnoreCase(type)) {
                liabilities.add(row);
                totalLiability = totalLiability.add(balance);
            } else if ("EQUITY".equalsIgnoreCase(type)) {
                equity.add(row);
                totalEquity = totalEquity.add(balance);
            }
        }

        // 关键步骤：计算本期净利润，并加入权益部分
        // 因为“利润”最终是属于股东的权益。如果不加这个，资产负债表是不平的。
        Map<String, Object> incomeStatement = getIncomeStatement();
        BigDecimal netIncome = (BigDecimal) incomeStatement.get("netIncome");

        if (netIncome.compareTo(BigDecimal.ZERO) != 0) {
            Map<String, Object> retainedEarnings = new HashMap<>();
            retainedEarnings.put("code", "9999"); // 虚拟代码
            retainedEarnings.put("name", "本年利润 (未结转)");
            retainedEarnings.put("balance", netIncome);

            equity.add(retainedEarnings); // 加到权益列表展示
            totalEquity = totalEquity.add(netIncome); // 加到权益总额
        }

        Map<String, Object> report = new HashMap<>();
        report.put("assets", assets);
        report.put("liabilities", liabilities);
        report.put("equity", equity);

        report.put("totalAsset", totalAsset);
        report.put("totalLiability", totalLiability);
        report.put("totalEquity", totalEquity);
        // 方便前端校验：负债+权益
        report.put("totalLiabilityAndEquity", totalLiability.add(totalEquity));

        return report;
    }
//    public Map<String, Object> getBalanceSheet(LocalDate asOfDate) {
//        String bookId = getCurrentBookId();
//        // 资产负债表是“存量”概念，查询从开天辟地到现在的累计余额
//        LocalDate startOfTime = LocalDate.of(1900, 1, 1);
//
//        List<Account> allAccounts = accountMapper.findAll(bookId);
//
//        List<Map<String, Object>> assets = new ArrayList<>();
//        List<Map<String, Object>> liabilities = new ArrayList<>();
//        List<Map<String, Object>> equity = new ArrayList<>();
//
//        BigDecimal totalAsset = BigDecimal.ZERO;
//        BigDecimal totalLiability = BigDecimal.ZERO;
//        BigDecimal totalEquity = BigDecimal.ZERO;
//
//        // 1. 遍历计算资产、负债、权益科目的余额
//        for (Account account : allAccounts) {
//            BigDecimal balance = accountMapper.getPeriodBalance(account.getCode(), bookId, startOfTime, asOfDate);
//            // 资产负债表一般习惯看正数
//            // 资产：借方为正；负债/权益：贷方为正（数据库存的是净借方，所以负债权益通常是负数，要取反）
//            // 这里为了简单，统一取绝对值展示
//            BigDecimal absBalance = balance.abs();
//
//            if (absBalance.compareTo(BigDecimal.ZERO) == 0) continue;
//
//            Map<String, Object> row = new HashMap<>();
//            row.put("code", account.getCode());
//            row.put("name", account.getName());
//            row.put("balance", absBalance);
//
//            String type = account.getType();
//            if ("ASSET".equalsIgnoreCase(type)) {
//                assets.add(row);
//                totalAsset = totalAsset.add(absBalance);
//            } else if ("LIABILITY".equalsIgnoreCase(type)) {
//                liabilities.add(row);
//                totalLiability = totalLiability.add(absBalance);
//            } else if ("EQUITY".equalsIgnoreCase(type)) {
//                equity.add(row);
//                totalEquity = totalEquity.add(absBalance);
//            }
//        }
//
//        // 2. 计算并追加“未分配利润” (Retained Earnings)
//        // 逻辑：所有收入 - 所有费用 (截止到今天)
//        Map<String, Object> incomeData = getIncomeStatement(startOfTime, asOfDate);
//        BigDecimal netIncome = (BigDecimal) incomeData.get("netIncome"); // 这是一个正数(如果盈利)
//
//        if (netIncome.compareTo(BigDecimal.ZERO) != 0) {
//            Map<String, Object> retainedEarnings = new HashMap<>();
//            retainedEarnings.put("code", "9999");
//            retainedEarnings.put("name", "未分配利润 (Retained Earnings)");
//            retainedEarnings.put("balance", netIncome.abs()); // 展示绝对值
//            // 如果亏损，在权益里应该是减项，这里简化处理，假设盈利
//            equity.add(retainedEarnings);
//            totalEquity = totalEquity.add(netIncome);
//        }
//
//        // 3. 计算总计
//        BigDecimal totalLiabAndEquity = totalLiability.add(totalEquity);
//
//        // 4. ✅ 垂直分析 (计算百分比)
//        // 资产占比 = 该项资产 / 总资产
//        calculatePercentage(assets, totalAsset);
//        // 负债占比 = 该项负债 / (负债+权益)
//        calculatePercentage(liabilities, totalLiabAndEquity);
//        // 权益占比 = 该项权益 / (负债+权益)
//        calculatePercentage(equity, totalLiabAndEquity);
//
//        Map<String, Object> report = new HashMap<>();
//        report.put("assets", assets);
//        report.put("liabilities", liabilities);
//        report.put("equity", equity);
//        report.put("totalAsset", totalAsset);
//        report.put("totalLiability", totalLiability);
//        report.put("totalEquity", totalEquity);
//        report.put("totalLiabilityAndEquity", totalLiabAndEquity);
//
//        return report;
//    }
    /**
     * 3. ✅ 升级版：资产负债表 (支持截止日期 + 垂直分析)
     */
//    public Map<String, Object> getBalanceSheet(LocalDate asOfDate) {
//        String bookId = getCurrentBookId();
//        // 资产负债表是“存量”概念，查询从开天辟地到现在的累计余额
//        LocalDate startOfTime = LocalDate.of(1900, 1, 1);
//
//        List<Account> allAccounts = accountMapper.findAll(bookId);
//
//        List<Map<String, Object>> assets = new ArrayList<>();
//        List<Map<String, Object>> liabilities = new ArrayList<>();
//        List<Map<String, Object>> equity = new ArrayList<>();
//
//        BigDecimal totalAsset = BigDecimal.ZERO;
//        BigDecimal totalLiability = BigDecimal.ZERO;
//        BigDecimal totalEquity = BigDecimal.ZERO;
//
//        // 1. 遍历计算资产、负债、权益科目的余额
//        for (Account account : allAccounts) {
//            BigDecimal balance = accountMapper.getPeriodBalance(account.getCode(), bookId, startOfTime, asOfDate);
//            // 资产负债表一般习惯看正数
//            // 资产：借方为正；负债/权益：贷方为正（数据库存的是净借方，所以负债权益通常是负数，要取反）
//            // 这里为了简单，统一取绝对值展示
//            BigDecimal absBalance = balance.abs();
//
//            if (absBalance.compareTo(BigDecimal.ZERO) == 0) continue;
//
//            Map<String, Object> row = new HashMap<>();
//            row.put("code", account.getCode());
//            row.put("name", account.getName());
//            row.put("balance", absBalance);
//
//            String type = account.getType();
//            if ("ASSET".equalsIgnoreCase(type)) {
//                assets.add(row);
//                totalAsset = totalAsset.add(absBalance);
//            } else if ("LIABILITY".equalsIgnoreCase(type)) {
//                liabilities.add(row);
//                totalLiability = totalLiability.add(absBalance);
//            } else if ("EQUITY".equalsIgnoreCase(type)) {
//                equity.add(row);
//                totalEquity = totalEquity.add(absBalance);
//            }
//        }
//
//        // 2. 计算并追加“未分配利润” (Retained Earnings)
//        // 逻辑：所有收入 - 所有费用 (截止到今天)
//        Map<String, Object> incomeData = getIncomeStatement(startOfTime, asOfDate);
//        BigDecimal netIncome = (BigDecimal) incomeData.get("netIncome"); // 这是一个正数(如果盈利)
//
//        if (netIncome.compareTo(BigDecimal.ZERO) != 0) {
//            Map<String, Object> retainedEarnings = new HashMap<>();
//            retainedEarnings.put("code", "9999");
//            retainedEarnings.put("name", "未分配利润 (Retained Earnings)");
//            retainedEarnings.put("balance", netIncome.abs()); // 展示绝对值
//            // 如果亏损，在权益里应该是减项，这里简化处理，假设盈利
//            equity.add(retainedEarnings);
//            totalEquity = totalEquity.add(netIncome);
//        }
//
//        // 3. 计算总计
//        BigDecimal totalLiabAndEquity = totalLiability.add(totalEquity);
//
//        // 4. ✅ 垂直分析 (计算百分比)
//        // 资产占比 = 该项资产 / 总资产
//        calculatePercentage(assets, totalAsset);
//        // 负债占比 = 该项负债 / (负债+权益)
//        calculatePercentage(liabilities, totalLiabAndEquity);
//        // 权益占比 = 该项权益 / (负债+权益)
//        calculatePercentage(equity, totalLiabAndEquity);
//
//        Map<String, Object> report = new HashMap<>();
//        report.put("assets", assets);
//        report.put("liabilities", liabilities);
//        report.put("equity", equity);
//        report.put("totalAsset", totalAsset);
//        report.put("totalLiability", totalLiability);
//        report.put("totalEquity", totalEquity);
//        report.put("totalLiabilityAndEquity", totalLiabAndEquity);
//
//        return report;
//    }
    /**
     * ✅ 升级版：利润表 (支持日期范围)
     */
    public Map<String, Object> getIncomeStatement(LocalDate startDate, LocalDate endDate) {
        String bookId = getCurrentBookId();
        List<Account> allAccounts = accountMapper.findAll(bookId);

        List<Map<String, Object>> revenues = new ArrayList<>();
        List<Map<String, Object>> expenses = new ArrayList<>();

        BigDecimal totalRevenue = BigDecimal.ZERO;
        BigDecimal totalExpense = BigDecimal.ZERO;

        // 1. 遍历所有科目，计算该时间段内的发生额
        for (Account account : allAccounts) {
            // 调用刚才在 Mapper 里新加的方法
            BigDecimal balance = accountMapper.getPeriodBalance(account.getCode(), bookId, startDate, endDate);

            // 取绝对值展示 (假设数据库里收入是负数，费用是正数，或者反之，这里统一转正数展示)
            BigDecimal absBalance = balance.abs();

            if (absBalance.compareTo(BigDecimal.ZERO) == 0) continue;

            Map<String, Object> row = new HashMap<>();
            row.put("code", account.getCode());
            row.put("name", account.getName());
            row.put("balance", absBalance);

            if ("INCOME".equalsIgnoreCase(account.getType())) {
                revenues.add(row);
                totalRevenue = totalRevenue.add(absBalance);
            } else if ("EXPENSE".equalsIgnoreCase(account.getType())) {
                expenses.add(row);
                totalExpense = totalExpense.add(absBalance);
            }
        }

        // 2. 计算百分比 (Common Size Analysis)
        // 每一项费用占总收入的比例，这是老板最爱看的
        calculatePercentage(revenues, totalRevenue);
        calculatePercentage(expenses, totalRevenue); // 注意：费用也是除以总收入

        BigDecimal netIncome = totalRevenue.subtract(totalExpense);

        Map<String, Object> report = new HashMap<>();
        report.put("revenues", revenues);
        report.put("expenses", expenses);
        report.put("totalRevenue", totalRevenue);
        report.put("totalExpense", totalExpense);
        report.put("netIncome", netIncome);

        // 返回净利润率 (Net Profit Margin)
        if (totalRevenue.compareTo(BigDecimal.ZERO) != 0) {
            report.put("margin", netIncome.divide(totalRevenue, 4, RoundingMode.HALF_UP).multiply(new BigDecimal(100)));
        } else {
            report.put("margin", BigDecimal.ZERO);
        }

        return report;
    }
    // 辅助方法：计算 list 中每一行的 percentage
    private void calculatePercentage(List<Map<String, Object>> list, BigDecimal denominator) {
        if (denominator.compareTo(BigDecimal.ZERO) == 0) return;
        for (Map<String, Object> row : list) {
            BigDecimal bal = (BigDecimal) row.get("balance");
            // 计算百分比，保留2位小数
            BigDecimal pct = bal.divide(denominator, 4, RoundingMode.HALF_UP).multiply(new BigDecimal(100));
            row.put("percentage", pct);
        }
    }


    }