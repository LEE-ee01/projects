package com.fGnucash.service;

import com.fGnucash.dao.SupplierMapper;
import com.fGnucash.domain.Supplier;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.bind.annotation.GetMapping;
import com.fGnucash.common.BookContext;
import java.util.List;
import java.util.UUID;
@Service
public class SupplierService {
    @Autowired
    private SupplierMapper supplierMapper;
    // ✅ 辅助方法：获取当前账套ID
    private String getCurrentBookId() {
        String bookId = BookContext.get();
        if (bookId == null) {
            throw new RuntimeException("操作失败：未选择账套！");
        }
        return bookId;
    }
    /**
     * 新增供应商
     */
    @Transactional
    public void createSupplier(Supplier supplier) {
        String bookId = getCurrentBookId();

        // 1. 校验名称重复 (只在当前账套内查重)
        if (supplierMapper.findByName(supplier.getName(), bookId) != null) {
            throw new IllegalArgumentException("当前账套下供应商已存在: " + supplier.getName());
        }

        // 2. 生成 ID
        if (supplier.getId() == null || supplier.getId().trim().isEmpty()) {
            supplier.setId(UUID.randomUUID().toString());
        }

        // 3. 设置 bookId
        supplier.setBookId(bookId);

        supplierMapper.insert(supplier);
    }

    /**
     * 获取所有供应商
     */
    public List<Supplier> getAllSuppliers() {
        return supplierMapper.findAll(getCurrentBookId());
    }

    /**
     * 删除供应商
     * (后期这里需要加校验：如果该供应商已经有采购订单，禁止删除)
     */
    @Transactional
    public void deleteSupplier(String id) {
        // 未来可以加校验：检查该供应商在 purchase_orders 表里是否有订单 (也要带 bookId 查)
        supplierMapper.deleteById(id, getCurrentBookId());
    }
    /**
     * ✅ 新增：更新供应商
     */
    @Transactional
    public void updateSupplier(Supplier supplier) {
        String bookId = getCurrentBookId();
        supplier.setBookId(bookId); // 确保是在当前账套下操作

        // 1. 校验参数
        if (supplier.getId() == null || supplier.getName() == null) {
            throw new IllegalArgumentException("参数不完整");
        }

        // 2. 查重校验 (如果改了名字，要看新名字是不是已经被别人占用了)
        Supplier existing = supplierMapper.findByName(supplier.getName(), bookId);
        if (existing != null && !existing.getId().equals(supplier.getId())) {
            // 如果查到了同名的，且那个同名的 ID 不是我自己的 ID，说明重名了
            throw new IllegalArgumentException("供应商名称已存在: " + supplier.getName());
        }

        // 3. 执行更新
        int rows = supplierMapper.update(supplier);
        if (rows == 0) {
            throw new RuntimeException("更新失败：未找到该供应商或无权修改");
        }
    }
}
