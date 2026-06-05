package com.fGnucash.controller;


import com.fGnucash.domain.Transaction;
import com.fGnucash.service.TransactionService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/transactions")
public class TransactionController {
    @Autowired
    private TransactionService transactionService;

    /**
     * 1. 录入交易 (复式记账)
     * URL: POST /transactions
     * Body: JSON (见下文示例)
     */
    @PostMapping
    public Map<String, Object> saveTransaction(@RequestBody Transaction transaction) {
        Map<String, Object> result = new HashMap<>();
        try {
            transactionService.saveTransaction(transaction);
            result.put("success", true);
            result.put("message", "交易录入成功");
            result.put("id", transaction.getId()); // 返回生成的 ID
        } catch (Exception e) {
            // 捕获 "试算不平衡" 等异常
            e.printStackTrace(); // 建议在控制台打印堆栈，方便调试
            result.put("success", false);
            result.put("message", "录入失败: " + e.getMessage());
        }
        System.out.println("测试————————————————————————————————————");
        return result;
    }
    /**
     * 2. 查询交易列表 (带分项明细)
     * URL: GET /transactions
     */
    @GetMapping
    public List<Transaction> listTransactions() {
        return transactionService.getTransactionList();
    }

    /**
     * 测试接口 - 用于验证应用是否正常运行
     * URL: GET /transactions/test
     */
    @GetMapping("/test")
    public Map<String, Object> test() {
        Map<String, Object> result = new HashMap<>();
        result.put("status", "success");
        result.put("message", "应用正常运行");
        result.put("timestamp", System.currentTimeMillis());
        return result;
    }

}
