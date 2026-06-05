package com.fGnucash.dao;

import com.fGnucash.domain.PurchaseOrder;
import com.fGnucash.domain.PurchaseOrderItem;
import org.apache.ibatis.annotations.*;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface PurchaseOrderMapper {

    /**
     * 1. 写入操作 (保存订单)
     * 保存订单主表
     */
    @Insert("INSERT INTO purchase_orders (id, date, delivery_date, supplier_id, description, status, book_id) " +
            "VALUES (#{id}, #{date}, #{delivery_date}, #{supplier_id}, #{description}, #{status}, #{bookId})")
    int insertOrder(PurchaseOrder order);

    /**
     * 2. 查询操作 (查看订单)
     * 查询所有采购订单 (带明细)
     * 原理：先查主表，再拿着 ID 去调用 findItemsByPoId 查子表
     */
    @Select("SELECT * FROM purchase_orders WHERE book_id = #{bookId} ORDER BY date DESC")
    @Results({
            @Result(property = "id", column = "id", id = true),
            @Result(property = "date", column = "date"),
            @Result(property = "supplier_id", column = "supplier_id"),
            @Result(property = "description", column = "description"),
            @Result(property = "status", column = "status"),
            @Result(property = "delivery_date", column = "delivery_date"),
            // 级联查询
            @Result(property = "items", column = "id",
                    many = @Many(select = "com.fGnucash.dao.PurchaseOrderMapper.findItemsByPoId"))
    })
    List<PurchaseOrder> findAll(@Param("bookId") String bookId);

    /**
     * 辅助查询：根据主表ID查明细
     */
    @Select("SELECT * FROM purchase_order_items WHERE po_id = #{poId}")
    List<PurchaseOrderItem> findItemsByPoId(String poId);

    /**
     * 根据ID查单个订单 (用于详情页或过账前的检查)
     */
    @Select("SELECT * FROM purchase_orders WHERE id = #{id} AND book_id = #{bookId}")
    @Results({
            @Result(property = "id", column = "id", id = true),
            @Result(property = "items", column = "id",
                    many = @Many(select = "com.fGnucash.dao.PurchaseOrderMapper.findItemsByPoId"))
    })
    PurchaseOrder findById(@Param("id") String id, @Param("bookId") String bookId);

    /**
     * 更新订单状态 (用于过账: DRAFT -> POSTED)
     */
    @Update("UPDATE purchase_orders SET status = #{status} WHERE id = #{id} AND book_id = #{bookId}")
    int updateStatus(@Param("id") String id, @Param("status") String status, @Param("bookId") String bookId);

    /**
     * 批量保存订单明细
     * 使用 <script> 标签包裹，让 MyBatis 解析里面的 <foreach> 循环
     */
    @Insert("<script>" +
            "INSERT INTO purchase_order_items " +
            "(id, po_id, description, quantity, unit_price, amount, tax_id, account_id) " + // 1. 加列名
            "VALUES " +
            "<foreach collection='items' item='item' separator=','>" +
            "(#{item.id}, #{item.po_id}, #{item.description}, #{item.quantity}, " +
            "#{item.unit_price}, #{item.amount}, #{item.tax_id}, #{item.account_id})" + // 2. 加占位符
            "</foreach>" +
            "</script>")
    int batchInsertItems(@Param("items") java.util.List<PurchaseOrderItem> items);


}
