package com.fGnucash.service;

import com.fGnucash.common.AccountConstants;
import com.fGnucash.dao.AccountMapper;
import com.fGnucash.dao.SalesOrderMapper;
import com.fGnucash.domain.*;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import com.fGnucash.common.BookContext;
import java.math.BigDecimal;
import java.util.ArrayList;
import java.util.Date;
import java.util.List;
import java.util.UUID;

@Service
public class SalesOrderService {

    @Autowired
    private SalesOrderMapper salesOrderMapper;

    @Autowired
    private TransactionService transactionService; // 财务引擎

    @Autowired
    private AccountMapper accountMapper; // 用于校验科目存在
    private String getCurrentBookId() {
        String bookId = BookContext.get();
        if (bookId == null) {
            throw new RuntimeException("操作失败：未选择账套！");
        }
        return bookId;
    }
    /**
     * 1. 创建销售订单 (草稿)
     */
    @Transactional
    public void createOrder(SalesOrder order) {
        String bookId = getCurrentBookId();
        // ID & 状态处理
        if (order.getId() == null || order.getId().trim().isEmpty()) {
            order.setId(UUID.randomUUID().toString());
        }
        if (order.getStatus() == null) {
            order.setStatus("DRAFT");
            order.setBookId(bookId);
        }

        // 保存主表
        salesOrderMapper.insertOrder(order);

        // 处理明细 & 计算金额
        List<SalesOrderItem> items = order.getItems();
        if (items != null && !items.isEmpty()) {
            for (SalesOrderItem item : items) {
                if (item.getId() == null) item.setId(UUID.randomUUID().toString());
                item.setSo_id(order.getId());

                // 自动计算行总价
                if (item.getQuantity() != null && item.getUnit_price() != null) {
                    item.setAmount(item.getQuantity().multiply(item.getUnit_price()));
                } else {
                    item.setAmount(BigDecimal.ZERO);
                }
            }
            salesOrderMapper.batchInsertItems(items);
        }
    }

    /**
     * 2. 销售过账 (确认收入)
     * 借：应收账款 (1122)
     * 贷：主营业务收入 (Item里的 account_id)
     */
    @Transactional
    public void postOrder(String orderId) {
        String bookId = getCurrentBookId();
        SalesOrder order = salesOrderMapper.findById(orderId,bookId);
        if (order == null) throw new IllegalArgumentException("订单不存在");
        if (!"DRAFT".equals(order.getStatus())) {
            throw new IllegalStateException("非草稿状态无法过账");
        }

        // 校验默认应收科目是否存在
        String arCode = AccountConstants.ACCOUNTS_RECEIVABLE; // "1122"
        if (accountMapper.findByCode(arCode,bookId) == null) {
            throw new IllegalStateException("系统配置错误：找不到应收账款科目 (" + arCode + ")");
        }

        // 准备分录
        Transaction tx = new Transaction();
        tx.setDate(new Date());
        tx.setDescription("销售过账: " + order.getDescription());

        List<Splits> splits = new ArrayList<>();
        BigDecimal totalAmount = BigDecimal.ZERO;

        // 遍历明细，生成【贷方】分录 (确认收入)
        for (SalesOrderItem item : order.getItems()) {
            if (item.getAccount_id() == null) {
                throw new IllegalStateException("商品 [" + item.getDescription() + "] 未指定收入科目");
            }
            // 贷：收入
            Splits creditSplit = Splits.createCredit(item.getAccount_id(), item.getAmount().toString());
            creditSplit.setDescription(item.getDescription());
            splits.add(creditSplit);

            totalAmount = totalAmount.add(item.getAmount());
        }

        // 生成【借方】分录 (增加应收债权)
        Splits debitSplit = Splits.createDebit(arCode, totalAmount.toString());
        debitSplit.setDescription("应收客户款项");
        splits.add(debitSplit);

        tx.setSplits(splits);

        // 保存凭证 & 更新状态
        transactionService.saveTransaction(tx);
        salesOrderMapper.updateStatus(orderId, "POSTED",bookId);
    }

    /**
     * 3. 收款 (Collection)
     * 借：银行存款 (钱进来了)
     * 贷：应收账款 (债权消了)
     */
    @Transactional
    public void receivePayment(String orderId, String bankAccountId) {
        String bookId = getCurrentBookId();
        SalesOrder order = salesOrderMapper.findById(orderId,bookId);
        if (!"POSTED".equals(order.getStatus())) {
            throw new IllegalStateException("订单未过账或已收款，无法收款");
        }

        // 校验收款账户
        if (accountMapper.findByCode(bankAccountId,bookId) == null) {
            throw new IllegalArgumentException("收款账户不存在");
        }

        // 计算总额
        BigDecimal totalAmount = BigDecimal.ZERO;
        for (SalesOrderItem item : order.getItems()) {
            totalAmount = totalAmount.add(item.getAmount());
        }

        Transaction tx = new Transaction();
        tx.setDate(new Date());
        tx.setDescription("销售收款: " + order.getDescription());

        List<Splits> splits = new ArrayList<>();

        // 借：银行存款 (资产增加)
        splits.add(Splits.createDebit(bankAccountId, totalAmount.toString()));

        // 贷：应收账款 (资产减少/债权抵消)
        splits.add(Splits.createCredit(AccountConstants.ACCOUNTS_RECEIVABLE, totalAmount.toString()));

        tx.setSplits(splits);

        transactionService.saveTransaction(tx);
        salesOrderMapper.updateStatus(orderId, "PAID",bookId);
    }

    // 查询方法
    public List<SalesOrder> getAllOrders() { return salesOrderMapper.findAll(getCurrentBookId()); }
    public SalesOrder getOrderById(String id) {
        String bookId = getCurrentBookId();
        return salesOrderMapper.findById(id,bookId); }
}