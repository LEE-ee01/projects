package com.fGnucash.controller;

import com.fGnucash.domain.ExpenseClaim;
import com.fGnucash.service.ExpenseService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/expenses")
public class ExpenseController {

    @Autowired
    private ExpenseService expenseService;

    /**
     * 1. 获取所有报销单列表
     * GET /expenses
     */
    @GetMapping
    public List<ExpenseClaim> getAll() {
        return expenseService.getAll();
    }

    /**
     * 2. 创建/提交报销单
     * POST /expenses
     */
    @PostMapping
    public Map<String, Object> create(@RequestBody ExpenseClaim claim) {
        Map<String, Object> res = new HashMap<>();
        try {
            expenseService.create(claim);
            res.put("success", true);
            res.put("message", "报销单提交成功");
        } catch (Exception e) {
            e.printStackTrace();
            res.put("success", false);
            res.put("message", "提交失败: " + e.getMessage());
        }
        return res;
    }

    /**
     * 3. 审核过账
     * POST /expenses/{id}/post
     */
    @PostMapping("/{id}/post")
    public Map<String, Object> post(@PathVariable("id") String id) {
        Map<String, Object> res = new HashMap<>();
        try {
            expenseService.post(id);
            res.put("success", true);
            res.put("message", "审核过账成功");
        } catch (Exception e) {
            e.printStackTrace();
            res.put("success", false);
            res.put("message", "过账失败: " + e.getMessage());
        }
        return res;
    }

    /**
     * 4. 确认支付
     * POST /expenses/{id}/pay
     * Body: { "bankAccountId": "1002" }
     */
    @PostMapping("/{id}/pay")
    public Map<String, Object> pay(@PathVariable("id") String id, @RequestBody Map<String, String> body) {
        Map<String, Object> res = new HashMap<>();
        try {
            // 从请求体中获取付款银行科目ID
            String bankAccountId = body.get("bankAccountId");
            if (bankAccountId == null || bankAccountId.isEmpty()) {
                throw new RuntimeException("请选择付款银行账户");
            }

            expenseService.pay(id, bankAccountId);

            res.put("success", true);
            res.put("message", "支付成功");
        } catch (Exception e) {
            e.printStackTrace();
            res.put("success", false);
            res.put("message", "支付失败: " + e.getMessage());
        }
        return res;
    }
}