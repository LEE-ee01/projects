package com.fGnucash.dao;

import com.fGnucash.domain.Employee;
import org.apache.ibatis.annotations.*;

import java.util.List;
@Mapper
public interface EmployeeMapper {
    @Insert("INSERT INTO employees (id, name, department, position, phone, book_id) VALUES (#{id}, #{name}, #{department}, #{position}, #{phone}, #{bookId})")
    void insert(Employee employee);

    @Select("SELECT * FROM employees WHERE book_id = #{bookId}")
    List<Employee> findAll(@Param("bookId") String bookId);

    @Select("SELECT * FROM employees WHERE id = #{id} AND book_id = #{bookId}")
    Employee findById(@Param("id") String id, @Param("bookId") String bookId);

    // ✅ 修正：查重时带上 book_id
    @Select("SELECT * FROM employees WHERE name = #{name} AND book_id = #{bookId}")
    Employee findByName(@Param("name") String name, @Param("bookId") String bookId);

    @Delete("DELETE FROM employees WHERE id = #{id} AND book_id = #{bookId}")
    void deleteById(@Param("id") String id, @Param("bookId") String bookId);

    // ✅ 新增：更新员工信息
    @Update("UPDATE employees SET name = #{name}, department = #{department}, position = #{position}, phone = #{phone} WHERE id = #{id} AND book_id = #{bookId}")
    void update(Employee employee,@Param("bookId") String bookId);
}
