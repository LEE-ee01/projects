package com.fGnucash.domain;

import java.math.BigDecimal;
import java.util.List;


public class Account {
    private String code;
    private String name;
    private String type;
    // 🔗 自关联：多对一 (找爸爸)
    private Account parent;
    // 🔗 自关联：一对多 (找孩子)
    private List<Account> children;
    private String parent_code;
    private BigDecimal balance;
    private String bookId;
    public BigDecimal getBalance() {
        return balance;
    }

    public void setBalance(BigDecimal balance) {
        this.balance = balance;
    }

    public Account(String code, String name, String type, Account parent, List<Account> children) {
        this.code = code;
        this.name = name;
        this.type = type;
        this.parent = parent;
        this.children = children;
    }

    @Override
    public String toString() {
        return "Account{" +
                "code='" + code + '\'' +
                ", name='" + name + '\'' +
                ", type='" + type + '\'' +
                ", parent=" + parent +
                ", children=" + children +
                ", parent_code='" + parent_code + '\'' +
                '}';
    }

    public String getParent_code() {
        return parent_code;
    }

    public void setParent_code(String parent_code) {
        this.parent_code = parent_code;
    }

    public Account(String code, String name, String type, String parent_code) {
        this.code = code;
        this.name = name;
        this.type = type;
        this.parent_code = parent_code;
    }

    public Account() {
    }

    public Account(String code, String name, String type, Account parent) {
        this.code = code;
        this.name = name;
        this.type = type;
        this.parent = parent;
    }
    public String getBookId() { return bookId; }
    public void setBookId(String bookId) { this.bookId = bookId; }
    public String getCode() {
        return code;
    }

    public void setCode(String code) {
        this.code = code;
    }

    public String getName() {
        return name;
    }

    public void setName(String name) {
        this.name = name;
    }

    public String getType() {
        return type;
    }

    public void setType(String type) {
        this.type = type;
    }

    public Account getParent() {
        return parent;
    }

    public void setParent(Account parent) {
        this.parent = parent;
    }

    /**
     * 获取父账户代码，用于MyBatis映射
     * @return 父账户代码，如果parent为null则返回null
     */
    public String getParentCode() {
        return parent == null ? null : parent.getCode();
    }

    public List<Account> getChildren() {
        return children;
    }

    public void setChildren(List<Account> children) {
        this.children = children;
    }
}
