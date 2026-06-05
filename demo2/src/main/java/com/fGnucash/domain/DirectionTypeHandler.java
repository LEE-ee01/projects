package com.fGnucash.domain;
import org.apache.ibatis.type.BaseTypeHandler;
import org.apache.ibatis.type.JdbcType;
import java.sql.*;
public class DirectionTypeHandler extends BaseTypeHandler<Direction>{
    // 1. 写数据 (Java -> DB): 把枚举转成中文存入
    @Override
    public void setNonNullParameter(PreparedStatement ps, int i, Direction parameter, JdbcType jdbcType) throws SQLException {
        ps.setString(i, parameter.getLabel());
    }

    // 2. 读数据 (DB -> Java): 根据列名读中文，转回枚举
    @Override
    public Direction getNullableResult(ResultSet rs, String columnName) throws SQLException {
        String dbValue = rs.getString(columnName);
        return Direction.fromLabel(dbValue);
    }

    // 3. 读数据 (DB -> Java): 根据下标读中文 (MyBatis 要求实现的另外两个方法)
    @Override
    public Direction getNullableResult(ResultSet rs, int columnIndex) throws SQLException {
        String dbValue = rs.getString(columnIndex);
        return Direction.fromLabel(dbValue);
    }

    @Override
    public Direction getNullableResult(CallableStatement cs, int columnIndex) throws SQLException {
        String dbValue = cs.getString(columnIndex);
        return Direction.fromLabel(dbValue);
    }
}
