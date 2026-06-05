package com.fGnucash.dao;

import com.fGnucash.domain.Splits;
import com.fGnucash.domain.Transaction;
import org.apache.ibatis.annotations.*;
import org.springframework.stereotype.Repository;

import java.util.List;

/****
 * 这是复式记账的mapper
 */
@Repository
public interface TransactionMapper {
    // 1. 保存交易头信息
    @Insert("INSERT INTO transactions (id, date, description, book_id) " +
            "VALUES (#{id}, #{date}, #{description}, #{bookId})")
    int saveTransaction(Transaction transaction);

    // 2. 批量保存分项 (使用 <script> 包裹动态 SQL)
    @Insert("<script>" +
            "INSERT INTO splits (id, transaction_id, account_id, amount, direction, description) " +
            "VALUES " +
            "<foreach collection='splits' item='split' separator=','>" +
            "(#{split.id}, #{split.transactionId}, #{split.accountId}, #{split.amount}, " +
            "#{split.direction, typeHandler=com.fGnucash.domain.DirectionTypeHandler}, " +
            "#{split.description})" +
            "</foreach>" +
            "</script>")
    int batchSaveSplits(@Param("splits") List<Splits> splits);



    /**
     * 新增：查询所有交易（带分项明细）
     * 1. 先执行 SELECT * FROM transactions
     * 2. 对每一行结果，拿着 column="id" (交易ID)
     * 3. 去调用 select="..." 指定的方法 (SplitMapper.findByTransactionId)
     * 4. 把查回来的 List<Split> 塞给 property="splits"
     */
    @Select("SELECT * FROM transactions WHERE book_id = #{bookId} ORDER BY date DESC")
    @Results({
            @Result(property = "id", column = "id", id = true),
            @Result(property = "date", column = "date"),
            @Result(property = "description", column = "description"),
            @Result(property = "bookId", column = "book_id"),
            // 子查询：查分录
            @Result(property = "splits", column = "id",
                    many = @Many(select = "com.fGnucash.dao.SplitMapper.findByTransactionId"))
    })
    List<Transaction> findAll(@Param("bookId") String bookId);

    //查询一个transaction
    @Select("SELECT * FROM transactions where id = #{id}")
    Transaction findTransaction(String id);
    @Select("SELECT * FROM transactions WHERE id = #{id} AND book_id = #{bookId}")
    Transaction findById(@Param("id") String id, @Param("bookId") String bookId);

}
