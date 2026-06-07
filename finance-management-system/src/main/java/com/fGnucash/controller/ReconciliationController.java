package com.fGnucash.controller;

import com.fGnucash.service.ReconciliationService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.HashMap;
import java.util.Map;

/***
 * 自动对账
 */
@RestController
@RequestMapping("/reconciliation")
public class ReconciliationController {
    @Autowired
    private ReconciliationService reconciliationService;

    /**
     * 🧠 触发自动对账
     * URL: POST /reconciliation/auto
     * 作用: 扫描未对账的银行流水，尝试在系统内寻找匹配项
     */
    @PostMapping("/auto")
    public Map<String, Object> autoReconcile() {
        Map<String, Object> result = new HashMap<>();
        try {
            // 执行核心算法，返回成功匹配的笔数
            int matchCount = reconciliationService.autoReconcile();

            result.put("success", true);
            result.put("matchCount", matchCount);
            result.put("message", "自动对账完成！成功匹配 " + matchCount + " 笔记录。");
        } catch (Exception e) {
            e.printStackTrace();
            result.put("success", false);
            result.put("message", "对账失败: " + e.getMessage());
        }
        return result;
    }
}
