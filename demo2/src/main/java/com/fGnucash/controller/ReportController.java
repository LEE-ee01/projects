package com.fGnucash.controller;

import com.fGnucash.service.ReportService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.format.annotation.DateTimeFormat;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import java.time.LocalDate;
import java.time.temporal.TemporalAdjusters;
import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/reports")
public class ReportController {
    @Autowired
    private ReportService reportService;

    /**
     * 获取试算平衡表
     * URL: GET /reports/trial-balance
     * 作用: 返回所有非零余额的科目列表
     */
    @GetMapping("/trial-balance")
    public List<Map<String, Object>> getTrialBalance() {
        // 直接调用我们刚写好的 Service
        return reportService.getTrialBalance();
    }

    /**
     * 获取利润表
     * URL: GET /reports/income-statement
     */
//    @GetMapping("/income-statement")
//    public Map<String, Object> getIncomeStatement() {
//        return reportService.getIncomeStatement();
//    }

    /**
     * 获取资产负债表
     * URL: GET /reports/balance-sheet
     */
    @GetMapping("/balance-sheet")
    public Map<String, Object> getBalanceSheet() {
        return reportService.getBalanceSheet();
    }
//    @GetMapping("/balance-sheet")
//    public Map<String, Object> getBalanceSheet(
//            @RequestParam(required = false) @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate asOfDate) {
//
//        // 如果没传日期，默认截止到今天
//        if (asOfDate == null) {
//            asOfDate = LocalDate.now();
//        }
//        return reportService.getBalanceSheet(asOfDate);
//    }

    /**
     * ✅ 升级：获取利润表 (支持日期参数)
     * URL: GET /reports/income-statement?startDate=2023-01-01&endDate=2023-12-31
     */
    @GetMapping("/income-statement")
    public Map<String, Object> getIncomeStatement(
            @RequestParam(required = false) @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate startDate,
            @RequestParam(required = false) @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate endDate) {

        // 如果前端没传日期，默认查当月
        if (startDate == null) startDate = LocalDate.now().with(TemporalAdjusters.firstDayOfMonth());
        if (endDate == null) endDate = LocalDate.now().with(TemporalAdjusters.lastDayOfMonth());

        return reportService.getIncomeStatement(startDate, endDate);
    }
}
