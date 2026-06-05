package com.fGnucash.service;

import com.fGnucash.dao.TransactionMapper;
import com.fGnucash.domain.Direction;
import com.fGnucash.domain.Splits;
import com.fGnucash.domain.Transaction;
import com.fGnucash.exception.InvalidAccountingException;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import com.fGnucash.common.BookContext;
import java.math.BigDecimal;
import java.util.List;
import java.util.UUID;

/****
 * 复式记账的核心功能，根据各split的方向完成借贷相等校验后存入一次transaction里
 *
 */
@Service
public class TransactionService {

    @Autowired
    public TransactionMapper transactionMapper;

    public void t(){
        Transaction transaction = transactionMapper.findTransaction("1");
        System.out.println(transaction);
    }
    // 获取当前账套ID
    private String getCurrentBookId() {
        String bookId = BookContext.get();
        if (bookId == null) throw new RuntimeException("操作失败：未选择账套！");
        return bookId;
    }
    @Transactional   //开启事务
    //借贷必相等！！！！
    public void saveTransaction(Transaction transaction){
        String bookId = getCurrentBookId();

        // 1. 设置 ID 和 BookId
        if (transaction.getId() == null) transaction.setId(UUID.randomUUID().toString());
        transaction.setBookId(bookId); // 👈 关键：标记这笔交易属于哪个账套
        BigDecimal totalDebit = BigDecimal.ZERO;
        BigDecimal totalCredit = BigDecimal.ZERO;
        List<Splits> splits = transaction.getSplits();
        for(Splits split:splits){
            if(split.getDirection() == Direction.DEBIT){
                totalDebit = totalDebit.add(split.getAmount());
            }
            else {
                totalCredit = totalCredit.add(split.getAmount());
            }
        }
        if(totalDebit.compareTo(totalCredit) != 0) {
            throw new InvalidAccountingException("试算不平衡！借方总额: " + totalDebit + ", 贷方总额: " + totalCredit);
        }
        // 4. ✅ 校验通过，准备保存到数据库
        // 通常我们需要在这里生成 UUID，确保存入数据库时不为空
//        if (transaction.getId() == null) {
//            transaction.setId(UUID.randomUUID().toString());
//        }
        if (transaction.getId() == null || transaction.getId().trim().isEmpty()) {
            transaction.setId(UUID.randomUUID().toString());
        }
        // 先保存交易头
        transactionMapper.saveTransaction(transaction);

        // 再给每个分项填上 Transaction ID，并生成自己的 ID
//        for (Splits split : transaction.getSplits()) {
//            split.setId(UUID.randomUUID().toString());
//            split.setTransactionId(transaction.getId()); // 把分项拴在交易上
//        }

        if (transaction.getSplits() != null && !transaction.getSplits().isEmpty()) {
            for (Splits split : transaction.getSplits()) {
                // 给分项生成自己的 ID
                if (split.getId() == null) {
                    split.setId(UUID.randomUUID().toString());
                }
                // 关键：把分项“拴”在交易上 (设置外键)
                split.setTransactionId(transaction.getId());
            }
        }
        // 最后批量保存分项
        transactionMapper.batchSaveSplits(transaction.getSplits());
    }

    /**
     * 获取交易列表 (用于查账)
     */
    public List<Transaction> getTransactionList() {
        String bookId = getCurrentBookId();
        return transactionMapper.findAll(bookId);
    }
}
