package com.fGnucash.controller;

import com.fGnucash.domain.PurchaseOrder;
import com.fGnucash.service.PurchaseOrderService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/purchase-orders")
public class PurchaseOrderController {
    @Autowired
    private PurchaseOrderService poService;

    /**
     * 1. 录入采购订单
     * URL: POST /purchase-orders
     * Body: JSON (包含 items 数组)
     */
    @PostMapping
    public Map<String, Object> createOrder(@RequestBody PurchaseOrder order) {
        Map<String, Object> result = new HashMap<>();
        try {
            // 这里调用 Service，order 里的 items 已经被 Spring 自动填好了
            poService.createOrder(order);

            result.put("success", true);
            result.put("message", "订单创建成功");
            result.put("id", order.getId());
        } catch (Exception e) {
            e.printStackTrace(); // 方便调试
            result.put("success", false);
            result.put("message", "创建失败: " + e.getMessage());
        }
        return result;
    }

    /**
     * 2. 查询订单列表 (含明细)
     * URL: GET /purchase-orders
     */
    @GetMapping
    public List<PurchaseOrder> getAllOrders() {
        return poService.getAllOrders();
    }

    /**
     * 3. 查询单个订单详情
     * URL: GET /purchase-orders/{id}
     */
    @GetMapping("/{id}")
    public PurchaseOrder getOrderById(@PathVariable("id") String id) {
        return poService.getOrderById(id);
    }

    /**
     * 4. ✅ 核心补充：订单过账接口
     * URL: POST /purchase-orders/{id}/post
     * 作用：把草稿变成会计凭证
     */
    @PostMapping("/{id}/post")
    public Map<String, Object> postOrder(@PathVariable("id") String id) {
        Map<String, Object> result = new HashMap<>();
        try {
            poService.postOrder(id);
            result.put("success", true);
            result.put("message", "过账成功！已生成会计凭证。");
        } catch (Exception e) {
            e.printStackTrace();
            result.put("success", false);
            result.put("message", "过账失败: " + e.getMessage());
        }
        return result;
    }

    /**
     * 5. 支付订单
     * URL: POST /purchase-orders/{id}/pay
     * Body: { "bankAccountId": "1002" }
     */
    @PostMapping("/{id}/pay")
    public Map<String, Object> payOrder(@PathVariable("id") String id, @RequestBody Map<String, String> params) {
        Map<String, Object> result = new HashMap<>();
        try {
            // 从请求体里拿到付款账户，如果没有传，默认用 1001 (库存现金) 或报错
            String bankAccountId = params.get("bankAccountId");
            if (bankAccountId == null) {
                // 这里为了演示方便，如果没传就报错，或者你可以默认 "1002"
                throw new IllegalArgumentException("请指定付款账户 (bankAccountId)");
            }

            poService.payOrder(id, bankAccountId);

            result.put("success", true);
            result.put("message", "付款成功！订单已结清。");
        } catch (Exception e) {
            e.printStackTrace();
            result.put("success", false);
            result.put("message", "付款失败: " + e.getMessage());
        }
        return result;
    }
}
