package com.fGnucash.service;

import com.fGnucash.common.BookContext;
import com.fGnucash.dao.EmployeeMapper;
import com.fGnucash.domain.Employee;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import java.util.List;
import java.util.UUID;

@Service
public class EmployeeService {

    @Autowired
    private EmployeeMapper employeeMapper;

    public List<Employee> getAllEmployees() {
        return employeeMapper.findAll(getCurrentBookId());
    }
    // ✅ 辅助方法：获取当前账套ID
    private String getCurrentBookId() {
        String bookId = BookContext.get();
        if (bookId == null) {
            throw new RuntimeException("操作失败：未选择账套！");
        }
        return bookId;
    }
    @Transactional
    public void createEmployee(Employee employee) {
        String bookId = getCurrentBookId();

        // 生成ID
        if (employee.getId() == null || employee.getId().trim().isEmpty()) {
            employee.setId(UUID.randomUUID().toString());
        }

        // 绑定账套
        employee.setBookId(bookId);

        employeeMapper.insert(employee);
    }

    @Transactional
    public void deleteEmployee(String id) {
        // 后期可以加校验：如果该员工有未报销的单据，禁止删除
        employeeMapper.deleteById(id, getCurrentBookId());
    }
    /**
     * ✅ 更新员工信息
     */
    @Transactional
    public void updateEmployee(Employee employee) {
        String bookId = getCurrentBookId();
        employee.setBookId(bookId);

        // 1. 校验是否存在
        if (employeeMapper.findById(employee.getId(), bookId) == null) {
            throw new IllegalArgumentException("员工不存在或无权修改");
        }

        // 2. 查重 (排除自己)
        // 如果改了名字，要确保新名字没有和其他人冲突
        Employee duplicate = employeeMapper.findByName(employee.getName(), bookId);
        if (duplicate != null && !duplicate.getId().equals(employee.getId())) {
            throw new IllegalArgumentException("员工姓名已存在: " + employee.getName());
        }

        // 3. 执行更新
        employeeMapper.update(employee,bookId);
    }

}