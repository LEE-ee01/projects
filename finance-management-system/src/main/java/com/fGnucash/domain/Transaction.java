package com.fGnucash.domain;

import com.fasterxml.jackson.annotation.JsonFormat;

import java.util.ArrayList;
import java.util.Date;
import java.util.List;

public class Transaction {
    private String id;
    @JsonFormat(pattern = "yyyy-MM-dd HH:mm:ss", timezone = "GMT+8")
    private Date date;
    private String description;
    // 🔗 一对多：一笔交易包含多个分项
    private List<Splits> splits;
    private String account_id;
    private String bookId;
    public Transaction(String id, Date date, String description, List<Splits> splits) {
        this.id = id;
        this.date = date;
        this.description = description;
        this.splits = splits;
    }

    public Transaction(String id, Date date, String description) {
        this.id = id;
        this.date = date;
        this.description = description;
    }

    public String getBookId() {
        return bookId;
    }

    public void setBookId(String bookId) {
        this.bookId = bookId;
    }

    public Transaction() {
    }

    public String getAccount_id() {
        return account_id;
    }

    public void setAccount_id(String account_id) {
        this.account_id = account_id;
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

    public String getDescription() {
        return description;
    }

    public void setDescription(String description) {
        this.description = description;
    }

    public List<Splits> getSplits() {
        return splits;
    }

    public void setSplits(List<Splits> splits) {
        this.splits = splits;
    }

    @Override
    public String toString() {
        return "Transaction{" +
                "id='" + id + '\'' +
                ", date=" + date +
                ", description='" + description + '\'' +
                ", splits=" + splits +
                '}';
    }

    public void addSplit(Splits split) {
        if (this.splits == null) {
            this.splits = new ArrayList<>();
        }
        this.splits.add(split);
    }
}
