package com.fGnucash.controller;

import com.fGnucash.domain.Customer;
import com.fGnucash.service.CustomerService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/customers")
public class CustomerController {
    @Autowired
    private CustomerService customerService;

    /**
     * 1. 获取所有客户列表
     * URL: GET /customers
     * 作用: 用于前端下拉框选择客户，或展示客户名录
     * @return 客户对象列表
     */
    @GetMapping
    public List<Customer> getAllCustomers() {
        return customerService.getAllCustomers();
    }

    /**
     * 2. 新增客户
     * URL: POST /customers
     * 作用: 创建一个新的客户档案
     * @param customer 请求体 JSON，例如 { "name": "腾讯科技" }
     * @return 包含操作结果和新生成ID的 Map
     */
    @PostMapping
    public Map<String, Object> createCustomer(@RequestBody Customer customer) {
        Map<String, Object> result = new HashMap<>();
        try {
            customerService.createCustomer(customer);
            result.put("success", true);
            result.put("message", "客户创建成功");
            result.put("id", customer.getId());
        } catch (Exception e) {
            // 捕获如“名称重复”等异常
            result.put("success", false);
            result.put("message", "创建失败: " + e.getMessage());
        }
        return result;
    }

    /**
     * 3. 删除客户
     * URL: DELETE /customers/{id}
     * 作用: 根据 ID 删除指定客户
     * @param id 路径参数，要删除的客户ID
     * @return 操作结果
     */
    @DeleteMapping("/{id}")
    public Map<String, Object> deleteCustomer(@PathVariable("id") String id) {
        Map<String, Object> result = new HashMap<>();
        try {
            customerService.deleteCustomer(id);
            result.put("success", true);
            result.put("message", "删除成功");
        } catch (Exception e) {
            result.put("success", false);
            result.put("message", "删除失败: " + e.getMessage());
        }
        return result;
    }

    /**
     * 4. 修改客户信息
     * URL: PUT /customers/{id}
     * 作用: 更新客户名称等信息
     * @param id 路径参数，要修改的客户ID
     * @param customer 请求体 JSON，包含新的信息，例如 { "name": "腾讯集团" }
     * @return 操作结果
     */
    @PutMapping("/{id}")
    public Map<String, Object> updateCustomer(@PathVariable("id") String id,
                                              @RequestBody Customer customer) {
        Map<String, Object> result = new HashMap<>();
        try {
            // 确保 ID 一致性，把路径上的 ID 填入对象
            customer.setId(id);

            customerService.updateCustomer(customer);

            result.put("success", true);
            result.put("message", "修改成功");
        } catch (Exception e) {
            result.put("success", false);
            result.put("message", "修改失败: " + e.getMessage());
        }
        return result;
    }
}
