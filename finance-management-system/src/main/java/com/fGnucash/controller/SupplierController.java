package com.fGnucash.controller;

import com.fGnucash.domain.Supplier;
import com.fGnucash.service.SupplierService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import java.util.HashMap;
import java.util.List;
import java.util.Map;


@RestController
@RequestMapping("/supplier")
public class SupplierController {
    @Autowired
    private SupplierService supplierService;

    /**
     * 1. 获取列表
     * URL: GET /suppliers
     * 用于形成下拉列表
     */
    @GetMapping
    public List<Supplier> getAllSuppliers() {
        return supplierService.getAllSuppliers();
    }
    /**
     * 2. 新增供应商
     * URL: POST /suppliers
     * Body: { "name": "联想集团" }
     */
    @PostMapping
    public Map<String, Object> createSupplier(@RequestBody Supplier supplier) {
        Map<String, Object> result = new HashMap<>();
        try {
            supplierService.createSupplier(supplier);
            result.put("success", true);
            result.put("message", "供应商创建成功");
            result.put("id", supplier.getId());
        } catch (Exception e) {
            result.put("success", false);
            result.put("message", "创建失败: " + e.getMessage());
        }
        return result;
    }


    /**
     * 3. 删除供应商
     * URL: DELETE /suppliers/{id}
     */
    @DeleteMapping("/{id}")
    public Map<String, Object> deleteSupplier(@PathVariable("id") String id) {
        Map<String, Object> result = new HashMap<>();
        try {
            supplierService.deleteSupplier(id);
            result.put("success", true);
            result.put("message", "供应商删除成功");
        } catch (Exception e) {
            // 捕获异常 (比如以后加了"已被引用无法删除"的校验)
            result.put("success", false);
            result.put("message", "删除失败: " + e.getMessage());
        }
        return result;
    }
    /**
     * ✅ 新增：更新供应商
     * URL: PUT /supplier
     * Body: { "id": "xxx", "name": "新名称" }
     */
    @PutMapping
    public Map<String, Object> updateSupplier(@RequestBody Supplier supplier) {
        Map<String, Object> result = new HashMap<>();
        try {
            supplierService.updateSupplier(supplier);
            result.put("success", true);
            result.put("message", "供应商更新成功");
        } catch (Exception e) {
            result.put("success", false);
            result.put("message", "更新失败: " + e.getMessage());
        }
        return result;
    }
}
