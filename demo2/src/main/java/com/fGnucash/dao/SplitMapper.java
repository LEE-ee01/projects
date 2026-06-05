package com.fGnucash.dao;

import com.fGnucash.domain.Splits;
import org.apache.ibatis.annotations.Param;
import org.apache.ibatis.annotations.Result;
import org.apache.ibatis.annotations.Results;
import org.apache.ibatis.annotations.Select;
import org.springframework.stereotype.Repository;

import java.math.BigDecimal;
import java.util.Date;
import java.util.List;

@Repository
public interface SplitMapper{
    /**
     * 核心功能 1: 查询某科目的明细账
     * 场景：用户点开“银行存款”，想看流水
     */
    @Select("SELECT * FROM splits WHERE account_id = #{accountId}")
    List<Splits> findByAccountId(String accountId);

    /**
     * 核心功能 2: 通过交易ID查分项
     * 场景：查询交易详情时，需要把它的分项补全
     */
    @Select("SELECT * FROM splits WHERE transaction_id = #{transactionId}")
    List<Splits> findByTransactionId(String transactionId);

    /**
     * 核心功能 3: 检查科目是否被使用
     * 场景：AccountService 删除科目时的校验（之前我们是在 AccountMapper 里随便写的，其实放这里更合适）
     */
    @Select("SELECT count(*) FROM splits WHERE account_id = #{accountId}")
    int countByAccountId(String accountId);

    /**
     * 4. 计算某科目的“净借方余额” (Total Debit - Total Credit)
     * 逻辑：如果 direction 是 '借方'，就加；如果是 '贷方'，就减。
     * IFNULL 是为了防止如果没有记录，返回 null 导致报错，给个 0。
     */
    @Select("SELECT COALESCE(SUM( " +
            "  CASE " +
            "    WHEN s.direction = '借方' THEN s.amount " +
            "    WHEN s.direction = '贷方' THEN -s.amount " +
            "    ELSE 0 " +
            "  END " +
            "), 0) " +
            "FROM splits s " +
            "JOIN transactions t ON s.transaction_id = t.id " + // 👈 关键 JOIN
            "WHERE s.account_id = #{accountId} " +
            "AND t.book_id = #{bookId}")                        // 👈 关键过滤
    BigDecimal calculateNetDebitBalance(@Param("accountId") String accountId, @Param("bookId") String bookId);

    /**
     * 🔍 对账核心查询
     * 寻找符合条件的系统分录
     * @param accountId  目标科目 (如 1002 银行存款)
     * @param amount     目标金额 (必须完全相等)
     * @param startDate  开始日期 (如: 交易日 - 3天)
     * @param endDate    结束日期 (如: 交易日 + 3天)
     */
    @Select("SELECT s.* FROM splits s " +
            "JOIN transactions t ON s.transaction_id = t.id " +
            "WHERE s.account_id = #{accountId} " +
            "AND s.amount = #{amount} " +
            "AND t.book_id = #{bookId} " + // 👈 关键过滤
            "AND t.date BETWEEN #{startDate} AND #{endDate} " +
            "LIMIT 1")
    @Results({
            @Result(property = "accountId", column = "account_id"),
            @Result(property = "transactionId", column = "transaction_id"),
            @Result(property = "direction", column = "direction", typeHandler = com.fGnucash.domain.DirectionTypeHandler.class)
    })
    Splits findPotentialMatch(@Param("accountId") String accountId,
                              @Param("amount") BigDecimal amount,
                              @Param("startDate") Date startDate,
                              @Param("endDate") Date endDate,
                              @Param("bookId") String bookId);
}
