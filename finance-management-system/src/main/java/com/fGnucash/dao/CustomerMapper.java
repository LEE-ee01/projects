package com.fGnucash.dao;

import com.fGnucash.domain.Customer;
import org.apache.ibatis.annotations.*;
import org.springframework.stereotype.Repository;

import java.util.List;
@Repository
public interface CustomerMapper {
    /***
     * 新增客户
     * @param customer
     * @return
     */
    @Insert("INSERT INTO customers (id, name, book_id) VALUES (#{id}, #{name}, #{bookId})")
    void insert(Customer customer);

    /***
     * 查询所有客户，一个列表
     * @return
     */
    @Select("SELECT * FROM customers WHERE book_id = #{bookId}")
    List<Customer> findAll(@Param("bookId") String bookId);

    /***
     * 根据客户id查询客户
     * @param id
     * @return
     */
    @Select("SELECT * FROM customers WHERE id = #{id} AND book_id = #{bookId}")
    Customer findById(@Param("id") String id, @Param("bookId") String bookId);

    /***
     * 根据客户名字查询客户
     * @param name
     * @return
     */
    @Select("SELECT * FROM customers WHERE name = #{name} AND book_id = #{bookId}")
    Customer findByName(@Param("name") String name, @Param("bookId") String bookId);

    /***
     * 删除客户
     * @param id
     * @return
     */
    @Delete("DELETE FROM customers WHERE id = #{id} AND book_id = #{bookId}")
    void deleteById(@Param("id") String id, @Param("bookId") String bookId);
    /**
     * 更新客户信息
     */
    @Update("UPDATE customers SET name = #{name} WHERE id = #{id} AND book_id = #{bookId}")
    void update(Customer customer);
    // ✅ 修正：查重时必须带上 book_id，否则不同账套不能叫同一个名字


    
}
