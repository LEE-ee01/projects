package com.fGnucash.domain;

import java.util.List;

/*****
 * 税项
 * 它代表一个抽象的税种类别。
 * 它只负责定义名字，比如 “增值税” 或 “企业所得税”。
 * 注意：它本身不存具体的税率数值（比如它不存 0.13）
 */
public class Tax {
    private String id;
    private String name;
    // 一对多：一个税种可以包含多个细目
    private List<TaxLine> taxLines;

    public String getId() {
        return id;
    }

    public void setId(String id) {
        this.id = id;
    }

    public String getName() {
        return name;
    }

    public void setName(String name) {
        this.name = name;
    }

    public List<TaxLine> getTaxLines() {
        return taxLines;
    }

    public void setTaxLines(List<TaxLine> taxLines) {
        this.taxLines = taxLines;
    }

    public Tax(String id, String name, List<TaxLine> taxLines) {
        this.id = id;
        this.name = name;
        this.taxLines = taxLines;
    }

    public Tax() {
    }

    @Override
    public String toString() {
        return "Tax{" +
                "id='" + id + '\'' +
                ", name='" + name + '\'' +
                ", taxLines=" + taxLines +
                '}';
    }
}
