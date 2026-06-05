package com.fGnucash.service;

import com.fGnucash.dao.TaxMapper;
import com.fGnucash.domain.Tax;
import com.fGnucash.domain.TaxLine;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.UUID;

@Service
public class TaxService {
    @Autowired
    private TaxMapper taxMapper;

    /**
     * 1. 新建税种 (包含细目)
     * 例子：创建一个 "增值税"，下面挂一个 "13%" 的细目
     */
    @Transactional
    public void createTax(Tax tax) {
        // 1. 生成主表 ID
        if (tax.getId() == null) {
            tax.setId(UUID.randomUUID().toString());
        }
        // 保存主表
        taxMapper.insertTax(tax);
        // 2. 处理细目
        if (tax.getTaxLines() != null) {
            for (TaxLine line : tax.getTaxLines()) {
                // 生成细目 ID
                if (line.getId() == null) {
                    line.setId(UUID.randomUUID().toString());
                }
                // 关键：把细目挂在这个税种下面 (设置外键)
                line.setTaxId(tax.getId()); // 注意这里调用的是 setTaxId

                // 保存细目
                taxMapper.insertTaxLine(line);
            }
        }
    }

    /**
     * 2. 获取所有税种 (包含细目)
     * 用于：前端订单录入页面，下拉选择税种
     */
    public List<Tax> getAllTaxes() {
        return taxMapper.findAll();
    }
}
