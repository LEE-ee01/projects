package com.fGnucash.dao;

import com.fGnucash.domain.Supplier;
import org.apache.ibatis.annotations.Delete;
import org.apache.ibatis.annotations.Insert;
import org.apache.ibatis.annotations.Param;
import org.apache.ibatis.annotations.Select;
import org.springframework.stereotype.Repository;

import java.util.List;
@Repository
public interface SupplierMapper {


    // 1. 新建供应商1
    @Insert("INSERT INTO suppliers (id, name, book_id) VALUES (#{id}, #{name}, #{bookId})")
    int insert(Supplier supplier);

    // 2. 查询列表 (供下拉框选择)
    @Select("SELECT * FROM suppliers WHERE book_id = #{bookId} ORDER BY name")
    List<Supplier> findAll(@Param("bookId") String bookId);

    // 3. 根据ID查询 (用于订单回显)
    @Select("SELECT * FROM suppliers WHERE id = #{id} AND book_id = #{bookId}")
    Supplier findById(@Param("id") String id, @Param("bookId") String bookId);

    // 4. 根据名称查询 (用于查重)
    @Select("SELECT * FROM suppliers WHERE name = #{name} AND book_id = #{bookId}")
    Supplier findByName(@Param("name") String name, @Param("bookId") String bookId);

    // 5. 删除
    @Delete("DELETE FROM suppliers WHERE id = #{id} AND book_id = #{bookId}")
    int deleteById(@Param("id") String id, @Param("bookId") String bookId);

    // ✅ 新增：更新供应商信息
    @org.apache.ibatis.annotations.Update("UPDATE suppliers SET name = #{name} WHERE id = #{id} AND book_id = #{bookId}")
    int update(Supplier supplier);
}
