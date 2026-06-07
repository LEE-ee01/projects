package com.fGnucash.domain;

import com.fasterxml.jackson.annotation.JsonFormat;

import java.util.Date;
import java.util.List;

public class PurchaseOrder {
    private String id;
    //处理JSOn格式的,订单日期
    @JsonFormat(pattern = "yyyy-MM-dd HH:mm:ss", timezone = "GMT+8")
    private Date date;
    //供应商id
    private String supplier_id;
    private String description;
    /**
     * status 是连接“业务单据”和“财务凭证”的桥梁。
     * DRAFT = 只有业务员看得到（购物车）
     * POSTED = 会计也能看得到（正式账本）。
     */
    private String status; // DRAFT, POSTED
    // 一对多：包含多个明细行
    private List<PurchaseOrderItem> items;
    // 交付日期
    @JsonFormat(pattern = "yyyy-MM-dd HH:mm:ss", timezone = "GMT+8")
    private Date delivery_date;
    private String bookId;
    public PurchaseOrder() {
    }

    public Date getDelivery_date() {
        return delivery_date;
    }

    public void setDelivery_date(Date delivery_date) {
        this.delivery_date = delivery_date;
    }

    @Override
    public String toString() {
        return "PurchaseOrder{" +
                "id='" + id + '\'' +
                ", date=" + date +
                ", supplier_id='" + supplier_id + '\'' +
                ", description='" + description + '\'' +
                ", status='" + status + '\'' +
                ", items=" + items +
                ", delivery_date=" + delivery_date +
                ", bookId='" + bookId + '\'' +
                '}';
    }

    public String getBookId() {
        return bookId;
    }

    public void setBookId(String bookId) {
        this.bookId = bookId;
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

    public String getSupplier_id() {
        return supplier_id;
    }

    public void setSupplier_id(String supplier_id) {
        this.supplier_id = supplier_id;
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

    public List<PurchaseOrderItem> getItems() {
        return items;
    }

    public void setItems(List<PurchaseOrderItem> items) {
        this.items = items;
    }
}
