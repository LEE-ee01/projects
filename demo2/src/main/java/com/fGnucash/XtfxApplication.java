package com.fGnucash;

import org.mybatis.spring.annotation.MapperScan;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.transaction.annotation.EnableTransactionManagement;

@SpringBootApplication
@MapperScan("com.fGnucash.dao") // 扫描MyBatis Mapper接口
@EnableTransactionManagement // 开启事务管理
public class XtfxApplication {
    public static void main(String[] args) {
        SpringApplication.run(XtfxApplication.class, args);
    }
}