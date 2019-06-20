package com.attendance.dreamdemo;

import com.attendance.dreamdemo.domain.User;
import com.attendance.dreamdemo.mapper.UserMapper;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.mybatis.spring.annotation.MapperScan;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.junit4.SpringRunner;
@MapperScan(basePackages = {"com.attendance.dreamdemo.mapper"})
@RunWith(SpringRunner.class)
@SpringBootTest
public class DreamdemoApplicationTests {
    @Autowired
    private UserMapper userMapper;
    @Test
    public void contextLoads() {

        User people =  userMapper.findByName("跳跳");
        System.out.println(people);
    }

}
