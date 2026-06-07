package com.fGnucash.dao;

import com.fGnucash.domain.Tax;
import com.fGnucash.domain.TaxLine;
import org.apache.ibatis.annotations.*;

import java.util.List;

public interface TaxMapper {
    // 1. 写入操作 (Insert)
    // ==========================================

    /**
     * 新增税务主表 (如 "增值税")
     */
    @Insert("INSERT INTO taxes (id, name) VALUES (#{id}, #{name})")
    int insertTax(Tax tax);

    /**
     * 新增税务细目 (如 "13% 进项税")
     */
    @Insert("INSERT INTO tax_lines (id, tax_id, name, rate) VALUES (#{id}, #{taxId}, #{name}, #{rate})")
    int insertTaxLine(TaxLine taxLine);

    // 2. 查询操作 (Select)
    // ==========================================

    /**
     * 查询所有税种，并自动填充下面的细目列表
     * 原理：
     * 1. 查出 taxes 表所有数据
     * 2. 拿着每一行的 id，去调用 findLinesByTaxId
     * 3. 把结果塞进 taxLines 字段
     */
    @Select("SELECT * FROM taxes")
    @Results({
            @Result(property = "id", column = "id", id = true),
            @Result(property = "name", column = "name"),
            // 关键：一对多关联
            @Result(property = "taxLines", column = "id", many = @Many(select = "com.fGnucash.dao.TaxMapper.findLinesByTaxId"))
    })
    List<Tax> findAll();

    /**
     * 辅助查询：查某个税种下的所有细目
     * 关键修正：因为关闭了驼峰转换，必须用 AS 起别名
     */
    @Select("SELECT id, tax_id AS taxId, name, rate " +
            "FROM tax_lines WHERE tax_id = #{taxId}")
    List<TaxLine> findLinesByTaxId(String taxId);

    /**
     * 根据 ID 查单个细目 (用于后续计算)
     */
    @Select("SELECT id, tax_id AS taxId, name, rate " +
            "FROM tax_lines WHERE id = #{id}")
    TaxLine findLineById(String id);
}
