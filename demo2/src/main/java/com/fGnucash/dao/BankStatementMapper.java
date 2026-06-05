package com.fGnucash.dao;

import com.fGnucash.domain.BankStatement;
import org.apache.ibatis.annotations.Insert;
import org.apache.ibatis.annotations.Param;
import org.apache.ibatis.annotations.Select;
import org.apache.ibatis.annotations.Update;
import org.springframework.stereotype.Repository;

import java.util.List;
@Repository
public interface BankStatementMapper {
    // 插入银行流水
    @Insert("INSERT INTO bank_statements (id, date, amount, description, status) " +
            "VALUES (#{id}, #{date}, #{amount}, #{description}, #{status})")
    int insert(BankStatement stmt);

    // 查询所有未对账的记录 (用于跑算法)
    @Select("SELECT * FROM bank_statements WHERE status = 'UNMATCHED'")
    List<BankStatement> findUnmatched();

    // 更新对账状态 (连连看成功后调用)
    @Update("UPDATE bank_statements SET status = 'MATCHED', matched_split_id = #{matched_split_id} " +
            "WHERE id = #{id}")
    int markMatched(@Param("id") String id, @Param("matched_split_id") String splitId);
}
