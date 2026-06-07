package com.fGnucash.service;

import com.fGnucash.common.AccountConstants;
import com.fGnucash.dao.AccountMapper;
import com.fGnucash.dao.PurchaseOrderMapper;
import com.fGnucash.domain.PurchaseOrder;
import com.fGnucash.domain.PurchaseOrderItem;
import com.fGnucash.domain.Splits;
import com.fGnucash.domain.Transaction;
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
public class PurchaseOrderService {

    @Autowired
    private PurchaseOrderMapper purchaseOrderMapper;
    @Autowired
    private TransactionService transactionService;
    @Autowired
    private AccountMapper accountMapper;
    private String getCurrentBookId() {
        String bookId = BookContext.get();
        if (bookId == null) {
            throw new RuntimeException("操作失败：未选择账套！");
        }
        return bookId;
    }
    /**
     * 1. 创建采购订单
     * 逻辑：
     * - 设置初始状态为 DRAFT (草稿)
     * - 生成 ID
     * - 遍历明细：生成ID、关联主表
     * - 核心：自动计算行总价 (数量 * 单价)，防止前端算错
     */
    @Transactional
    public void createOrder(PurchaseOrder order) {
        String bookId = getCurrentBookId();
        // 1. 基础信息处理
        if (order.getId() == null || order.getId().trim().isEmpty()) {
            order.setId(UUID.randomUUID().toString());
        }

        // 新单据默认都是草稿，只有确认收货/发票后才过账
        if (order.getStatus() == null) {
            order.setStatus("DRAFT");
        }
        order.setBookId(bookId);
        // 2. 保存主表
        purchaseOrderMapper.insertOrder(order);

        // 3. 处理明细行
        List<PurchaseOrderItem> items = order.getItems();
        if (items != null && !items.isEmpty()) {
            for (PurchaseOrderItem item : items) {
                // 生成明细 ID
                if (item.getId() == null) {
                    item.setId(UUID.randomUUID().toString());
                }

                // 🔗 关联主表 (外键)
                item.setPo_id(order.getId());

                // 💰 核心业务逻辑：自动计算总价
                // Amount = Quantity * UnitPrice
                if (item.getQuantity() != null && item.getUnit_price() != null) {
                    BigDecimal calculatedAmount = item.getQuantity().multiply(item.getUnit_price());
                    item.setAmount(calculatedAmount);
                } else {
                    // 如果缺数量或单价，视为 0
                    item.setAmount(BigDecimal.ZERO);
                }
            }

            // 4. 批量保存明细
            purchaseOrderMapper.batchInsertItems(items);
        }
    }

    /**
     * 2. 查询订单列表
     */
    public List<PurchaseOrder> getAllOrders() {
        return purchaseOrderMapper.findAll(getCurrentBookId());
    }

    /**
     * 3. 查询单个订单详情
     */
    public PurchaseOrder getOrderById(String id) {
        return purchaseOrderMapper.findById(id,getCurrentBookId());
    }

    /**
     * 核心功能：过账
     * 把 "草稿" 变成 "会计凭证"
     * 即将purchaseOrder--》transaction
     */
    @Transactional
    public void postOrder(String orderId) {
        String bookId = getCurrentBookId();
        // 1. 获取订单详情
        PurchaseOrder order = purchaseOrderMapper.findById(orderId,bookId);
        if (order == null) {
            throw new IllegalArgumentException("订单不存在: " + orderId);
        }

        // 2. 状态校验：只有草稿才能过账
        if (!"DRAFT".equals(order.getStatus())) {
            throw new IllegalStateException("订单状态不正确，无法过账。当前状态: " + order.getStatus());
        }
        // 安全检查：在使用默认科目之前，先确认数据库里真的有它！
        String apCode = AccountConstants.ACCOUNTS_PAYABLE; // "2002"

        if (accountMapper.findByCode(apCode,bookId) == null) {
            throw new IllegalStateException(
                    "系统配置错误：找不到默认的应付账款科目 (代码: " + apCode + ")。请先在科目表中创建该科目。"
            );
        }

        // 3. 准备会计分录 (Transaction)
        Transaction tx = new Transaction();
        tx.setDate(new Date()); // 入账日期为当前时间
        tx.setDescription("采购过账: " + order.getDescription()); // 摘要关联订单

        List<Splits> splits = new ArrayList<>();
        BigDecimal totalAmount = BigDecimal.ZERO; // 用于计算总应付金额

        // 4. 生成借方分录 (Debit) - 对应每一个商品行
        List<PurchaseOrderItem> items = order.getItems();
        if (items == null || items.isEmpty()) {
            throw new IllegalStateException("空订单无法过账");
        }

        for (PurchaseOrderItem item : items) {
            if (item.getAccount_id() == null) {
                throw new IllegalStateException("商品 [" + item.getDescription() + "] 未指定入账科目！");
            }

            // 使用静态方法快速创建借方
            Splits debitSplit = Splits.createDebit(
                    item.getAccount_id(),
                    item.getAmount().toString()
            );
            debitSplit.setDescription(item.getDescription()); // 分项备注

            splits.add(debitSplit);

            // 累加总金额
            totalAmount = totalAmount.add(item.getAmount());
        }

        // 5. 生成贷方分录 (Credit) - 对应 "应付账款"
        // 这一笔是我们要给供应商的钱
        Splits creditSplit = Splits.createCredit(
                AccountConstants.ACCOUNTS_PAYABLE,
                totalAmount.toString()
        );
        creditSplit.setDescription("应付供应商款项");
        splits.add(creditSplit);

        // 装载分项
        tx.setSplits(splits);

        // 6. 调用财务引擎保存凭证 (会自动校验借贷平衡)
        transactionService.saveTransaction(tx);

        // 7. 更新订单状态为 "POSTED" (已过账)
        purchaseOrderMapper.updateStatus(orderId, "POSTED",bookId);
    }

    /**
     * 核心功能：支付采购款
     * @param orderId 订单ID
     * @param bankAccountId 付款账户代码 (如 "1002" 银行存款)
     */
    @Transactional
    public void payOrder(String orderId, String bankAccountId) {
        String bookId = getCurrentBookId();
        // 1. 获取订单
        PurchaseOrder order = purchaseOrderMapper.findById(orderId,bookId);
        if (order == null) {
            throw new IllegalArgumentException("订单不存在");
        }

        // 2. 状态校验
        // 只有 POSTED (已过账) 的订单才能付款
        // 如果是 DRAFT (草稿)，提示先过账
        // 如果是 PAID (已付款)，提示不能重复付
        if (!"POSTED".equals(order.getStatus())) {
            throw new IllegalStateException("当前状态无法付款: " + order.getStatus() +
                    " (必须是 POSTED 状态才能付款)");
        }

        // 3. 校验付款账户 (银行账户必须存在)
        if (accountMapper.findByCode(bankAccountId,bookId) == null) {
            throw new IllegalArgumentException("付款账户不存在: " + bankAccountId);
        }

        // 4. 计算需要支付的总金额
        BigDecimal totalAmount = BigDecimal.ZERO;
        for (PurchaseOrderItem item : order.getItems()) {
            totalAmount = totalAmount.add(item.getAmount());
        }

        // 5. 生成付款凭证 (Transaction)
        Transaction tx = new Transaction();
        tx.setDate(new Date());
        tx.setDescription("支付采购款: " + order.getDescription());

        List<Splits> splits = new ArrayList<>();

        // 借方: 应付账款 (2002) -> 债务减少
        Splits debitSplit = Splits.createDebit(
                AccountConstants.ACCOUNTS_PAYABLE, // "2002"
                totalAmount.toString()
        );
        debitSplit.setDescription("冲销应付账款");
        splits.add(debitSplit);

        // 贷方: 银行存款 (bankAccountId) -> 钱少了
        Splits creditSplit = Splits.createCredit(
                bankAccountId,
                totalAmount.toString()
        );
        creditSplit.setDescription("银行转账支付");
        splits.add(creditSplit);

        tx.setSplits(splits);

        // 6. 保存凭证
        transactionService.saveTransaction(tx);

        // 7. 更新订单状态为 PAID
        purchaseOrderMapper.updateStatus(orderId, "PAID",bookId);
    }

}
