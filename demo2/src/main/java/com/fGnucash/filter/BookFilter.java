package com.fGnucash.filter;

import com.fGnucash.common.BookContext;
import org.springframework.core.annotation.Order;
import org.springframework.stereotype.Component;
import jakarta.servlet.*;             // 注意：Spring Boot 3 用 jakarta
import jakarta.servlet.http.HttpServletRequest;
import java.io.IOException;

/**
 * 账套过滤器
 * 拦截请求，解析 Header 中的 X-Book-Id
 */
@Component
@Order(1) // 确保在 CorsFilter 之后 (如果有的话) 或适当的顺序
public class BookFilter implements Filter {

    @Override
    public void doFilter(ServletRequest request, ServletResponse response, FilterChain chain)
            throws IOException, ServletException {
        HttpServletRequest req = (HttpServletRequest) request;

        // 1. 从 Header 获取前端传来的账套ID
        String bookId = req.getHeader("X-Book-Id");

        try {
            // 2. 如果有ID，存入上下文 (排除登录、注册或获取账本列表本身的接口)
            if (bookId != null && !bookId.trim().isEmpty() && !"null".equals(bookId)) {
                BookContext.set(bookId);
            }

            // 3. 放行
            chain.doFilter(request, response);
        } finally {
            // 4. 清理 ThreadLocal，防止内存泄漏
            BookContext.clear();
        }
    }
}