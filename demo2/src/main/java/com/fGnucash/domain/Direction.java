package com.fGnucash.domain;

/****
 * 这是专门用来处理借贷方向的类
 */
public enum Direction {
    DEBIT("借方"),
    CREDIT("贷方");

    // 2. 成员变量，用来存 "借方" 或 "贷方"
    private final String label;

    // 3. ✅ 构造函数 (答案在这里)
    // 枚举的构造函数默认是 private 的，不需要加 public
    Direction(String label) {
        this.label = label;
    }

    // 4. Getter 方法，方便在 Java 代码里获取中文
    public String getLabel() {
        return label;
    }

    // 5. ✅ 静态查找方法 (DB -> Java)
    public static Direction fromLabel(String label) {
        // 遍历所有的枚举项 (DEBIT, CREDIT)
        for (Direction d : Direction.values()) {
            if (d.getLabel().equals(label)) {
                return d;
            }
        }
        return null; // 或者抛出异常，如果数据库里存了不认识的词
    }
}
