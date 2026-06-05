package com.fGnucash.dao;

import com.fGnucash.domain.ExpenseClaim;
import com.fGnucash.domain.ExpenseItem;
import org.apache.ibatis.annotations.*;
import java.util.List;

@Mapper
public interface ExpenseMapper {

    // 查主表，带出子表
    @Select("SELECT id, employee_id as employeeId, date, description, status " +
            "FROM expense_claims WHERE book_id = #{bookId} ORDER BY date DESC")
    @Results({
            @Result(property = "id", column = "id", id = true),
            @Result(property = "items", column = "id", many = @Many(select = "findItemsByClaimId"))
    })
    List<ExpenseClaim> findAll(@Param("bookId") String bookId);

    @Select("SELECT id, employee_id as employeeId, date, description, status " +
            "FROM expense_claims WHERE id = #{id} AND book_id = #{bookId}")
    @Results({
            @Result(property = "id", column = "id", id = true),
            @Result(property = "items", column = "id", many = @Many(select = "findItemsByClaimId"))
    })
    ExpenseClaim findById(@Param("id") String id, @Param("bookId") String bookId);

    @Select("SELECT id, claim_id as claimId, description, account_id as accountId, amount FROM expense_items WHERE claim_id = #{claimId}")
    List<ExpenseItem> findItemsByClaimId(String claimId);

    // 插入
    @Insert("INSERT INTO expense_claims (id, employee_id, date, description, status, book_id) " +
            "VALUES (#{id}, #{employeeId}, #{date}, #{description}, #{status}, #{bookId})")
    void insertClaim(ExpenseClaim claim);

    @Insert("INSERT INTO expense_items (id, claim_id, description, account_id, amount) VALUES (#{id}, #{claimId}, #{description}, #{accountId}, #{amount})")
    void insertItem(ExpenseItem item);

    // 更新状态
    @Update("UPDATE expense_claims SET status = #{status} " +
            "WHERE id = #{id} AND book_id = #{bookId}")
    void updateStatus(@Param("id") String id, @Param("status") String status, @Param("bookId") String bookId);
}