package com.fGnucash.domain;

import org.springframework.stereotype.Component;

import java.math.BigDecimal;

public class Splits {
        private String id;
        private String transactionId; // 关联回 Transaction
        private String accountId;     // 关联到 Account
        // 💰 金额使用 BigDecimal
        private BigDecimal amount; //交易金额
        // 🧭 方向使用自定义 Enum
        private Direction direction;
        private String description;

        public Splits(String id, String transactionId, String accountId, BigDecimal amount, Direction direction, String description) {
            this.id = id;
            this.transactionId = transactionId;
            this.accountId = accountId;
            this.amount = amount;
            this.direction = direction;
            this.description = description;
    }

    public Splits() {
    }

    @Override
    public String toString() {
        return "Splits{" +
                "id='" + id + '\'' +
                ", transactionId='" + transactionId + '\'' +
                ", accountId='" + accountId + '\'' +
                ", amount=" + amount +
                ", direction=" + direction +
                ", description='" + description + '\'' +
                '}';
    }

    public String getId() {
        return id;
    }

    public void setId(String id) {
        this.id = id;
    }

    public String getTransactionId() {
        return transactionId;
    }

    public void setTransactionId(String transactionId) {
        this.transactionId = transactionId;
    }

    public String getAccountId() {
        return accountId;
    }

    public void setAccountId(String accountId) {
        this.accountId = accountId;
    }

    public BigDecimal getAmount() {
        return amount;
    }

    public void setAmount(BigDecimal amount) {
        this.amount = amount;
    }

    public Direction getDirection() {
        return direction;
    }

    public void setDirection(Direction direction) {
        this.direction = direction;
    }

    public String getDescription() {
        return description;
    }

    public void setDescription(String description) {
        this.description = description;
    }

    // ✅ 新增：快速创建借方分项的工厂方法
    public static Splits createDebit(String accountId, String amountStr) {
        Splits split = new Splits();
        split.setAccountId(accountId);
        split.setDirection(Direction.DEBIT); // 确保你有 Direction 枚举
        split.setAmount(new BigDecimal(amountStr));
        return split;
    }

    // ✅ 新增：快速创建贷方分项的工厂方法
    public static Splits createCredit(String accountId, String amountStr) {
        Splits split = new Splits();
        split.setAccountId(accountId);
        split.setDirection(Direction.CREDIT);
        split.setAmount(new BigDecimal(amountStr));
        return split;
    }
}