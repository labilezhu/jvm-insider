# 探视 Hotspot Build 的细节

(inspect-c-preprocessor-gen-code)=
## 探视 C Preprocessor 生成代码

{doc}`/appendix-lab-env/build-jdk/build-slow-debug-jdk` 中，讲述了 OpenJDK 的构建。但有时候，我们在分析 OpenJDK 源码原理时，需要知道 build 过程的细节。如，OpenJDK 中大量使用  `C Macro` / `C Preprocessor` 的编写方法 。人要从这些参数化+多层嵌套的 `C Preprocessor` 代码中看到最终生成的代码，从而了解其真实的意图，有很大的困难。没事，我们可以让 gcc 在编译时保存一下这些  `C Preprocessor`  生成的中间代码。


如， [src/hotspot/share/runtime/vmStructs.cpp](https://github.com/openjdk/jdk//blob/890adb6410dab4606a4f26a942aed02fb2f55387/src/hotspot/share/runtime/vmStructs.cpp#L1215) 中包含了大量的 `C Macro` / `C Preprocessor` 。以下方法可以探视到其实际生成的 C++ 代码
```c++
VMStructEntry VMStructs::localHotSpotVMStructs[] = {

  VM_STRUCTS(GENERATE_NONSTATIC_VM_STRUCT_ENTRY,
             GENERATE_STATIC_VM_STRUCT_ENTRY,
             GENERATE_STATIC_PTR_VOLATILE_VM_STRUCT_ENTRY,
             GENERATE_UNCHECKED_NONSTATIC_VM_STRUCT_ENTRY,
             GENERATE_NONSTATIC_VM_STRUCT_ENTRY,
             GENERATE_NONPRODUCT_NONSTATIC_VM_STRUCT_ENTRY,
             GENERATE_C1_NONSTATIC_VM_STRUCT_ENTRY,
             GENERATE_C2_NONSTATIC_VM_STRUCT_ENTRY,
             GENERATE_C1_UNCHECKED_STATIC_VM_STRUCT_ENTRY,
             GENERATE_C2_UNCHECKED_STATIC_VM_STRUCT_ENTRY)
...             
```


首先，需要知道 gcc 支持一个 [-save-temps=obj](https://gcc.gnu.org/onlinedocs/gcc-13.1.0/gcc/Overall-Options.html#:~:text=temps%3Dcwd%20and-,%2Dsave%2Dtemps%3Dobj,-override%20this%20default) 参数。它可以把 `C Preprocessor` 生成的中间代码输出到一个文件中。

那么，如何编写这个 gcc 命令？ 不用担心，我们可以抄之前 build openjdk 产生的功课：
```bash
cat /home/labile/opensource/jdk/build/linux-x86_64-server-slowdebug/hotspot/variant-server/libjvm/objs/vmStructs.o.cmdline

/usr/bin/g++ -MMD -MF /home/labile/opensource/jdk/build/linux-x86_64-server-slowdebug/hotspot/variant-server/libjvm/objs/vmStructs.d.tmp -I/home/labile/opensource/jdk/build/linux-x86_64-server-slowdebug/hotspot/variant-server/libjvm/objs/precompiled -D__STDC_FORMAT_MACROS -D__STDC_LIMIT_MACROS -D__STDC_CONSTANT_MACROS -D_GNU_SOURCE -D_REENTRANT -pipe -fno-rtti .... -c -o /home/labile/opensource/jdk/build/linux-x86_64-server-slowdebug/hotspot/variant-server/libjvm/objs/vmStructs.o /home/labile/opensource/jdk/src/hotspot/share/runtime/vmStructs.cpp -frandom-seed="vmStructs.cpp"
```

修改一下命令，加入 `-save-temps=obj` 。

```bash
/usr/bin/g++ -MMD -MF /home/labile/opensource/jdk/build/linux-x86_64-server-slowdebug/hotspot/variant-server/libjvm/objs/vmStructs.d.tmp -I/home/labile/opensource/jdk/build/linux-x86_64-server-slowdebug/hotspot/variant-server/libjvm/objs/precompiled -D__STDC_FORMAT_MACROS -D__STDC_LIMIT_MACROS -D__STDC_CONSTANT_MACROS -D_GNU_SOURCE -D_REENTRANT ... -I/home/labile/opensource/jdk/src/hotspot/os/posix -I/home/labile/opensource/jdk/src/hotspot/cpu/x86 -I/home/labile/opensource/jdk/src/hotspot/os_cpu/linux_x86 -I/home/labile/opensource/jdk/build/linux-x86_64-server-slowdebug/hotspot/variant-server/gensrc -I/home/labile/opensource/jdk/src/hotspot/share/precompiled -I... -save-temps=obj -v -c -o /home/labile/opensource/jdk/build/linux-x86_64-server-slowdebug/hotspot/variant-server/libjvm/objs/vmStructs.o /home/labile/opensource/jdk/src/hotspot/share/runtime/vmStructs.cpp -frandom-seed="vmStructs.cpp"
```

执行完成后，可以看到生成了 /home/labile/opensource/jdk/build/linux-x86_64-server-slowdebug/hotspot/variant-server/libjvm/objs/vmStructs.ii 文件:

```c++
...
# 140 "/home/labile/opensource/jdk/src/hotspot/share/runtime/vmStructs.cpp" 2

# 1 "/home/labile/opensource/jdk/src/hotspot/cpu/x86/vmStructs_x86.hpp" 1
# 143 "/home/labile/opensource/jdk/src/hotspot/share/runtime/vmStructs.cpp" 2
# 1 "/home/labile/opensource/jdk/src/hotspot/os/linux/vmStructs_linux.hpp" 1
# 28 "/home/labile/opensource/jdk/src/hotspot/os/linux/vmStructs_linux.hpp"
# 1 "/usr/include/dlfcn.h" 1 3 4
# 29 "/home/labile/opensource/jdk/src/hotspot/os/linux/vmStructs_linux.hpp" 2
# 144 "/home/labile/opensource/jdk/src/hotspot/share/runtime/vmStructs.cpp" 2
# 1 "/home/labile/opensource/jdk/src/hotspot/os_cpu/linux_x86/vmStructs_linux_x86.hpp" 1
# 145 "/home/labile/opensource/jdk/src/hotspot/share/runtime/vmStructs.cpp" 2
# 2736 "/home/labile/opensource/jdk/src/hotspot/share/runtime/vmStructs.cpp"
VMStructEntry VMStructs::localHotSpotVMStructs[] = {

    {"EpsilonHeap", "_virtual_space", "VirtualSpace", 0, ([]()
                                                          { char space[sizeof (EpsilonHeap)] __attribute__((aligned(16))); EpsilonHeap* dummyObj = (EpsilonHeap*)space; char* c = (char*)(void*)&dummyObj->_virtual_space; return (size_t)(c - space); }()),
...
```

