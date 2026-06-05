package com.fGnucash.controller;

import com.fGnucash.domain.Employee;
import com.fGnucash.service.EmployeeService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.bind.annotation.*;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/employees")
public class EmployeeController {

    @Autowired
    private EmployeeService employeeService;

    @GetMapping
    public List<Employee> getAll() {
        return employeeService.getAllEmployees();
    }

    @PostMapping
    public Map<String, Object> create(@RequestBody Employee employee) {
        Map<String, Object> res = new HashMap<>();
        try {
            employeeService.createEmployee(employee);
            res.put("success", true);
            res.put("message", "员工添加成功");
        } catch (Exception e) {
            res.put("success", false);
            res.put("message", e.getMessage());
        }
        return res;
    }

    @DeleteMapping("/{id}")
    public Map<String, Object> delete(@PathVariable("id") String id) {
        Map<String, Object> res = new HashMap<>();
        try {
            employeeService.deleteEmployee(id);
            res.put("success", true);
            res.put("message", "删除成功");
        } catch (Exception e) {
            res.put("success", false);
            res.put("message", e.getMessage());
        }
        return res;
    }
    /**
     * ✅ 新增：更新员工信息
     * URL: PUT /employees
     */
    @PutMapping
    public Map<String, Object> updateEmployee(@RequestBody Employee employee) {
        Map<String, Object> result = new HashMap<>();
        try {
            employeeService.updateEmployee(employee);
            result.put("success", true);
            result.put("message", "修改成功");
        } catch (Exception e) {
            result.put("success", false);
            result.put("message", "修改失败: " + e.getMessage());
        }
        return result;
    }

}