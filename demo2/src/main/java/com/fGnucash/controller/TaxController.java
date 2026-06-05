package com.fGnucash.controller;

import com.fGnucash.domain.Tax;
import com.fGnucash.service.TaxService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/taxes")
public class TaxController {
    @Autowired
    private TaxService taxService;

    /**
     * 1. 获取所有税种 (含细目)
     * URL: GET /taxes
     * 场景：前端在录入订单时，下拉框展示 "增值税", "消费税" 等选项
     * 生成树结构，和会计科目形式差不多
     */
    @GetMapping
    public List<Tax> getAllTaxes() {
        return taxService.getAllTaxes();
    }

    /**
     * 2. 新建税种
     * URL: POST /taxes
     * Body (JSON): 包含主表信息和细目列表
     */
    @PostMapping
    public Map<String, Object> createTax(@RequestBody Tax tax) {
        Map<String, Object> result = new HashMap<>();
        try {
            taxService.createTax(tax);
            result.put("success", true);
            result.put("message", "税种创建成功");
            result.put("id", tax.getId());
        } catch (Exception e) {
            e.printStackTrace();
            result.put("success", false);
            result.put("message", "创建失败: " + e.getMessage());
        }
        return result;
    }
}
