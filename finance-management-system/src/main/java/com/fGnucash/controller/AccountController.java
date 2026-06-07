package com.fGnucash.controller;

import com.fGnucash.domain.Account;
import com.fGnucash.service.AccountService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import java.math.BigDecimal;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/accounts")
public class AccountController {
    @Autowired
    private AccountService accountService;

    /**
     * 1. 获取科目列表
     * 场景 A: 初始化加载根节点 -> GET /accounts
     * 场景 B: 点击展开子节点 -> GET /accounts?parent=1000
     */
    @GetMapping
    public List<Account> getAccounts(@RequestParam(value = "parent", required = false) String parentCode) {
        return accountService.getAccounts(parentCode);
    }

    /**
     * 2. 新增科目
     * URL: POST /accounts
     * Body: { "code": "1003", "name": "支付宝", "type": "ASSET", "parent_code": "1000" }
     */
    @PostMapping
    public Map<String, Object> createAccount(@RequestBody Account account) {
        Map<String, Object> result = new HashMap<>();
        try {
            accountService.createAccount(account);
            result.put("success", true);
            result.put("message", "科目创建成功");
        } catch (Exception e) {
            result.put("success", false);
            result.put("message", "创建失败: " + e.getMessage());
        }
        return result;
    }

    /**
     * 3. 删除科目
     * URL: DELETE /accounts/{code}
     */
    @DeleteMapping("/{code}")
    public Map<String, Object> deleteAccount(@PathVariable("code") String code) {
        Map<String, Object> result = new HashMap<>();
        try {
            accountService.deleteAccount(code);
            result.put("success", true);
            result.put("message", "科目删除成功");
        } catch (Exception e) {
            result.put("success", false);
            result.put("message", "删除失败: " + e.getMessage());
        }
        return result;
    }

    /**
     * 4. 查询科目余额 (✨ 新增功能)
     * URL: GET /accounts/{code}/balance
     * 作用: 实时计算该科目的净余额
     */
    @GetMapping("/{code}/balance")
    public Map<String, Object> getBalance(@PathVariable("code") String code) {
        Map<String, Object> result = new HashMap<>();
        try {
            BigDecimal balance = accountService.getAccountBalance(code);
            result.put("success", true);
            result.put("code", code);
            result.put("balance", balance);
        } catch (Exception e) {
            result.put("success", false);
            result.put("message", "查询失败: " + e.getMessage());
        }
        return result;
    }
}
