package com.fGnucash.controller;

import com.fGnucash.domain.SalesOrder;
import com.fGnucash.service.SalesOrderService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/sales-orders")
public class SalesOrderController {
    @Autowired
    private SalesOrderService salesOrderService;

    /**
     * 1. 录入销售订单 (草稿)
     * URL: POST /sales-orders
     */
    @PostMapping
    public Map<String, Object> createOrder(@RequestBody SalesOrder order) {
        Map<String, Object> result = new HashMap<>();
        try {
            salesOrderService.createOrder(order);
            result.put("success", true);
            result.put("message", "销售单创建成功");
            result.put("id", order.getId());
        } catch (Exception e) {
            e.printStackTrace();
            result.put("success", false);
            result.put("message", "创建失败: " + e.getMessage());
        }
        return result;
    }

    /**
     * 2. 查询列表
     * URL: GET /sales-orders
     */
    @GetMapping
    public List<SalesOrder> getAllOrders() {
        return salesOrderService.getAllOrders();
    }

    /**
     * 3. 查询详情
     * URL: GET /sales-orders/{id}
     */
    @GetMapping("/{id}")
    public SalesOrder getOrderById(@PathVariable("id") String id) {
        return salesOrderService.getOrderById(id);
    }

    /**
     * 4. 销售过账 (确认收入 + 应收债权)
     * URL: POST /sales-orders/{id}/post
     */
    @PostMapping("/{id}/post")
    public Map<String, Object> postOrder(@PathVariable("id") String id) {
        Map<String, Object> result = new HashMap<>();
        try {
            salesOrderService.postOrder(id);
            result.put("success", true);
            result.put("message", "过账成功！已生成收入凭证。");
        } catch (Exception e) {
            e.printStackTrace();
            result.put("success", false);
            result.put("message", "过账失败: " + e.getMessage());
        }
        return result;
    }

    /**
     * 5. 收款 (资金回笼)
     * URL: POST /sales-orders/{id}/payment
     * Body: { "bankAccountId": "1002" }  <-- 这里可以填银行(1002)也可以填现金(1001)
     */
    @PostMapping("/{id}/payment")
    public Map<String, Object> receivePayment(@PathVariable("id") String id,
                                              @RequestBody Map<String, String> params) {
        Map<String, Object> result = new HashMap<>();
        try {
            String bankAccountId = params.get("bankAccountId");
            if (bankAccountId == null) {
                throw new IllegalArgumentException("请指定收款账户 (bankAccountId)");
            }

            salesOrderService.receivePayment(id, bankAccountId);

            result.put("success", true);
            result.put("message", "收款成功！订单已结清。");
        } catch (Exception e) {
            e.printStackTrace();
            result.put("success", false);
            result.put("message", "收款失败: " + e.getMessage());
        }
        return result;
    }


}
