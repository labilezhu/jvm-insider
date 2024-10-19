# Java Object Layout

> 以下内容基于 OpenJDK 21 。因为 OpenJDK oop header markword 的 bit layout，在不同版本中，可以有大的、不兼容的变化。如：
>
> - [OpenJDK15: JEP 374: Deprecate and Disable Biased Locking](https://openjdk.org/jeps/374)
> - [OpenJDK22: Synchronization Using The ObjectMonitorTable](https://wiki.openjdk.org/display/HotSpot/Synchronization+Using+The+ObjectMonitorTable)



## Oop Header

[src/hotspot/share/oops/oop.hpp](https://github.com/openjdk/jdk//blob/890adb6410dab4606a4f26a942aed02fb2f55387/src/hotspot/share/oops/oop.hpp#L52) 定义了 Oop 对象头内存 layout :

```c++
class oopDesc {
 private:
  volatile markWord _mark;
  union _metadata/*class word*/ {
    Klass*      _klass;
    narrowKlass _compressed_klass;
  } _metadata;
```



`markWord` 是 `unsigned long int`  8 bytes。

`Klass*` 是 8 bytes 的地址指针。

`narrowKlass` 是 uint32_t 4 bytes。



所以，整个 `oopDesc` 最大情况下，大小是 16 byte。



> [Java Objects Inside Out - shipilev.net](https://shipilev.net/jvm/objects-inside-out/)
>
> you would notice the object header [consists of two parts](http://hg.openjdk.java.net/jdk/jdk/file/19afeaa0fdbe/src/hotspot/share/oops/oop.hpp#l52): *`mark word`* and *`class word`*. `Class word` carries the information about the object’s type: it links to the native structure that describes the class



### Mark Word



`mark word` 有多种用途：

1. 存储 GC移动对象用的元数据（`forwarding 标记行动中`和`object age 对象年龄`）。

2. 存储` identity hash code`。

3. 存储`locking information`。



[src/hotspot/share/oops/markWord.hpp](https://github.com/openjdk/jdk//blob/890adb6410dab4606a4f26a942aed02fb2f55387/src/hotspot/share/oops/markWord.hpp#L71) 中说明了对应版本 OpenJDK 的内存 layout :

```c++
// The markWord describes the header of an object.
//
// Bit-format of an object header (most significant first, big endian layout below):
//
//  64 bits:
//  --------
//  unused:25 hash:31 -->| unused_gap:1  age:4  unused_gap:1  lock:2 (normal object)
//
//  - hash contains the identity hash value: largest value is
//    31 bits, see os::random().  Also, 64-bit vm's require
//    a hash value no bigger than 32 bits because they will not
//    properly generate a mask larger than that: see library_call.cpp
//
//  - the two lock bits are used to describe three states: locked/unlocked and monitor.
//
//    [ptr             | 00]  locked             ptr points to real header on stack (stack-locking in use)
//    [header          | 00]  locked             locked regular object header (fast-locking in use)
//    [header          | 01]  unlocked           regular object header
//    [ptr             | 10]  monitor            inflated lock (header is swapped out)
//    [ptr             | 11]  marked             used to mark an object
//    [0 ............ 0| 00]  inflating          inflation in progress (stack-locking in use)
//
//    We assume that stack/thread pointers have the lowest two bits cleared.
//
//  - INFLATING() is a distinguished markword value of all zeros that is
//    used when inflating an existing stack-lock into an ObjectMonitor.
//    See below for is_being_inflated() and INFLATING().

class markWord {
 private:
  uintptr_t _value;
...    
```



本书的实验环境是 X86 64bit，是： Little-endian (LSB) means we start with the least significant part in the lowest address. 说白了，就如一个 8 byte unsigned long 值 0x00007fffdc6b1234，地址最低的 byte 保存了 0x34 。



对于上面源码的

```
// Bit-format of an object header (most significant first, big endian layout below):
//
//  64 bits:
//  --------
//  unused:25 hash:31 -->| unused_gap:1  age:4  unused_gap:1  lock:2 (normal object)
```

在 x86 64bit 中，应该解读为

```
// Bit-format of an object header (most significant first, big endian layout below):
//
//  64 bits:
//  --------
//  unused:25 hash:31 -->| unused_gap:1  age:4  unused_gap:1  lock:2 (normal object)
    高地址 ----------------------------------------------------> 低地址
    
    
```



下面我们看一些示例，可能更便于理解：



#### Object Young GC age

[JOLSample_22_Promotion.java](https://github.com/labilezhu/pub-diy/blob/b70af9932204bc17320bb830c5689cafd3fbff2b/jvm-insider-book/memory/java-obj-layout/src/org/openjdk/jol/samples/JOLSample_22_Promotion.java#L43)

```java
package org.openjdk.jol.samples;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;

public class JOLSample_22_Promotion {
    public static void main(String[] args) throws IOException {
        long processID = ProcessHandle.current().pid();
        System.out.println("PID: " + processID);

        Object o = new TestClass();

        for (int i = 1; ; i++) {
            System.out.println(i + ": Please use jhsdb to get addr object: scanoops 0xXXXXXX 0x0XXXXXX org.openjdk.jol.samples.TestClass");
            BufferedReader reader = new BufferedReader(new InputStreamReader(System.in));
            String s = reader.readLine();
            if( s == null ) {
                break;
            }
            // make garbage
            byte[] bs = new byte[1024*1024*5];//Mb
        }
        o.toString();
    }
}
```



```bash
bash -c 'echo $$ > /tmp/jvm-insider.pid && exec setarch $(uname -m) --addr-no-randomize java -XX:+AlwaysPreTouch  -Xms100m -Xmx100m -XX:MaxTenuringThreshold=5 -server -XX:+UseSerialGC  -XX:-UseCompressedOops -XX:+UnlockDiagnosticVMOptions "-Xlog:gc*=debug::tid" -Xlog:safepoint=debug::tid -cp /home/labile/pub-diy/jvm-insider-book/memory/java-obj-layout/out/production/java-obj-layout org.openjdk.jol.samples.JOLSample_22_Promotion'

[168173] Compressed class space mapped at: 0x0000000080000000-0x00000000c0000000, reserved size: 1073741824

1: Please use jhsdb to get addr object: scanoops 0xXXXXXX 0x0XXXXXX org.openjdk.jol.samples.TestClass

2: Please use jhsdb to get addr object: scanoops 0xXXXXXX 0x0XXXXXX org.openjdk.jol.samples.TestClass

3: Please use jhsdb to get addr object: scanoops 0xXXXXXX 0x0XXXXXX org.openjdk.jol.samples.TestClass

4: Please use jhsdb to get addr object: scanoops 0xXXXXXX 0x0XXXXXX org.openjdk.jol.samples.TestClass

[42221] Safepoint synchronization initiated using futex wait barrier. (10 threads)
[42221] GC(0) Pause Young (Allocation Failure)
[42221] GC(0) Heap before GC invocations=0 (full 0):
[42221] GC(0)  def new generation   total 30720K, used 23578K [0x00007fffdac00000, 0x00007fffdcd50000, 0x00007fffdcd50000)

```



hsdb

```
# 在上面 java 程序输出： 1: Please use jhsdb to get addr object: scanoops 0xXXXXXX 0x0XXXXXX org.openjdk.jol.samples.TestClass 时执行：
$ sudo /home/labile/opensource/jdk/build/linux-x86_64-server-slowdebug-hsdis/jdk/bin/jhsdb clhsdb --pid $(cat /tmp/jvm-insider.pid)

hsdb> universe
 Heap Parameters:
Gen 0:   eden [0x00007fffdac00000,0x00007fffdb406a10,0x00007fffdc6b0000) space capacity = 27983872, 30.07360811255855 used
  from [0x00007fffdc6b0000,0x00007fffdc6b0000,0x00007fffdca00000) space capacity = 3473408, 0.0 used
  to   [0x00007fffdca00000,0x00007fffdca00000,0x00007fffdcd50000) space capacity = 3473408, 0.0 usedInvocations: 0

Gen 1:   old  [0x00007fffdcd50000,0x00007fffdcd50000,0x00007fffe1000000) space capacity = 69926912, 0.0 usedInvocations: 0

hsdb> scanoops 0x00007fffdac00000 0x00007fffdcd50000 org.openjdk.jol.samples.TestClass
 0x00007fffdb33edc0 org/openjdk/jol/samples/TestClass

hsdb> inspect 0x00007fffdb33edc0
...
hsdb> mem 0x00007fffdb33edc0/2
0x00007fffdb33edc0: 0x0000000000000001 = binary: age:0000 unused_gap:0 lock:01

hsdb> detach
 ...
 
# 在上面 java 程序输出： GC(0) Pause Young (Allocation Failure) 时执行： 
hsdb> reattach


hsdb> scanoops 0x00007fffdac00000 0x00007fffdcd50000 org.openjdk.jol.samples.TestClass
# 通过地址，结合上面 universe 的输出，可见，对象已经从 Eden Area 移动到 Young to area 
0x00007fffdca40180 org/openjdk/jol/samples/TestClass

hsdb> inspect 0x00007fffdca40180
hsdb> mem 0x00007fffdca40180/2
# 可见，对象已经从 Age 从 0 变成 1
0x00007fffdca40180: 0x0000000000000009 = binary: age:0001 unused_gap:0 lock:01
hsdb> detach
```





gdb

```
(gdb) p ((oopDesc*)0x00007fffdca40180)->_mark._value
$1 = 9
(gdb) set $mark_addr = &(((oopDesc*)0x00007fffdca40180)->_mark._value)
(gdb) x/8xb $mark_addr
0x7fffdca40180: 0x09    0x00    0x00    0x00    0x00    0x00    0x00    0x00
(gdb) x/8tb $mark_addr
0x7fffdca40180: 00001001        00000000        00000000        00000000        00000000        00000000        00000000        00000000
(gdb) x/1tg $mark_addr
0x7fffdca40180: 0000000000000000000000000000000000000000000000000000000000001001 = age:0001 unused_gap:0 lock:01
```





### Class word

```
hsdb> inspect 0x00007fffdca40180
instance of Oop for org/openjdk/jol/samples/TestClass @ 0x00007fffdca40180 (size = 16)
_mark: 9
_metadata._compressed_klass: InstanceKlass for org/openjdk/jol/samples/TestClass

```



```
(gdb) p *((oopDesc*)0x00007fffdca40180)
{_mark = {_value = 9, _metadata = {_klass = 0x80084a10, _compressed_klass = 2148026896}}
```

由于我已经 `-XX:-UseCompressedOops` 所以不采用 _compressed_klass ，采用 _klass。

```
p *((Klass*)0x80084a10)

$3 = {<Metadata> = {<MetaspaceObj> = {_vptr.Metadata = 0x7ffff7c256a0 <vtable for InstanceKlass+16>, _valid = 0}, static KLASS_KIND_COUNT = 7, 
  _layout_helper = 16, _kind = Klass::InstanceKlassKind, _modifier_flags = 1, _super_check_offset = 64, _name = 0x7ffff03fd698, _secondary_super_cache = 0x0, _secondary_supers = 0x7fffd0000048, _primary_supers = {0x80041200, 
    0x80084a10, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0}, _java_mirror = {_obj = 0x7ffff03a8720}, _super = 0x80041200, _subklass = 0x0, _next_sibling = 0x800db970, _next_link = 0x80084800, _class_loader_data = 0x7ffff03a84a0, 
  _vtable_len = 5, _access_flags = {_flags = 33}, _trace_id = 84148224, _shared_class_path_index = -1, _shared_class_flags = 0, _archived_mirror_index = -1}
```

由 `vtable for InstanceKlass` 可知，这个对象的具体 class 是 Klass 的 sub class `InstanceKlass` 。看看 java 类名：

```
(gdb) p ((InstanceKlass*)0x80084a10)->_name->base()
$10 = (const u1 *) 0x7ffff03fd69e "org/openjdk/jol/samples/TestClass", '\361' <repeats 39 times>, "\350\216u"
```

可见，结果对得上 hsdb 的结果。



参考源码：

- src/hotspot/share/oops/klass.hpp
- src/hotspot/share/oops/instanceKlass.hpp
- src/hotspot/share/oops/symbol.hpp



地址 0x80084a10 就是在上面 java 中的 Compressed class space 中。根据是进程启动时输出了：

```
[168173] Compressed class space mapped at: 0x0000000080000000-0x00000000c0000000, reserved size: 1073741824
```





## 参考

 - [Java Object Layout: A Tale Of Confusion - psy-lob-saw.blogspot.com - 2014](https://psy-lob-saw.blogspot.com/2014/03/java-object-layout-tale-of-confusion.html)
 - [JOL (Java Object Layout) is the tiny toolbox to analyze object layout schemes in JVMs - openjdk.org](https://openjdk.org/projects/code-tools/jol/)
 - [Java Objects Inside Out - shipilev.net](https://shipilev.net/jvm/objects-inside-out/)
 - [Lock Lock Lock: Enter!](https://jpbempel.github.io/2013/03/25/lock-lock-lock-enter.html)