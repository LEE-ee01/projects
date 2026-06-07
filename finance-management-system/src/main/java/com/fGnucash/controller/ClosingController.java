package com.fGnucash.controller;

import com.fGnucash.service.ClosingService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.CrossOrigin;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.HashMap;
import java.util.Map;

@RestController
@RequestMapping("/closing")
public class ClosingController {
    @Autowired
    private ClosingService closingService;
    /**
     * 执行期末结账
     * URL: POST /closing/period-end
     * 作用: 清零所有损益科目，将利润转入权益
     */
    @PostMapping("/period-end")
    public Map<String, Object> performClosing() {
        Map<String, Object> result = new HashMap<>();
        try {
            closingService.performClosing();
            result.put("success", true);
            result.put("message", "期末结账成功！损益科目已清零，利润已结转。");
        } catch (Exception e) {
            e.printStackTrace();
            result.put("success", false);
            result.put("message", "结账失败: " + e.getMessage());
        }
        return result;
    }

}
