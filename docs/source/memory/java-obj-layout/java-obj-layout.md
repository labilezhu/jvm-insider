# Java Object Layout

```

```

> https://sourceware.org/gdb/current/onlinedocs/gdb.html/Memory.html
> https://sourceware.org/gdb/current/onlinedocs/gdb.html/Output-Formats.html



## Oop Header

[src/hotspot/share/oops/oop.hpp](https://github.com/openjdk/jdk//blob/890adb6410dab4606a4f26a942aed02fb2f55387/src/hotspot/share/oops/oop.hpp#L52)

```c++
class oopDesc {
 private:
  volatile markWord _mark;
  union _metadata {
    Klass*      _klass;
    narrowKlass _compressed_klass;
  } _metadata;
```



`markWord` 是 `unsigned long int`  8 bytes。

`Klass*` 是 8 bytes 的地址指针。

`narrowKlass` 是 uint32_t 4 bytes。



所以，整个 `oopDesc` 最大大小是 16 byte。



```
TestObjA
0x00007ffc02a5ad28
```





```
p *((oopDesc*)0x00007ffc02a5ad28)
$2 = {_mark = {_value = 1 }, _metadata = {_klass = 0x80084c20, _compressed_klass = 2148027424}}
```



> [Java Objects Inside Out - shipilev.net](https://shipilev.net/jvm/objects-inside-out/)
>
> you would notice the object header [consists of two parts](http://hg.openjdk.java.net/jdk/jdk/file/19afeaa0fdbe/src/hotspot/share/oops/oop.hpp#l52): *`mark word`* and *`class word`*. `Class word` carries the information about the object’s type: it links to the native structure that describes the class





### Mark Word



```


p ((oopDesc*)0x00007ffc02a5ad28)->_mark._value
1

set $mark_addr = &(((oopDesc*)0x00007ffc02a5ad28)->_mark._value)

p sizeof(((oopDesc*)0x00007ffc02a5ad28)->_mark._value)
8

x/8xb $mark_addr
0x7ffc02a5ad28: 0x01    0x00    0x00    0x00    0x00    0x00    0x00    0x00
//X86 is Little-endian (LSB) means we start with the least significant part in the lowest address.

x/8ob $mark_addr
0x7ffc02a5ad28: 01      0       0       0       0       0       0       0

x/8tb $mark_addr
0x7ffc02a5ad28: 00000001        00000000        00000000        00000000        00000000        00000000        00000000        00000000

```





`mark word` 有多种用途：

1. 存储 GC移动对象用的元数据（`forwarding 标记行动中`和`object age 对象年龄`）。

2. 存储` identity hash code`。

3. 存储`locking information`。



[src/hotspot/share/oops/markWord.hpp](https://github.com/openjdk/jdk//blob/890adb6410dab4606a4f26a942aed02fb2f55387/src/hotspot/share/oops/markWord.hpp#L71)

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
  // Constants
  static const int age_bits                       = 4;
  static const int lock_bits                      = 2;
  static const int first_unused_gap_bits          = 1;
  static const int max_hash_bits                  = BitsPerWord - age_bits - lock_bits - first_unused_gap_bits;
  static const int hash_bits                      = max_hash_bits > 31 ? 31 : max_hash_bits;
  static const int second_unused_gap_bits         = LP64_ONLY(1) NOT_LP64(0);

  static const int lock_shift                     = 0;
  static const int age_shift                      = lock_bits + first_unused_gap_bits;
  static const int hash_shift                     = age_shift + age_bits + second_unused_gap_bits;

  static const uintptr_t lock_mask                = right_n_bits(lock_bits);
  static const uintptr_t lock_mask_in_place       = lock_mask << lock_shift;
  static const uintptr_t age_mask                 = right_n_bits(age_bits);
  static const uintptr_t age_mask_in_place        = age_mask << age_shift;
  static const uintptr_t hash_mask                = right_n_bits(hash_bits);
  static const uintptr_t hash_mask_in_place       = hash_mask << hash_shift;

  static const uintptr_t locked_value             = 0;
  static const uintptr_t unlocked_value           = 1;
  static const uintptr_t monitor_value            = 2;
  static const uintptr_t marked_value             = 3;

  static const uintptr_t no_hash                  = 0 ;  // no hash value assigned
  static const uintptr_t no_hash_in_place         = (address_word)no_hash << hash_shift;
  static const uintptr_t no_lock_in_place         = unlocked_value;

    
```

























## 参考

 - [Java Object Layout: A Tale Of Confusion - psy-lob-saw.blogspot.com - 2014](https://psy-lob-saw.blogspot.com/2014/03/java-object-layout-tale-of-confusion.html)
 - [JOL (Java Object Layout) is the tiny toolbox to analyze object layout schemes in JVMs - openjdk.org](https://openjdk.org/projects/code-tools/jol/)
 - [Java Objects Inside Out - shipilev.net](https://shipilev.net/jvm/objects-inside-out/)
 - [Lock Lock Lock: Enter!](https://jpbempel.github.io/2013/03/25/lock-lock-lock-enter.html)