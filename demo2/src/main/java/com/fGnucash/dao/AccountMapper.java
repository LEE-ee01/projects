package com.fGnucash.dao;

import com.fGnucash.domain.Account;
import org.apache.ibatis.annotations.Delete;
import org.apache.ibatis.annotations.Insert;
import org.apache.ibatis.annotations.Param;
import org.apache.ibatis.annotations.Select;
import org.springframework.stereotype.Repository;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.List;

/****
 * 用来对科目管理，删除、新建、展开科目
 *
 */
@Repository
public interface AccountMapper {
    // 1. 新建科目
    @Insert("INSERT INTO accounts (code, name, type, parent_code, book_id) " +
            "VALUES (#{code}, #{name}, #{type}, #{parent_code}, #{bookId})")
    void insert(Account account);

    // 2. 删除科目
    @Delete("DELETE FROM accounts WHERE code = #{code} AND book_id = #{bookId}")
    void deleteByCode(@Param("code") String code, @Param("bookId") String bookId);

    // 3. 展开科目：查它的儿子们 (根据 parent_code)
    @Select("SELECT * FROM accounts WHERE parent_code = #{parentCode} AND book_id = #{bookId}")
    List<Account> findByParentCode(@Param("parentCode") String parentCode, @Param("bookId") String bookId);

    // 4. 查顶级科目 (parent_code 为空的那些，作为树的根)
    @Select("SELECT * FROM accounts WHERE parent_code IS NULL AND book_id = #{bookId}")
    List<Account> findRootAccounts(@Param("bookId") String bookId);
    // 5. 查单个科目 (用于校验是否存在)
    @Select("SELECT * FROM accounts WHERE code = #{code} AND book_id = #{bookId}")
    Account findByCode(@Param("code") String code, @Param("bookId") String bookId);

    /**
     * 制作报表用
     * 作用：查出数据库里所有的科目，按代码排序
     * 用于：后续 Service 层遍历计算每个科目的余额
     */
    @Select("SELECT * FROM accounts WHERE book_id = #{bookId}")
    List<Account> findAll(@Param("bookId") String bookId);

    /**
     * 查找特定类型的科目,查找损益科目 (用于期末结账)
     * 场景：结账时，只查 INCOME 和 EXPENSE
     * XML配置或注解：SELECT * FROM accounts WHERE type IN ('INCOME', 'EXPENSE')
     */
    @Select("SELECT * FROM accounts WHERE (type = 'INCOME' OR type = 'EXPENSE') AND book_id = #{bookId}")
    List<Account> findPnLAccounts(@Param("bookId") String bookId);

    /**
     * ✅ 新增：查询某科目在指定日期范围内的发生额合计 (用于利润表)
     * 注意：这里假设你的 splits 表关联了 transactions 表 (t)，且 account 表关联了 splits 表 (s)
     * 如果你的表结构不同，请根据实际情况调整 JOIN 语句
     */
    @Select("SELECT COALESCE(SUM( " +
            "  CASE " +
            "    WHEN s.direction = '借方' THEN s.amount " +
            "    WHEN s.direction = '贷方' THEN -s.amount " +
            "    ELSE 0 " +
            "  END " +
            "), 0) " +
            "FROM splits s " +
            "JOIN transactions t ON s.transaction_id = t.id " +
            "WHERE s.account_id = #{code} " +
            "AND t.book_id = #{bookId} " +
            "AND t.date >= #{startDate} AND t.date <= #{endDate}")
    BigDecimal getPeriodBalance(@Param("code") String code,
                                @Param("bookId") String bookId,
                                @Param("startDate") LocalDate startDate,
                                @Param("endDate") LocalDate endDate);
}


