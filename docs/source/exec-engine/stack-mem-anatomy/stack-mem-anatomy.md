# Stack Memory - 堆栈内存剖析



:::{figure-md}

<img src="mem-layout-r3.drawio.svg" alt="图： JVM 堆栈内存剖析">

*图： JVM 堆栈内存剖析*
:::
*[用 Draw.io 打开](https://app.diagrams.net/?ui=sketch#Uhttps%3A%2F%2Fjvm-insider.mygraphql.com%2Fzh-cn%2Flatest%2F_images%2Fmem-layout-r3.drawio.svg)*



由于堆栈是线程运行的 context，是运行引擎的热点核心数据。线程想触达到其它的在 heap 中的对象，几乎都要以这个 context 为根，去多次寻址才能触达 heap 中的目标数据 。可以说，这个 context 就是串联各功能模块的中心，用它可以找到上级函数返回点、入参、本函数的本地变量……了解堆栈上保存了什么数据，怎样保存数据，对了解 JVM 运行引擎、JIT编译、GC 等等功能面有重要的串接作用。就可能知道功能面之间是如何耦合、协作，完成 JVM 的完整功能。



HotSpot OpenJDK 的 Java 堆栈直接建立于 Native 堆栈内存区上。保存在其中的数据，最少包括以下类型：

- 返回到上级函数的返回地址
- 函数的入参
- 函数内的 local vars



对于需要精学掌握的知识，我喜欢用 `get my hands dirty` 做实验的方法来学习，有以下好处：

- 做 fact check。技术的更新太快，有的东西要眼见为实
- 加强记忆。知识是自己挖出来，比直接学习来得深刻
- 实验的过程学习到目标知识之外周边的技能和知识。做个有实操能力的技术人。而不单单纸上谈兵。



## 实验环境准备

1. JDK 需要支持 hsdis 
2. Java 程序
3. Java Options
4. 保存现场
5. 启动 debugger

### JDK 支持 hsdis

> 如需要分析 JVM 编译生成的代码，可以通过 `-XX:+PrintAssembly` java 参数让 JVM 以汇编为格式，输出 JIT 编译后的程序到日志文件。使用说明见： [https://wiki.openjdk.org/display/HotSpot/PrintAssembly](https://wiki.openjdk.org/display/HotSpot/PrintAssembly) 。
> `-XX:+PrintAssembly` 基于 hsdis 技术，需要 jdk 在构建期就支持 hsdis。
> 另外，其实 JDK 自带的 jhsdb 也可以实时反编译 JIT 生成的机器指令。所以 hsdis 有时不是必须的。但如果你希望得到注释比较丰富（如函数 call 地址后显示函数名），可读性高，可用 [jitwatch](https://github.com/AdoptOpenJDK/jitwatch) GUI 分析的汇编代码，那么支持 hsdis 是必须的。

JVM 支持 hsdis 的准备工作参见： {doc}`/appendix-lab-env/build-jdk/build-slow-debug-jdk`



### Java 程序

见： [https://github.com/labilezhu/pub-diy/blob/main/jvm-insider-book/exec-engine/stack-mem-anatomy/](https://github.com/labilezhu/pub-diy/blob/main/jvm-insider-book/exec-engine/stack-mem-anatomy/)

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

(java-options)=
### Java Options


```bash
setarch $(uname -m) --addr-no-randomize /home/labile/opensource/jdk/build/linux-x86_64-server-slowdebug-hsdis/jdk/bin/java -server -XX:+UseSerialGC -XX:+PreserveFramePointer -Xcomp -XX:-TieredCompilation -XX:-BackgroundCompilation -XX:-UseCompressedOops -XX:+UnlockDiagnosticVMOptions -XX:+PrintAssembly -XX:PrintAssemblyOptions=intel -XX:CompileCommand=dontinline -Xlog:class+load=info -XX:+LogCompilation -XX:LogFile=./round3/mylogfile.log -XX:+DebugNonSafepoints -XX:+PrintInterpreter  -cp . SimpleObj 
```

想看每个 Options 的描述，可以在 [VM Options Explorer - OpenJDK11 HotSpot](https://chriswhocodes.com/vm-options-explorer.html) 中找到。但要看深入的内容，还得自己搜索。

其中：
 - `setarch $(uname -m) --addr-no-randomize` 是为了禁用 [Address space layout randomization (ASLR)](https://en.wikipedia.org/wiki/Address_space_layout_randomization) 。以让多次重启 Java 进程时，内存地址尽量一致。
 - `-XX:+PreserveFramePointer` 是为了 stack 和 CPU 寄存器的使用 与 gdb 兼容，让 gdb 可以正确识别出线程的 stack 。 详见： [Java Mixed-Mode
Flame Graphs - Brendan Gregg](https://www.brendangregg.com/Slides/JavaOne2015_MixedModeFlameGraphs.pdf)
 - `-Xcomp -XX:-TieredCompilation -XX:-BackgroundCompilation` 让代码跳过 interpreter 直接 JIT 编译。因为本节的重点是 JIT 。`-XX:-BackgroundCompilation` 与 `-Xbatch` 同义，均为不在异步后台编译，直接在工作线程中等待编译完成。
 - `-XX:+PrintAssembly -XX:PrintAssemblyOptions=intel -XX:CompileCommand=dontinline -Xlog:class+load=info -XX:+LogCompilation -XX:LogFile=./round3/mylogfile.log -XX:+DebugNonSafepoints -XX:+PrintInterpreter` 这些参数目的是保存 JIT 汇编输出。对于本节实验这是可选的。参数使用说明见： https://wiki.openjdk.org/display/HotSpot/PrintAssembly

(save-debug-output)=
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

已经放到 [github 中](https://github.com/labilezhu/pub-diy/blame/main/jvm-insider-book/exec-engine/stack-mem-anatomy/round3/)。


(start-debugger)=
### 启动 debugger

jhsdb

```bash
# GUI hsdb
/home/labile/opensource/jdk/build/linux-x86_64-server-slowdebug-hsdis/jdk/bin/jhsdb hsdb --core /home/labile/opensource/jdk/jvm-insider/simple-object/round3/core.core --exe /home/labile/opensource/jdk/build/linux-x86_64-server-slowdebug-hsdis/jdk/bin/java

# command line hsdb
/home/labile/opensource/jdk/build/linux-x86_64-server-slowdebug-hsdis/jdk/bin/jhsdb clhsdb --core /home/labile/opensource/jdk/jvm-insider/simple-object/round3/core.core --exe /home/labile/opensource/jdk/build/linux-x86_64-server-slowdebug-hsdis/jdk/bin/java
```

GDB

```bash
gdb /home/labile/opensource/jdk/build/linux-x86_64-server-slowdebug-hsdis/jdk/bin/java /home/labile/opensource/jdk/jvm-insider/simple-object/round3/core.core
```



## 堆栈内存剖析



### 线程

从 GDB 看：

```
(gdb) info thread
  Id   Target Id                          Frame 
* 1    Thread 0x7ffff7d3eb80 (LWP 513808) __futex_abstimed_wait_common64 (private=128, cancel=true, abstime=0x0, op=265, expected=513811, futex_word=0x7ffff5286910) at ./nptl/futex-internal.c:57
  2    Thread 0x7ffff5286640 (LWP 513811) __futex_abstimed_wait_common64 (private=-173778129, cancel=true, abstime=0x7ffff5285600, op=137, expected=0, futex_word=0x7ffff002c278) at ./nptl/futex-internal.c:57
  3    Thread 0x7ffff4fb5640 (LWP 513812) __futex_abstimed_wait_common64 (private=-171172765, cancel=true, abstime=0x7ffff4fb4c60, op=137, expected=0, futex_word=0x7ffff7d05874 <mutex_init()::PeriodicTask_lock_storage+92>)    at ./nptl/futex-internal.c:57
  4    Thread 0x7ffff4eb4640 (LWP 513816) __futex_abstimed_wait_common64 (private=-266988752, cancel=true, abstime=0x7ffff4eb3c60, op=137, expected=0, futex_word=0x7ffff7d06b90 <mutex_init()::VMOperation_lock_storage+88>)    at ./nptl/futex-internal.c:57
  5    Thread 0x7ffff453b640 (LWP 513835) __futex_abstimed_wait_common64 (private=0, cancel=true, abstime=0x0, op=393, expected=0, futex_word=0x7ffff7d06970 <mutex_init()::Heap_lock_storage+88>) at ./nptl/futex-internal.c:57
...
```

格式解释： 对于 Id=2 (第2行数据)： `Id=2` 是 gdb 为 gdb 命令引用这个线程而生成的线程序号，以下叫 `gdb thread index`。 `0x7ffff5286640` 是 pthread 的 userspace 内存指针。513811 是 tid 。 `__futex_abstimed_wait_common64(private=-173778129,...` 是线程 userspace 的最高 stack top function 及其入参。



那么问题来了，哪条线程才是 java 的 main ? coredump 模式下的 GDB 不能看到 thread name([pthread_setname_np](https://man7.org/linux/man-pages/man3/pthread_setname_np.3.html#NOTES)) 的。因为数据是来源于运行状态下的进程在内核 [procfs 文件系统](http://man7.org/linux/man-pages/man5/proc.5.html) 的 `/proc/$PID/task/$TID/comm` 文件中。

没关系，还记得之前的 `ps  -T -p $JAVA_PID | tee /home/labile/opensource/jdk/jvm-insider/simple-object/round3/threads.txt` ：

```
    PID    SPID TTY          TIME CMD
 513808  513808 pts/18   00:00:00 java
 513808  513811 pts/18   00:00:12 java
 513808  513812 pts/18   00:00:01 VM Periodic Tas
 513808  513816 pts/18   00:00:00 VM Thread
```

看样子是 513808 、 513811 之一。

```
(gdb) thread 1 #切换到 gdb thread index 1
(gdb) bt #查看当前 thread stack
#0  __futex_abstimed_wait_common64 (...
#1  __futex_abstimed_wait_common (...
#2  __GI___futex_abstimed_wait_cancelable64 (...
#3  0x00007ffff7df2624 in __pthread_clockjoin_ex (...
#4  0x00007ffff7fb03e9 in CallJavaMainInNewThread (stack_size=1048576, args=0x7fffffffa860) at /home/labile/opensource/jdk/src/java.base/unix/native/libjli/java_md.c:693
#5  0x00007ffff7faedd8 in ContinueInNewThread (ifn=0x7fffffffa9f0, threadStackSize=1048576, argc=0, argv=0x555555559940, mode=1, what=0x555555559650 "SimpleObj", ret=0)
    at /home/labile/opensource/jdk/src/java.base/share/native/libjli/java.c:2329
#6  0x00007ffff7fb048f in JVMInit (ifn=0x7fffffffa9f0, threadStackSize=0, argc=0, argv=0x555555559940, mode=1, what=0x555555559650 "SimpleObj", ret=0) at /home/labile/opensource/jdk/src/java.base/unix/native/libjli/java_md.c:718
#7  0x00007ffff7fa84f2 in JLI_Launch (argc=0, argv=0x555555559940, jargc=0, jargv=0x0, appclassc=0, appclassv=0x0, fullversion=0x5555555560c1 "21-internal-adhoc.labile.jdk", dotversion=0x5555555560bd "0.0", 
    pname=0x555555556032 "java", lname=0x555555556037 "openjdk", javaargs=0 '\000', cpwildcard=1 '\001', javaw=0 '\000', ergo=0) at /home/labile/opensource/jdk/src/java.base/share/native/libjli/java.c:340
#8  0x000055555555566e in main (argc=19, argv=0x7fffffffdbf8) at /home/labile/opensource/jdk/src/java.base/share/native/launcher/main.c:166
```

可见，gdb thread index 1 只是 native 层面的 main thread ，但应该不是 Java 层面的。

```
(gdb) thread 2
(gdb) bt
#0  __futex_abstimed_wait_common64 (...
#1  __futex_abstimed_wait_common (...
#2  __GI___futex_abstimed_wait_cancelable64 (...
#3  0x00007ffff7defe9b in __pthread_cond_wait_common (...
#4  ___pthread_cond_timedwait64 (cond=0x7ffff002c250, mutex=0x7ffff002c228, abstime=0x7ffff5285600) at ./nptl/pthread_cond_wait.c:652
#5  0x00007ffff6690d96 in PlatformEvent::park_nanos (this=0x7ffff002c200, nanos=1000000000000000) at /home/labile/opensource/jdk/src/hotspot/os/posix/os_posix.cpp:1575
#6  0x00007ffff61720b7 in JavaThread::sleep_nanos (this=0x7ffff002b3c0, nanos=1000000000000000) at /home/labile/opensource/jdk/src/hotspot/share/runtime/javaThread.cpp:2044
#7  0x00007ffff6291796 in JVM_Sleep (env=0x7ffff002b7b8, threadClass=0x7ffff5285770, nanos=1000000000000000) at /home/labile/opensource/jdk/src/hotspot/share/prims/jvm.cpp:3067
#8  0x00007fffed72ca20 in ?? ()
#9  0x00007ffff5285780 in ?? ()
#10 0x00007ffbf404fa90 in ?? ()
...
#24 0x00007fffed007eec in ?? ()
#25 0x00007fffed007eec in ?? ()
#26 0x000000003b9aca00 in ?? ()
#27 0x0000000000000000 in ?? ()
```

回想到 java 程序的 `SimpleObj.main(...)` 中调用了 `Thread.sleep(1000*1000*1000)` 。

于是找回 JDK 源码，调用链倒序(stack)如下：




- [src/hotspot/share/include/jvm.h 的 JVM_Sleep(JNIEnv *env, jclass threadClass, jlong nanos)](https://github.com/openjdk/jdk//blob/890adb6410dab4606a4f26a942aed02fb2f55387/src/hotspot/share/include/jvm.h#L279)
- [native 的 Thread.sleep0(long nanos) ](https://github.com/openjdk/jdk//blob/890adb6410dab4606a4f26a942aed02fb2f55387/src/java.base/share/classes/java/lang/Thread.java#L516)
- [Thread.sleep(long millis) ](https://github.com/openjdk/jdk//blob/890adb6410dab4606a4f26a942aed02fb2f55387/src/java.base/share/classes/java/lang/Thread.java#L498)
- [SimpleObj.main(...) ](https://github.com/labilezhu/pub-diy/blame/main/jvm-insider-book/exec-engine/stack-mem-anatomy/SimpleObj.java#L5)



> 校真的读者会问如果得知 Thread.sleep0(long nanos)  会调用 JVM_Sleep() ？主要看 [src/java.base/share/native/libjava/Thread.c](https://github.com/openjdk/jdk//blob/890adb6410dab4606a4f26a942aed02fb2f55387/src/java.base/share/native/libjava/Thread.c#L42-L43) 。



可见 `gdb thread index 1 ` 或说 `TID 513811` 为 java 的 main 线程。

可以用  hsdb 的 `threadcontext` 命令检查一下：

```
hsdb> threadcontext -v 513811
Thread "main" id=513811 Address=0x00007ffff002b3c0
...
r10: 0x00007ffff5285600: In java stack [0x00007ffff5287000,0x00007ffff52854c0,0x00007ffff5187000] for thread sun.jvm.hotspot.runtime.JavaThread@0x00007ffff002b3c0:
   "main" #1 prio=5 tid=0x00007ffff002b3c0 nid=513811 waiting on condition [0x00007ffff5285000]
   java.lang.Thread.State: TIMED_WAITING (sleeping)
   JavaThread state: _thread_blocked
...
rcx: 0x00007ffff7ded117: __GI___futex_abstimed_wait_cancelable64 + 0xe7
...
rip: 0x00007ffff7ded117: __GI___futex_abstimed_wait_cancelable64 + 0xe7
...
rsp: 0x00007ffff52854c0: In java stack [0x00007ffff5287000,0x00007ffff52854c0,0x00007ffff5187000] for thread sun.jvm.hotspot.runtime.JavaThread@0x00007ffff002b3c0:
   "main" #1 prio=5 tid=0x00007ffff002b3c0 nid=513811 waiting on condition [0x00007ffff5285000]
   java.lang.Thread.State: TIMED_WAITING (sleeping)
   JavaThread state: _thread_blocked
fsbase: 0x00007ffff5286640: In java stack [0x00007ffff5287000,0x00007ffff52854c0,0x00007ffff5187000] for thread sun.jvm.hotspot.runtime.JavaThread@0x00007ffff002b3c0:
   "main" #1 prio=5 tid=0x00007ffff002b3c0 nid=513811 waiting on condition [0x00007ffff5285000]
   java.lang.Thread.State: TIMED_WAITING (sleeping)
   JavaThread state: _thread_blocked
gsbase: null
```

从上面的 "main" 可见，这个判断正确。



### 内存分区

以下假设读者已经对以下知识有一些概念认识：

-  Linux 进程内存分区概念。如还未了解，可见：[进程的内存 - 《Mark’s DevOps 雜碎》](https://devops-insider.mygraphql.com/zh-cn/latest/kernel/mem/vma/pmap.html#id1)
- Java 内存分区，以及它 Linux 进程内存分区的映射关系。如还未了解，可见：[把大象装入货柜里——Java容器内存拆解](https://blog.mygraphql.com/zh/notes/java/native-mem/java-native-mem-case/)



先看看 [pmap 输出](https://github.com/labilezhu/pub-diy/blame/main/jvm-insider-book/exec-engine/stack-mem-anatomy/round3/pmap.txt#L2)：

```
         Address Perm   Offset Device    Inode     Size     Rss     Pss Referenced Anonymous LazyFree ShmemPmdMapped FilePmdMapped Shared_Hugetlb Private_Hugetlb Swap SwapPss Locked THPeligible Mapping
...         
    7ffc02600000 rw-p 00000000  00:00        0   342656  342656  342656     342656    342656        0              0             0              0               0    0       0      0           0 
    7ffff518b000 rw-p 00000000  00:00        0     1008     124     124        124       124        0              0             0              0               0    0       0      0           0 
    7fffed000000 rwxp 00000000  00:00        0     7360    7360    7360       7360      7360        0              0             0              0               0    0       0      0           0 
```



再看看 hsdb 的 heap 信息：

```
hsdb> universe
Heap Parameters:
Gen 0:   eden [0x00007ffc02600000,0x00007ffc040c6a58,0x00007ffc131c0000) space capacity = 280756224, 10.000359600220296 used
  from [0x00007ffc131c0000,0x00007ffc131c0000,0x00007ffc15330000) space capacity = 35061760, 0.0 used
  to   [0x00007ffc15330000,0x00007ffc15330000,0x00007ffc174a0000) space capacity = 35061760, 0.0 usedInvocations: 0

Gen 1:   old  [0x00007ffd50950000,0x00007ffd50950000,0x00007ffd7a6b0000) space capacity = 701890560, 0.0 usedInvocations: 0
```



### Stack 剖析

在上面启动的 jhsdb GUI 中，在 “Java Threads” 窗口中选择 main thread ，然后运行 “Stack Memory” 工具，就会看到形似下图中的 “Stack Memory for main” 窗口 的结果：

:::{figure-md} 图： JVM 堆栈内存剖析

<img src="mem-layout-r3.drawio.svg" alt="图： JVM 堆栈内存剖析">

*图： JVM 堆栈内存剖析*
:::
*[用 Draw.io 打开](https://app.diagrams.net/?ui=sketch#Uhttps%3A%2F%2Fjvm-insider.mygraphql.com%2Fzh-cn%2Flatest%2F_images%2Fmem-layout-r3.drawio.svg)*



以  “Stack Memory for main”  窗口的信息为中心，就可以扩展交叉关联到其它工具的信息。如：

- gdb 中 main thread 的寄存器信息：

```
(gdb) info registers
sp (native stack top)   0x7ffff52854c0
r10                     0x7ffff5285600      
```

- gdb 的 bt 打印 native stack 输出

- jhsdb GUI 的 “Inspector” 中输入一个OoP地址，即可以观察一个 OoP 对象的类型。

- OoP 对象所在的 Java 内存区(from jhsdb)，以及Java 内存区对应的 Linux 内存区(from pmap)
- JIT 生成的CPU机器指令码所在的 Code Cache ，以及Java 内存区对应的 Linux 内存区。Linux 内存区带了 `x` permission ，即为存放可执行机器指令的内存区。
- jhsdb GUI “Code Viewer” 中输入一个 stack 中的函数返回地址，即可反汇编出整个函数的汇编指令。
- JDK 的Java 源码以及 c/c++ 源码



图中已经有比较完整的信息了，就不再重复描述了。只是要看明白这个图有点费显示器和时间。反正我是在两个 2k 显示器中画图的 :)



## 参考
- [Notes on debugging HotSpot's JIT compilation - Jorn Vernee](https://jornvernee.github.io/hotspot/jit/2023/08/18/debugging-jit.html)



