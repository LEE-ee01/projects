package com.fGnucash.domain;

import com.fasterxml.jackson.annotation.JsonFormat;

import java.math.BigDecimal;
import java.util.Date;

/*****
 * 银行对账表
 */
public class BankStatement {
    private String id;

    @JsonFormat(pattern = "yyyy-MM-dd HH:mm:ss", timezone = "GMT+8")
    private Date date;

    private BigDecimal amount;
    private String description;
    private String status; // UNMATCHED, MATCHED

    // 对应数据库 matched_split_id
    private String matched_split_id;

    public BankStatement() {
    }

    public String getId() {
        return id;
    }

    public void setId(String id) {
        this.id = id;
    }

    public Date getDate() {
        return date;
    }

    public void setDate(Date date) {
        this.date = date;
    }

    public BigDecimal getAmount() {
        return amount;
    }

    public void setAmount(BigDecimal amount) {
        this.amount = amount;
    }

    public String getDescription() {
        return description;
    }

    public void setDescription(String description) {
        this.description = description;
    }

    public String getStatus() {
        return status;
    }

    public void setStatus(String status) {
        this.status = status;
    }

    public String getMatched_split_id() {
        return matched_split_id;
    }

    public void setMatched_split_id(String matched_split_id) {
        this.matched_split_id = matched_split_id;
    }
}
