# Stack Memory Anatomy - 堆栈内存剖析



:::{figure-md} 图： JVM 堆栈内存剖析

<img src="mem-layout-r3.drawio.svg" alt="图： JVM 堆栈内存剖析">

*图： JVM 堆栈内存剖析*
:::
*[用 Draw.io 打开](https://app.diagrams.net/?ui=sketch#Uhttps%3A%2F%2Fjvm-insider.mygraphql.com%2Fzh-cn%2Flatest%2F_images%2Fmem-layout-r3.drawio.svg)*


## 实验环境准备

1. JDK 需要支持 hsdis 
2. Java 程序
3. Java Options
4. 保存现场
5. 启动 debugger

### JDK 支持 hsdis

> 如需要分析 JVM 编译生成的代码，可以通过 `-XX:+PrintAssembly` java 参数让 JVM 以汇编为格式，输出 JIT 编译后的程序到日志文件。使用说明见： https://wiki.openjdk.org/display/HotSpot/PrintAssembly 。
> `-XX:+PrintAssembly` 基于 hsdis 技术，需要 jdk 在构建期就支持 hsdis。
> 另外，其实 JDK 自带的 jhsdb 也可以实时反编译 JIT 生成的机器指令。所以 hsdis 有时不是必须的。但如果你希望得到注释比较丰富（如函数 call 地址后显示函数名），可读性高，可用 [jitwatch](https://github.com/AdoptOpenJDK/jitwatch) GUI 分析的汇编代码，那么支持 hsdis 是必须的。

JVM 支持 hsdis 的准备工作参见： {ref}`appendix-lab-env/build-jdk/build-slow-debug-jdk:hsdis 工具分析 JVM 编译生成的代码`



### Java 程序

```java
public class SimpleObj {

    public static TestStaticObjA testStaticObj = new TestStaticObjA();

    public static void main(String[] args) throws InterruptedException {
        TestObjA testObjA = new TestObjA();
        System.out.println("Hello SimpleObj: " + ProcessHandle.current().pid());
        Thread.currentThread().sleep(1000*1000*1000);
    }
}

public class TestObjA {
    public int testObjInt1;
    TestObjB testObjB = new TestObjB();
}


public class TestObjB {
    public int testObjInt;
}

public class TestStaticObjA {
    public int testObjInt;
}

```

### Java Options


```bash
setarch $(uname -m) --addr-no-randomize /home/labile/opensource/jdk/build/linux-x86_64-server-slowdebug-hsdis/jdk/bin/java -server -XX:+UseSerialGC -XX:+PreserveFramePointer -Xcomp -XX:-TieredCompilation -XX:-BackgroundCompilation -XX:-UseCompressedOops -XX:+UnlockDiagnosticVMOptions -XX:+PrintAssembly -XX:PrintAssemblyOptions=intel -XX:CompileCommand=dontinline -Xlog:class+load=info -XX:+LogCompilation -XX:LogFile=./round3/mylogfile.log -XX:+DebugNonSafepoints -XX:+PrintInterpreter  -cp . SimpleObj 
```

想看每个 Options 的描述，可以在 [VM Options Explorer - OpenJDK11 HotSpot](https://chriswhocodes.com/vm-options-explorer.html) 中找到。但要看深入的内容，还得自己搜索。

其中：
 - `setarch $(uname -m) --addr-no-randomize` 是为了禁用 [Address space layout randomization (ASLR)](https://en.wikipedia.org/wiki/Address_space_layout_randomization) 。以让多次重启 Java 进程时，内存地址尽量一致。
 - `-XX:+PreserveFramePointer` 是为了 stack 和 CPU 寄存器的使用 与 gdb 兼容，让 gdb 可以正确识别出线程的 stack 。 详见： [Java Mixed-Mode
Flame Graphs - Brendan Gregg](https://www.brendangregg.com/Slides/JavaOne2015_MixedModeFlameGraphs.pdf)
 - `-Xcomp -XX:-TieredCompilation -XX:-BackgroundCompilation` 让代码跳过 interpreter 直接 JIT 编译。因为本节的重点是 JIT 。
 - `-XX:+PrintAssembly -XX:PrintAssemblyOptions=intel -XX:CompileCommand=dontinline -Xlog:class+load=info -XX:+LogCompilation -XX:LogFile=./round3/mylogfile.log -XX:+DebugNonSafepoints -XX:+PrintInterpreter` 这些参数目的是保存 JIT 汇编输出。对于本节实验这是可选的。参数使用说明见： https://wiki.openjdk.org/display/HotSpot/PrintAssembly

### 保存现场


```bash
# Save memory region list
pmap -X $JAVA_PID > /home/labile/opensource/jdk/jvm-insider/simple-object/round3/pmap.txt
pmap -XX $JAVA_PID | tee /home/labile/opensource/jdk/jvm-insider/simple-object/round3/pmapXX.txt
# save thread id to thread name mapping
ps  -T -p $JAVA_PID | tee /home/labile/opensource/jdk/jvm-insider/simple-object/round3/threads.txt
```

保存 core dump :
```bash
sudo gdb -p $JAVA_PID
(gdb) gcore /home/labile/opensource/jdk/jvm-insider/simple-object/round3/core.core
```



最后会有这些现场记录文件：

```
- core.core 
- mylogfile.log 
- pmap.txt 
- pmapXX.txt 
- threads.txt
```

### 启动 debugger

jhsdb

```bash
/home/labile/opensource/jdk/build/linux-x86_64-server-slowdebug-hsdis/jdk/bin/jhsdb hsdb --core /home/labile/opensource/jdk/jvm-insider/simple-object/round3/core.core --exe /home/labile/opensource/jdk/build/linux-x86_64-server-slowdebug-hsdis/jdk/bin/java
```

gdb

```bash
gdb /home/labile/opensource/jdk/build/linux-x86_64-server-slowdebug-hsdis/jdk/bin/java /home/labile/opensource/jdk/jvm-insider/simple-object/round3/core.core
```

### a