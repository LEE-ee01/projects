package com.fGnucash.dao;

import com.fGnucash.domain.SalesOrder;
import com.fGnucash.domain.SalesOrderItem;
import org.apache.ibatis.annotations.*;
import org.springframework.stereotype.Repository;

import java.util.List;
@Repository
public interface SalesOrderMapper {

    /**
     * 1. 写入操作 (保存销售订单)
     * 保存主表
     * 注意：#{customer_id} 对应实体类里的字段名
     */
    @Insert("INSERT INTO sales_orders (id, customer_id, date, description, status, book_id) " +
            "VALUES (#{id}, #{customer_id}, #{date}, #{description}, #{status}, #{bookId})")
    void insertOrder(SalesOrder order);

    /**
     * 批量保存明细 (核心性能点)
     */
    @Insert("<script>" +
            "INSERT INTO sales_order_items " +
            "(id, so_id, description, quantity, unit_price, amount, tax_id, account_id) " +
            "VALUES " +
            "<foreach collection='items' item='item' separator=','>" +
            "(#{item.id}, #{item.so_id}, #{item.description}, #{item.quantity}, " +
            "#{item.unit_price}, #{item.amount}, #{item.tax_id}, #{item.account_id})" +
            "</foreach>" +
            "</script>")
    int batchInsertItems(@Param("items") List<SalesOrderItem> items);

    /**
     * 查询所有销售订单 (带明细)
     */
    @Select("SELECT * FROM sales_orders WHERE book_id = #{bookId} ORDER BY date DESC")
    @Results({
            @Result(property = "id", column = "id", id = true),
            @Result(property = "date", column = "date"),
            @Result(property = "customer_id", column = "customer_id"),
            @Result(property = "description", column = "description"),
            @Result(property = "status", column = "status"),
            // 级联查询明细
            @Result(property = "items", column = "id",
                    many = @Many(select = "com.fGnucash.dao.SalesOrderMapper.findItemsBySoId"))
    })
    List<SalesOrder> findAll(@Param("bookId") String bookId);

    /**
     * 辅助查询：根据主表ID查明细
     */
    @Select("SELECT * FROM sales_order_items WHERE so_id = #{soId}")
    List<SalesOrderItem> findItemsBySoId(String soId);

    /**
     * 根据ID查单个订单 (用于过账前检查)
     */
    @Select("SELECT * FROM sales_orders WHERE id = #{id} AND book_id = #{bookId}")
    @Results({
            @Result(property = "id", column = "id", id = true),
            @Result(property = "items", column = "id", many = @Many(select = "findItemsByOrderId"))
    })
    SalesOrder findById(@Param("id") String id, @Param("bookId") String bookId);

    /**
     * 更新状态 (DRAFT -> POSTED -> PAID)
     */
    @Update("UPDATE sales_orders SET status = #{status} WHERE id = #{id} AND book_id = #{bookId}")
    void updateStatus(@Param("id") String id, @Param("status") String status, @Param("bookId") String bookId);
}
