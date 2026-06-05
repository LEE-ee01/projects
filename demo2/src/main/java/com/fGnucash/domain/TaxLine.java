package com.fGnucash.domain;

import java.math.BigDecimal;

/****
 * 某一个税项
 * 它代表这个税种下具体的、可执行的税率条目。
 * 它存储了具体的税率，比如 “13% 进项税”、“6% 服务业税”、“小规模纳税人 3%”。
 * 它必须属于某一个 Tax
 */
public class TaxLine {
    private String id;
    private String taxId;
    private String name;

    // 税率使用 BigDecimal 保证计算精度
    private BigDecimal rate;

    @Override
    public String toString() {
        return "TaxLine{" +
                "id='" + id + '\'' +
                ", taxId='" + taxId + '\'' +
                ", name='" + name + '\'' +
                ", rate=" + rate +
                '}';
    }

    public TaxLine() {
    }

    public String getId() {
        return id;
    }

    public void setId(String id) {
        this.id = id;
    }

    public String getTaxId() {
        return taxId;
    }

    public void setTaxId(String taxId) {
        this.taxId = taxId;
    }

    public String getName() {
        return name;
    }

    public void setName(String name) {
        this.name = name;
    }

    public BigDecimal getRate() {
        return rate;
    }

    public void setRate(BigDecimal rate) {
        this.rate = rate;
    }

    public TaxLine(String id, String taxId, String name, BigDecimal rate) {
        this.id = id;
        this.taxId = taxId;
        this.name = name;
        this.rate = rate;
    }
}
