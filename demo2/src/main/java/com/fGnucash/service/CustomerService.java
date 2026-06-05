package com.fGnucash.service;

import com.fGnucash.dao.CustomerMapper;
import com.fGnucash.domain.Customer;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import com.fGnucash.common.BookContext;
import java.util.List;
import java.util.UUID;

@Service
public class CustomerService {
    @Autowired
    private CustomerMapper customerMapper;
    // ✅ 辅助方法：获取当前账套ID
    private String getCurrentBookId() {
        String bookId = BookContext.get();
        if (bookId == null) {
            throw new RuntimeException("操作失败：未选择账套！");
        }
        return bookId;
    }
    /****
     * 创建一个客户
     * @param customer
     */
    @Transactional
    public void createCustomer(Customer customer) {
        // 查重
        String bookId = getCurrentBookId();
        if (customerMapper.findByName(customer.getName(),bookId) != null) {
            throw new IllegalArgumentException("客户已存在: " + customer.getName());
        }
        // 生成ID
        if (customer.getId() == null || customer.getId().trim().isEmpty()) {
            customer.setId(UUID.randomUUID().toString());
        }
        customer.setBookId(bookId);
        customerMapper.insert(customer);
    }

    /***
     * 返回所有的客户列表
     * @return
     */
    public List<Customer> getAllCustomers() {
        return customerMapper.findAll(getCurrentBookId());
    }

    /***
     * 根据id删除该客户
     * @param id
     */
    @Transactional
    public void deleteCustomer(String id) {
        customerMapper.deleteById(id, getCurrentBookId());
    }

    /**
     * 修改客户信息
     */
    @Transactional
    public void updateCustomer(Customer customer) {
        String bookId = getCurrentBookId();
        // 1. 校验 ID 是否存在
        if (customerMapper.findById(customer.getId(),bookId) == null) {
            throw new IllegalArgumentException("客户不存在，无法修改 ID: " + customer.getId());
        }

        // 2. 校验名称重复 (排除自己)
        // 逻辑：如果查到了同名的，且那个同名的 ID 不是我自己的 ID，说明名字冲突了
        Customer duplicate = customerMapper.findByName(customer.getName(),bookId);
        if (duplicate != null && !duplicate.getId().equals(customer.getId())) {
            throw new IllegalArgumentException("客户名称已存在: " + customer.getName());
        }
        customer.setBookId(getCurrentBookId());
        // 3. 执行更新
        customerMapper.update(customer);
    }

}
