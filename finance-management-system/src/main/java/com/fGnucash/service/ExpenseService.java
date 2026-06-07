package com.fGnucash.service;

import com.fGnucash.dao.ExpenseMapper;
import com.fGnucash.domain.*;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import com.fGnucash.common.BookContext;
import java.math.BigDecimal;
import java.util.Date;
import java.util.List;
import java.util.UUID;

@Service
public class ExpenseService {

    @Autowired
    private ExpenseMapper expenseMapper;

    @Autowired
    private TransactionService transactionService;

    public List<ExpenseClaim> getAll() {
        return expenseMapper.findAll(getCurrentBookId());
    }
    private String getCurrentBookId() {
        String bookId = BookContext.get();
        if (bookId == null) {
            throw new RuntimeException("操作失败：未选择账套！");
        }
        return bookId;
    }
    // 1. 创建草稿
    @Transactional
    public void create(ExpenseClaim claim) {
        String bookId = getCurrentBookId();
        if (claim.getId() == null || claim.getId().trim().isEmpty()) {
            claim.setId(UUID.randomUUID().toString());
        }
        claim.setStatus("DRAFT");

        // ✅ 核心修改：直接判断 null 即可，无需 format
        if (claim.getDate() == null) {
            claim.setDate(new Date());
        }
        claim.setBookId(bookId);
        expenseMapper.insertClaim(claim);

        if (claim.getItems() != null) {
            for (ExpenseItem item : claim.getItems()) {
                if (item.getId() == null) item.setId(UUID.randomUUID().toString());
                item.setClaimId(claim.getId());
                expenseMapper.insertItem(item);
            }
        }
    }

    // 2. 审核过账
    @Transactional
    public void post(String id) {
        String bookId = getCurrentBookId();
        ExpenseClaim claim = expenseMapper.findById(id,bookId);
        if (claim == null) throw new RuntimeException("单据不存在");
        if (!"DRAFT".equals(claim.getStatus())) throw new RuntimeException("状态不正确");

        Transaction tx = new Transaction();
        // ✅ 核心修改：直接赋值 Date 对象，无需 String 转换
        tx.setDate(claim.getDate());
        tx.setDescription("报销单过账: " + claim.getDescription());

        BigDecimal totalAmount = BigDecimal.ZERO;

        for (ExpenseItem item : claim.getItems()) {
            Splits debitSplit = Splits.createDebit(item.getAccountId(), item.getAmount().toString());
            debitSplit.setDescription(item.getDescription());
            tx.addSplit(debitSplit);
            totalAmount = totalAmount.add(item.getAmount());
        }

        Splits creditSplit = Splits.createCredit("2241", totalAmount.toString());
        creditSplit.setDescription("应付报销款");
        tx.addSplit(creditSplit);

        transactionService.saveTransaction(tx);
        expenseMapper.updateStatus(id, "POSTED",bookId);
    }

    // 3. 支付
    @Transactional
    public void pay(String id, String bankAccountId) {
        String bookId = getCurrentBookId();
        ExpenseClaim claim = expenseMapper.findById(id,bookId);
        if (claim == null) throw new RuntimeException("单据不存在");
        if (!"POSTED".equals(claim.getStatus())) throw new RuntimeException("必须先过账才能支付");

        BigDecimal totalAmount = BigDecimal.ZERO;
        for (ExpenseItem item : claim.getItems()) {
            totalAmount = totalAmount.add(item.getAmount());
        }

        Transaction tx = new Transaction();
        // ✅ 核心修改：直接 new Date()
        tx.setDate(new Date());
        tx.setDescription("支付报销款: " + claim.getDescription());

        Splits debitSplit = Splits.createDebit("2241", totalAmount.toString());
        debitSplit.setDescription("冲销应付款");
        tx.addSplit(debitSplit);

        Splits creditSplit = Splits.createCredit(bankAccountId, totalAmount.toString());
        creditSplit.setDescription("银行转账支出");
        tx.addSplit(creditSplit);

        transactionService.saveTransaction(tx);
        expenseMapper.updateStatus(id, "PAID",bookId);
    }
}