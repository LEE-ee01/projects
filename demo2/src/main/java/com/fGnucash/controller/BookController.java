package com.fGnucash.controller;

import com.fGnucash.domain.Book;
import com.fGnucash.service.BookService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import java.io.StringReader;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/books")
public class BookController {
    @Autowired
    private BookService bookService;

    @GetMapping
    public List<Book> getAll() {
        return bookService.getAll();
    }

    @PostMapping
    public Map<String, Object> create(@RequestBody Book book) {
        Map<String, Object> res = new HashMap<>();
        try {
            bookService.create(book);
            res.put("success", true);
        } catch (Exception e) {
            res.put("success", false);
            res.put("message", e.getMessage());
        }
        return res;
    }


    @DeleteMapping("/{id}")
    public Map<String, Object> delete(@PathVariable String id) {
        Map<String, Object> res = new HashMap<>();
        try {
            bookService.delete(id);
            res.put("success", true);
        } catch (Exception e) {
            res.put("success", false);
            res.put("message", e.getMessage());
        }
        return res;
    }
}