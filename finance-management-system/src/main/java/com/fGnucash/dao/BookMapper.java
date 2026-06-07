package com.fGnucash.dao;


import com.fGnucash.domain.Book;
import org.apache.ibatis.annotations.*;
import java.util.List;

@Mapper
public interface BookMapper {
    @Select("SELECT * FROM books ORDER BY created_at DESC")
    List<Book> findAll();

    @Insert("INSERT INTO books (id, name, created_at) VALUES (#{id}, #{name}, #{createdAt})")
    void insert(Book book);

    @Delete("DELETE FROM books WHERE id = #{id}")
    void delete(String id);
}