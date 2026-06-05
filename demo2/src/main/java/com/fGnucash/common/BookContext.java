package com.fGnucash.common;

/**
 * 账套上下文容器
 * 使用 ThreadLocal 存储当前请求对应的 bookId
 */
public class BookContext {
    private static final ThreadLocal<String> currentBookId = new ThreadLocal<>();

    public static void set(String bookId) {
        currentBookId.set(bookId);
    }

    public static String get() {
        return currentBookId.get();
    }

    public static void clear() {
        currentBookId.remove();
    }
}