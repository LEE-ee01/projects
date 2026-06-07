package com.fGnucash.domain;

import java.math.BigDecimal;

public class ExpenseItem {
    private String id;
    private String claimId; // 对应数据库 claim_id
    private String description;
    private String accountId; // 对应数据库 account_id
    private BigDecimal amount;

    // Getters and Setters
    public String getId() { return id; }
    public void setId(String id) { this.id = id; }
    public String getClaimId() { return claimId; }
    public void setClaimId(String claimId) { this.claimId = claimId; }
    public String getDescription() { return description; }
    public void setDescription(String description) { this.description = description; }
    public String getAccountId() { return accountId; }
    public void setAccountId(String accountId) { this.accountId = accountId; }
    public BigDecimal getAmount() { return amount; }
    public void setAmount(BigDecimal amount) { this.amount = amount; }
}