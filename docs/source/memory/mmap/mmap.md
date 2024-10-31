# MMap - OS Memory Area

## 内存分区
关于 JVM 内存分区，可见我之前写的文章：

-  Linux 进程内存分区概念。如还未了解，可见：[进程的内存 - 《Mark’s DevOps 雜碎》](https://devops-insider.mygraphql.com/zh-cn/latest/kernel/mem/vma/pmap.html#id1)
- Java 内存分区，以及它 Linux 进程内存分区的映射关系。如还未了解，可见：[把大象装入货柜里——Java容器内存拆解](https://blog.mygraphql.com/zh/notes/java/native-mem/java-native-mem-case/)

## 分阶段占用内存

### 实验
```bash
bash -c 'echo pid=$$ && read && exec /home/labile/opensource/jdk/build/linux-x86_64-server-slowdebug-hsdis/jdk/bin/java -XX:NativeMemoryTracking=detail -XX:+PrintNMTStatistics -XX:+AlwaysPreTouch  -Xms100m -Xmx100m -server -XX:+UseSerialGC  -XX:-UseCompressedOops -XX:+UnlockDiagnosticVMOptions -cp /home/labile/pub-diy/jvm-insider-book/memory/java-obj-layout/out/production/java-obj-layout com.mygraphql.jvm.insider.safepoint.SafepointGDB'
```

### Reserve Memory Address

#### CodeCache

```
  char* addr = (char*)::mmap(requested_addr, bytes, PROT_NONE, flags, -1, 0);


libjvm.so!anon_mmap(char * requested_addr, size_t bytes) (/home/labile/opensource/jdk/src/hotspot/os/linux/os_linux.cpp:3423)
libjvm.so!os::pd_reserve_memory(size_t bytes, bool exec) (/home/labile/opensource/jdk/src/hotspot/os/linux/os_linux.cpp:3470)
libjvm.so!os::reserve_memory(size_t bytes, bool executable, MEMFLAGS flags) (/home/labile/opensource/jdk/src/hotspot/share/runtime/os.cpp:1756)
libjvm.so!map_or_reserve_memory(size_t size, int fd, bool executable) (/home/labile/opensource/jdk/src/hotspot/share/memory/virtualspace.cpp:95)
libjvm.so!reserve_memory(char * requested_address, const size_t size, const size_t alignment, int fd, bool exec) (/home/labile/opensource/jdk/src/hotspot/share/memory/virtualspace.cpp:170)
libjvm.so!ReservedSpace::reserve(ReservedSpace * const this, size_t size, size_t alignment, size_t page_size, char * requested_address, bool executable) (/home/labile/opensource/jdk/src/hotspot/share/memory/virtualspace.cpp:268)
libjvm.so!ReservedSpace::initialize(ReservedSpace * const this, size_t size, size_t alignment, size_t page_size, char * requested_address, bool executable) (/home/labile/opensource/jdk/src/hotspot/share/memory/virtualspace.cpp:300)
libjvm.so!ReservedCodeSpace::ReservedCodeSpace(ReservedCodeSpace * const this, size_t r_size, size_t rs_align, size_t rs_page_size) (/home/labile/opensource/jdk/src/hotspot/share/memory/virtualspace.cpp:662)
libjvm.so!CodeCache::reserve_heap_memory(size_t size) (/home/labile/opensource/jdk/src/hotspot/share/code/codeCache.cpp:362)
libjvm.so!CodeCache::initialize_heaps() (/home/labile/opensource/jdk/src/hotspot/share/code/codeCache.cpp:327)
libjvm.so!CodeCache::initialize() (/home/labile/opensource/jdk/src/hotspot/share/code/codeCache.cpp:1191)
libjvm.so!codeCache_init() (/home/labile/opensource/jdk/src/hotspot/share/code/codeCache.cpp:1214)
libjvm.so!init_globals() (/home/labile/opensource/jdk/src/hotspot/share/runtime/init.cpp:121)
libjvm.so!Threads::create_vm(JavaVMInitArgs * args, bool * canTryAgain) (/home/labile/opensource/jdk/src/hotspot/share/runtime/threads.cpp:549)
libjvm.so!JNI_CreateJavaVM_inner(JavaVM ** vm, void ** penv, void * args) (/home/labile/opensource/jdk/src/hotspot/share/prims/jni.cpp:3577)
libjvm.so!JNI_CreateJavaVM(JavaVM ** vm, void ** penv, void * args) (/home/labile/opensource/jdk/src/hotspot/share/prims/jni.cpp:3668)
libjli.so!InitializeJVM(JavaVM ** pvm, JNIEnv ** penv, InvocationFunctions * ifn) (/home/labile/opensource/jdk/src/java.base/share/native/libjli/java.c:1506)
libjli.so!JavaMain(void * _args) (/home/labile/opensource/jdk/src/java.base/share/native/libjli/java.c:415)
libjli.so!ThreadJavaMain(void * args) (/home/labile/opensource/jdk/src/java.base/unix/native/libjli/java_md.c:650)
start_thread(void * arg) (pthread_create.c:442)
```

#### GenCollectedHeap
```
  // Check for overflow.
  size_t total_reserved = _young_gen_spec->max_size() + _old_gen_spec->max_size();

  char* addr = (char*)::mmap(requested_addr, bytes, PROT_NONE, flags, -1, 0);

libjvm.so!anon_mmap(char * requested_addr, size_t bytes) (/home/labile/opensource/jdk/src/hotspot/os/linux/os_linux.cpp:3423)
libjvm.so!os::pd_reserve_memory(size_t bytes, bool exec) (/home/labile/opensource/jdk/src/hotspot/os/linux/os_linux.cpp:3470)
libjvm.so!os::reserve_memory(size_t bytes, bool executable, MEMFLAGS flags) (/home/labile/opensource/jdk/src/hotspot/share/runtime/os.cpp:1756)
libjvm.so!map_or_reserve_memory(size_t size, int fd, bool executable) (/home/labile/opensource/jdk/src/hotspot/share/memory/virtualspace.cpp:95)
libjvm.so!reserve_memory(char * requested_address, const size_t size, const size_t alignment, int fd, bool exec) (/home/labile/opensource/jdk/src/hotspot/share/memory/virtualspace.cpp:170)
libjvm.so!ReservedSpace::reserve(ReservedSpace * const this, size_t size, size_t alignment, size_t page_size, char * requested_address, bool executable) (/home/labile/opensource/jdk/src/hotspot/share/memory/virtualspace.cpp:268)
libjvm.so!ReservedSpace::initialize(ReservedSpace * const this, size_t size, size_t alignment, size_t page_size, char * requested_address, bool executable) (/home/labile/opensource/jdk/src/hotspot/share/memory/virtualspace.cpp:300)
libjvm.so!ReservedHeapSpace::ReservedHeapSpace(ReservedHeapSpace * const this, size_t size, size_t alignment, size_t page_size, const char * heap_allocation_directory) (/home/labile/opensource/jdk/src/hotspot/share/memory/virtualspace.cpp:636)
libjvm.so!Universe::reserve_heap(size_t heap_size, size_t alignment) (/home/labile/opensource/jdk/src/hotspot/share/memory/universe.cpp:874)
libjvm.so!GenCollectedHeap::allocate(GenCollectedHeap * const this, size_t alignment) (/home/labile/opensource/jdk/src/hotspot/share/gc/shared/genCollectedHeap.cpp:168)
libjvm.so!GenCollectedHeap::initialize(GenCollectedHeap * const this) (/home/labile/opensource/jdk/src/hotspot/share/gc/shared/genCollectedHeap.cpp:110)
libjvm.so!Universe::initialize_heap() (/home/labile/opensource/jdk/src/hotspot/share/memory/universe.cpp:843)
libjvm.so!universe_init() (/home/labile/opensource/jdk/src/hotspot/share/memory/universe.cpp:785)
libjvm.so!init_globals() (/home/labile/opensource/jdk/src/hotspot/share/runtime/init.cpp:124)
libjvm.so!Threads::create_vm(JavaVMInitArgs * args, bool * canTryAgain) (/home/labile/opensource/jdk/src/hotspot/share/runtime/threads.cpp:549)
libjvm.so!JNI_CreateJavaVM_inner(JavaVM ** vm, void ** penv, void * args) (/home/labile/opensource/jdk/src/hotspot/share/prims/jni.cpp:3577)
libjvm.so!JNI_CreateJavaVM(JavaVM ** vm, void ** penv, void * args) (/home/labile/opensource/jdk/src/hotspot/share/prims/jni.cpp:3668)
libjli.so!InitializeJVM(JavaVM ** pvm, JNIEnv ** penv, InvocationFunctions * ifn) (/home/labile/opensource/jdk/src/java.base/share/native/libjli/java.c:1506)
libjli.so!JavaMain(void * _args) (/home/labile/opensource/jdk/src/java.base/share/native/libjli/java.c:415)
libjli.so!ThreadJavaMain(void * args) (/home/labile/opensource/jdk/src/java.base/unix/native/libjli/java_md.c:650)  

```




### commit memory


```
  int prot = exec ? PROT_READ|PROT_WRITE|PROT_EXEC : PROT_READ|PROT_WRITE;
  uintptr_t res = (uintptr_t) ::mmap(addr, size, prot,
                                     MAP_PRIVATE|MAP_FIXED|MAP_ANONYMOUS, -1, 0);

__GI___mmap64(void * addr, size_t len, int prot, int flags, int fd, off64_t offset) (mmap64.c:47)
libjvm.so!os::Linux::commit_memory_impl(char * addr, size_t size, bool exec) (/home/labile/opensource/jdk/src/hotspot/os/linux/os_linux.cpp:2745)
libjvm.so!os::Linux::commit_memory_impl(char * addr, size_t size, size_t alignment_hint, bool exec) (/home/labile/opensource/jdk/src/hotspot/os/linux/os_linux.cpp:2800)
libjvm.so!os::pd_commit_memory(char * addr, size_t size, size_t alignment_hint, bool exec) (/home/labile/opensource/jdk/src/hotspot/os/linux/os_linux.cpp:2809)
libjvm.so!os::commit_memory(char * addr, size_t size, size_t alignment_hint, bool executable) (/home/labile/opensource/jdk/src/hotspot/share/runtime/os.cpp:1791)
libjvm.so!commit_expanded(char * start, size_t size, size_t alignment, bool pre_touch, bool executable) (/home/labile/opensource/jdk/src/hotspot/share/memory/virtualspace.cpp:829)
libjvm.so!VirtualSpace::expand_by(VirtualSpace * const this, size_t bytes, bool pre_touch) (/home/labile/opensource/jdk/src/hotspot/share/memory/virtualspace.cpp:926)
libjvm.so!VirtualSpace::initialize_with_granularity(VirtualSpace * const this, ReservedSpace rs, size_t committed_size, size_t max_commit_granularity) (/home/labile/opensource/jdk/src/hotspot/share/memory/virtualspace.cpp:732)
libjvm.so!VirtualSpace::initialize(VirtualSpace * const this, ReservedSpace rs, size_t committed_size) (/home/labile/opensource/jdk/src/hotspot/share/memory/virtualspace.cpp:689)
libjvm.so!CodeHeap::reserve(CodeHeap * const this, ReservedSpace rs, size_t committed_size, size_t segment_size) (/home/labile/opensource/jdk/src/hotspot/share/memory/heap.cpp:217)
libjvm.so!CodeCache::add_heap(ReservedSpace rs, const char * name, CodeBlobType code_blob_type) (/home/labile/opensource/jdk/src/hotspot/share/code/codeCache.cpp:447)
libjvm.so!CodeCache::initialize_heaps() (/home/labile/opensource/jdk/src/hotspot/share/code/codeCache.cpp:337)
libjvm.so!CodeCache::initialize() (/home/labile/opensource/jdk/src/hotspot/share/code/codeCache.cpp:1191)
libjvm.so!codeCache_init() (/home/labile/opensource/jdk/src/hotspot/share/code/codeCache.cpp:1214)
libjvm.so!init_globals() (/home/labile/opensource/jdk/src/hotspot/share/runtime/init.cpp:121)
libjvm.so!Threads::create_vm(JavaVMInitArgs * args, bool * canTryAgain) (/home/labile/opensource/jdk/src/hotspot/share/runtime/threads.cpp:549)
libjvm.so!JNI_CreateJavaVM_inner(JavaVM ** vm, void ** penv, void * args) (/home/labile/opensource/jdk/src/hotspot/share/prims/jni.cpp:3577)
libjvm.so!JNI_CreateJavaVM(JavaVM ** vm, void ** penv, void * args) (/home/labile/opensource/jdk/src/hotspot/share/prims/jni.cpp:3668)
libjli.so!InitializeJVM(JavaVM ** pvm, JNIEnv ** penv, InvocationFunctions * ifn) (/home/labile/opensource/jdk/src/java.base/share/native/libjli/java.c:1506)
libjli.so!JavaMain(void * _args) (/home/labile/opensource/jdk/src/java.base/share/native/libjli/java.c:415)
```

#### GenCollectedHeap
```
  int prot = exec ? PROT_READ|PROT_WRITE|PROT_EXEC : PROT_READ|PROT_WRITE;
  uintptr_t res = (uintptr_t) ::mmap(addr, size, prot,
                                     MAP_PRIVATE|MAP_FIXED|MAP_ANONYMOUS, -1, 0);

libjvm.so!os::Linux::commit_memory_impl(char * addr, size_t size, bool exec) (/home/labile/opensource/jdk/src/hotspot/os/linux/os_linux.cpp:2745)
libjvm.so!os::Linux::commit_memory_impl(char * addr, size_t size, size_t alignment_hint, bool exec) (/home/labile/opensource/jdk/src/hotspot/os/linux/os_linux.cpp:2800)
libjvm.so!os::pd_commit_memory(char * addr, size_t size, size_t alignment_hint, bool exec) (/home/labile/opensource/jdk/src/hotspot/os/linux/os_linux.cpp:2809)
libjvm.so!os::commit_memory(char * addr, size_t size, size_t alignment_hint, bool executable) (/home/labile/opensource/jdk/src/hotspot/share/runtime/os.cpp:1791)
libjvm.so!commit_expanded(char * start, size_t size, size_t alignment, bool pre_touch, bool executable) (/home/labile/opensource/jdk/src/hotspot/share/memory/virtualspace.cpp:829)
libjvm.so!VirtualSpace::expand_by(VirtualSpace * const this, size_t bytes, bool pre_touch) (/home/labile/opensource/jdk/src/hotspot/share/memory/virtualspace.cpp:926)
libjvm.so!VirtualSpace::initialize_with_granularity(VirtualSpace * const this, ReservedSpace rs, size_t committed_size, size_t max_commit_granularity) (/home/labile/opensource/jdk/src/hotspot/share/memory/virtualspace.cpp:732)
libjvm.so!VirtualSpace::initialize(VirtualSpace * const this, ReservedSpace rs, size_t committed_size) (/home/labile/opensource/jdk/src/hotspot/share/memory/virtualspace.cpp:689)
libjvm.so!Generation::Generation(Generation * const this, ReservedSpace rs, size_t initial_size) (/home/labile/opensource/jdk/src/hotspot/share/gc/shared/generation.cpp:46)
libjvm.so!DefNewGeneration::DefNewGeneration(DefNewGeneration * const this, ReservedSpace rs, size_t initial_size, size_t min_size, size_t max_size, const char * policy) (/home/labile/opensource/jdk/src/hotspot/share/gc/serial/defNewGeneration.cpp:336)
libjvm.so!GenerationSpec::init(GenerationSpec * const this, ReservedSpace rs, CardTableRS * remset) (/home/labile/opensource/jdk/src/hotspot/share/gc/shared/generationSpec.cpp:39)
libjvm.so!GenCollectedHeap::initialize(GenCollectedHeap * const this) (/home/labile/opensource/jdk/src/hotspot/share/gc/shared/genCollectedHeap.cpp:130)
libjvm.so!Universe::initialize_heap() (/home/labile/opensource/jdk/src/hotspot/share/memory/universe.cpp:843)
libjvm.so!universe_init() (/home/labile/opensource/jdk/src/hotspot/share/memory/universe.cpp:785)
libjvm.so!init_globals() (/home/labile/opensource/jdk/src/hotspot/share/runtime/init.cpp:124)
libjvm.so!Threads::create_vm(JavaVMInitArgs * args, bool * canTryAgain) (/home/labile/opensource/jdk/src/hotspot/share/runtime/threads.cpp:549)
libjvm.so!JNI_CreateJavaVM_inner(JavaVM ** vm, void ** penv, void * args) (/home/labile/opensource/jdk/src/hotspot/share/prims/jni.cpp:3577)
libjvm.so!JNI_CreateJavaVM(JavaVM ** vm, void ** penv, void * args) (/home/labile/opensource/jdk/src/hotspot/share/prims/jni.cpp:3668)
libjli.so!InitializeJVM(JavaVM ** pvm, JNIEnv ** penv, InvocationFunctions * ifn) (/home/labile/opensource/jdk/src/java.base/share/native/libjli/java.c:1506)
libjli.so!JavaMain(void * _args) (/home/labile/opensource/jdk/src/java.base/share/native/libjli/java.c:415)
```

#### Metaspace

直接 commit，不经过 reserve memory address。 因为其直接指定了地址，使用低地址，如 0x80040000 。原因


```
libjvm.so!metaspace::Metachunk::initialize(metaspace::Metachunk * const this, metaspace::VirtualSpaceNode * node, MetaWord * base, metaspace::chunklevel_t lvl) (/home/labile/opensource/jdk/src/hotspot/share/memory/metaspace/metachunk.hpp:327)
libjvm.so!metaspace::RootChunkArea::alloc_root_chunk_header(metaspace::RootChunkArea * const this, metaspace::VirtualSpaceNode * node) (/home/labile/opensource/jdk/src/hotspot/share/memory/metaspace/rootChunkArea.cpp:64)
libjvm.so!metaspace::VirtualSpaceNode::allocate_root_chunk(metaspace::VirtualSpaceNode * const this) (/home/labile/opensource/jdk/src/hotspot/share/memory/metaspace/virtualSpaceNode.cpp:322)
libjvm.so!metaspace::VirtualSpaceList::allocate_root_chunk(metaspace::VirtualSpaceList * const this) (/home/labile/opensource/jdk/src/hotspot/share/memory/metaspace/virtualSpaceList.cpp:134)
libjvm.so!metaspace::ChunkManager::get_chunk_locked(metaspace::ChunkManager * const this, metaspace::chunklevel_t preferred_level, metaspace::chunklevel_t max_level, size_t min_committed_words) (/home/labile/opensource/jdk/src/hotspot/share/memory/metaspace/chunkManager.cpp:186)
libjvm.so!metaspace::ChunkManager::get_chunk(metaspace::ChunkManager * const this, metaspace::chunklevel_t preferred_level, metaspace::chunklevel_t max_level, size_t min_committed_words) (/home/labile/opensource/jdk/src/hotspot/share/memory/metaspace/chunkManager.cpp:118)
libjvm.so!metaspace::MetaspaceArena::allocate_new_chunk(metaspace::MetaspaceArena * const this, size_t requested_word_size) (/home/labile/opensource/jdk/src/hotspot/share/memory/metaspace/metaspaceArena.cpp:93)
libjvm.so!metaspace::MetaspaceArena::allocate_inner(metaspace::MetaspaceArena * const this, size_t requested_word_size) (/home/labile/opensource/jdk/src/hotspot/share/memory/metaspace/metaspaceArena.cpp:313)
libjvm.so!metaspace::MetaspaceArena::allocate(metaspace::MetaspaceArena * const this, size_t requested_word_size) (/home/labile/opensource/jdk/src/hotspot/share/memory/metaspace/metaspaceArena.cpp:244)
libjvm.so!ClassLoaderMetaspace::allocate(ClassLoaderMetaspace * const this, size_t word_size, Metaspace::MetadataType mdType) (/home/labile/opensource/jdk/src/hotspot/share/memory/classLoaderMetaspace.cpp:96)
libjvm.so!Metaspace::allocate(ClassLoaderData * loader_data, size_t word_size, MetaspaceObj::Type type) (/home/labile/opensource/jdk/src/hotspot/share/memory/metaspace.cpp:907)
libjvm.so!Metaspace::allocate(ClassLoaderData * loader_data, size_t word_size, MetaspaceObj::Type type, JavaThread * __the_thread__) (/home/labile/opensource/jdk/src/hotspot/share/memory/metaspace.cpp:927)
libjvm.so!Array<Klass*>::operator new(size_t size, ClassLoaderData * loader_data, int length, JavaThread * __the_thread__) (/home/labile/opensource/jdk/src/hotspot/share/oops/array.inline.hpp:36)
libjvm.so!MetadataFactory::new_array<Klass*>(ClassLoaderData * loader_data, int length, JavaThread * __the_thread__) (/home/labile/opensource/jdk/src/hotspot/share/memory/metadataFactory.hpp:41)
libjvm.so!MetadataFactory::new_array<Klass*>(ClassLoaderData * loader_data, int length, Klass * value, JavaThread * __the_thread__) (/home/labile/opensource/jdk/src/hotspot/share/memory/metadataFactory.hpp:46)
libjvm.so!Universe::genesis(JavaThread * __the_thread__) (/home/labile/opensource/jdk/src/hotspot/share/memory/universe.cpp:345)
libjvm.so!universe2_init() (/home/labile/opensource/jdk/src/hotspot/share/memory/universe.cpp:973)
libjvm.so!init_globals2() (/home/labile/opensource/jdk/src/hotspot/share/runtime/init.cpp:150)
libjvm.so!Threads::create_vm(JavaVMInitArgs * args, bool * canTryAgain) (/home/labile/opensource/jdk/src/hotspot/share/runtime/threads.cpp:568)
libjvm.so!JNI_CreateJavaVM_inner(JavaVM ** vm, void ** penv, void * args) (/home/labile/opensource/jdk/src/hotspot/share/prims/jni.cpp:3577)
```

## Inspect



### pmap Linux command



### jcmd System.map

[The jcmd Command - OpenJDK23 - docs.oracle.com](https://docs.oracle.com/en/java/javase/23/docs/specs/man/jcmd.html)

> ## Synopsis
>
> `jcmd` [*pid* | *main-class*] *command*... | `PerfCounter.print` | `-f` *filename*
>
> `jcmd` [`-l`]
>
> ```
> jcmd` `-h
> ```
>
> 
>
> ## Commands for jcmd
>
> `System.map` \[_options_\] (Linux only)
>
> Prints an annotated process memory map of the VM process.
>
> Impact: Low
>
> **Note:**
>
> The following _options_ must be specified using either _key_ or _key_`=`_value_ syntax.
>
> _options_:
>
> - `-H`: (Optional) Human readable format (BOOLEAN, false)


```bash
/home/labile/opensource/jdk/build/linux-x86_64-server-slowdebug-hsdis/jdk/bin/jcmd 168171 System.map
```




### Java options:  -XX:+PrintMemoryMapAtExit

Java options:  `-XX:+PrintMemoryMapAtExit` .  Print an annotated memory map at exit.

[Understanding JVM Memory Layout with OpenJDK24’s New PrintMemoryMapAtExit VM Option - foojay.io - 2024](https://foojay.io/today/understanding-jvm-memory-layout-with-openjdk24s-new-printmemorymapatexit-vm-option/) :

```bash
java -XX:+UnlockDiagnosticVMOptions -XX:+PrintMemoryMapAtExit -XX:NativeMemoryTracking=summary ReadMappedFile
```



```
from               to                        vsize prot          rss      hugetlb pgsz notes            info                                  file
========================================================================================================================================================================
0x0000000689400000-0x00000006a0c00000    394264576 rw-p     17076224            0 4K   com              JAVAHEAP                              -
0x00000006a0c00000-0x00000007ffc00000   5888802816 ---p            0            0 4K   -                JAVAHEAP                              -
0x00000007ffc00000-0x00000007ffd21000      1183744 rw-p      1183744            0 4K   com              JAVAHEAP                              /big/jdks/jdk24/lib/server/classes.jsa
0x00000007ffd21000-0x0000000800000000      3010560 rw-p            0            0 4K   com              JAVAHEAP                              -
0x00007f0000000000-0x00007f0000d90000     14221312 rw-p     14098432            0 4K   com              CDS                                   /big/jdks/jdk24/lib/server/classes.jsa
0x00007f0000d90000-0x00007f0001000000      2555904 ---p            0            0 4K   -                CDS                                   -
0x00007f0001000000-0x00007f0001010000        65536 rw-p        28672            0 4K   com              CLASS                                 -
0x00007f0001010000-0x00007f0001040000       196608 ---p            0            0 4K   -                CLASS                                 -
0x00007f0001040000-0x00007f0001050000        65536 rw-p        36864            0 4K   com              CLASS                                 -
0x00007f0001050000-0x00007f0041000000   1073414144 ---p            0            0 4K   -                CLASS                                 -
0x0000b49b739f0000-0x0000b49b739f1000         4096 r-xp         4096            0 4K   com              -                                     /big/jdks/jdk24/bin/java
0x0000b49b73a01000-0x0000b49b73a02000         4096 r--p         4096            0 4K   com              -                                     /big/jdks/jdk24/bin/java
0x0000b49b73a02000-0x0000b49b73a03000         4096 rw-p         4096            0 4K   com              -                                     /big/jdks/jdk24/bin/java
0x0000b49ba384e000-0x0000b49ba3881000       208896 rw-p       159744            0 4K   com              -                                     [heap]
...
0x0000ec2570000000-0x0000ec25700b0000       720896 rw-p       712704            0 4K   com              META                                  -
0x0000ec25700b0000-0x0000ec2570400000      3473408 ---p            0            0 4K   -                META                                  -
...
0x0000ec2580fbf000-0x0000ec2580fcf000        65536 ---p            0            0 4K   com              -                                     -
0x0000ec2580fcf000-0x0000ec25811cd000      2088960 rw-p        12288            0 4K   com              STACK-1696938-GC-Thread               -
0x0000ec25811cd000-0x0000ec25811dd000        65536 ---p            0            0 4K   com              -                                     -
0x0000ec25811dd000-0x0000ec25813db000      2088960 rw-p        12288            0 4K   com              STACK-1696937-GC-Thread               -
0x0000ec25813db000-0x0000ec25813eb000        65536 ---p            0            0 4K   com              -                                     -
0x0000ec25813eb000-0x0000ec25815e9000      2088960 rw-p        12288            0 4K   com              STACK-1696936-GC-Thread               -
0x0000ec25815e9000-0x0000ec25815ed000        16384 ---p            0            0 4K   -                -                                     -
0x0000ec25815ed000-0x0000ec25817e7000      2072576 rw-p        32768            0 4K   com              -                                     -
0x0000ec2581808000-0x0000ec258180c000        16384 ---p            0            0 4K   com              STACK-1696934-Common-Cleaner          -
0x0000ec258180c000-0x0000ec2581a06000      2072576 rw-p        94208            0 4K   com              STACK-1696934-Common-Cleaner          -
0x0000ec2581a06000-0x0000ec2581a0a000        16384 ---p            0            0 4K   com              STACK-1696933-Notification-Thread     -
0x0000ec2581a0a000-0x0000ec2581c04000      2072576 rw-p        12288            0 4K   com              STACK-1696933-Notification-Thread     -
0x0000ec2581c04000-0x0000ec2581c08000        16384 ---p            0            0 4K   com              STACK-1696932-C1-CompilerThread0      -
0x0000ec2581c08000-0x0000ec2581e02000      2072576 rw-p        20480            0 4K   com              STACK-1696932-C1-CompilerThread0      -
0x0000ec2581e02000-0x0000ec2581e06000        16384 ---p            0            0 4K   com              STACK-1696931-C2-CompilerThread0      -
0x0000ec2581e06000-0x0000ec2584000000     35627008 rw-p        32768            0 4K   com              GC                                    -
0x0000ec2584000000-0x0000ec2584021000       135168 rw-p         4096            0 4K   -                -                                     -
0x0000ec2584021000-0x0000ec2588000000     66973696 ---p            0            0 4K   -                -                                     -
0x0000ec2588000000-0x0000ec2588021000       135168 rw-p         4096            0 4K   -                -                                     -
0x0000ec2588021000-0x0000ec258c000000     66973696 ---p            0            0 4K   -                -                                     -
0x0000ec258c000000-0x0000ec258c021000       135168 rw-p        12288            0 4K   -                -                                     -
0x0000ec258c021000-0x0000ec2590000000     66973696 ---p            0            0 4K   -                -                                     -
0x0000ec2590020000-0x0000ec259002c000        49152 r-xp        49152            0 4K   com              -                                     /big/jdks/jdk24/lib/libnet.so
0x0000ec259002c000-0x0000ec259003b000        61440 ---p            0            0 4K   com              -                                     /big/jdks/jdk24/lib/libnet.so
0x0000ec259003b000-0x0000ec259003c000         4096 r--p         4096            0 4K   com              -                                     /big/jdks/jdk24/lib/libnet.so
0x0000ec259003c000-0x0000ec259003d000         4096 rw-p         4096            0 4K   com              -                                     /big/jdks/jdk24/lib/libnet.so
0x0000ec2590040000-0x0000ec2590044000        16384 ---p            0            0 4K   com              STACK-1696930-Monitor-Deflation-Thread -
0x0000ec2590044000-0x0000ec259023e000      2072576 rw-p        12288            0 4K   com              STACK-1696930-Monitor-Deflation-Thread -
0x0000ec259023e000-0x0000ec2590242000        16384 ---p            0            0 4K   com              STACK-1696929-Service-Thread          -
0x0000ec2590242000-0x0000ec259043c000      2072576 rw-p        12288            0 4K   com              STACK-1696929-Service-Thread          -
0x0000ec259043c000-0x0000ec2590440000        16384 ---p            0            0 4K   com              STACK-1696928-Signal-Dispatcher       -
0x0000ec2590440000-0x0000ec259063a000      2072576 rw-p        12288            0 4K   com              STACK-1696928-Signal-Dispatcher       -
0x0000ec259063a000-0x0000ec259063e000        16384 ---p            0            0 4K   com              STACK-1696927-Finalizer               -
0x0000ec259063e000-0x0000ec2590838000      2072576 rw-p        90112            0 4K   com              STACK-1696927-Finalizer               -
0x0000ec2590838000-0x0000ec259083c000        16384 ---p            0            0 4K   com              STACK-1696926-Reference-Handler       -
0x0000ec259083c000-0x0000ec2590a36000      2072576 rw-p        94208            0 4K   com              STACK-1696926-Reference-Handler       -
0x0000ec2590a36000-0x0000ec2590a46000        65536 ---p            0            0 4K   com              -                                     -
0x0000ec2590a46000-0x0000ec2590c44000      2088960 rw-p        16384            0 4K   com              STACK-1696925-VM-Thread               -
...
0x0000ec2591470000-0x0000ec2591480000        65536 ---p            0            0 4K   com              -                                     -
0x0000ec2591480000-0x0000ec259167e000      2088960 rw-p        12288            0 4K   com              STACK-1696921-GC-Thread               -
0x0000ec259167e000-0x0000ec259168e000        65536 ---p            0            0 4K   com              -                                     -
0x0000ec259168e000-0x0000ec259188c000      2088960 rw-p        12288            0 4K   com              -                                     -
0x0000ec259188c000-0x0000ec259189c000        65536 ---p            0            0 4K   com              -                                     -
0x0000ec259189c000-0x0000ec259207a000      8249344 rw-p        12288            0 4K   com              STACK-1696919-GC-Thread,GC            -
0x0000ec259207a000-0x0000ec259783a000     92012544 ---p            0            0 4K   -                GC                                    -
0x0000ec259783a000-0x0000ec2597906000       835584 rw-p       770048            0 4K   com              GC                                    -
0x0000ec2597906000-0x0000ec25983fe000     11501568 ---p            0            0 4K   -                GC                                    -
0x0000ec25983fe000-0x0000ec2598400000         8192 rw-p         8192            0 4K   com              GC                                    -
0x0000ec2598400000-0x0000ec2598670000      2555904 rwxp       651264            0 4K   com              CODE                                  -
0x0000ec2598670000-0x0000ec259f937000    120352768 ---p            0            0 4K   -                CODE                                  -
0x0000ec259f937000-0x0000ec259fba7000      2555904 rwxp       626688            0 4K   com              CODE                                  -
0x0000ec259fba7000-0x0000ec259fec7000      3276800 ---p            0            0 4K   -                CODE                                  -
0x0000ec259fec7000-0x0000ec25a0137000      2555904 rwxp       237568            0 4K   com              CODE                                  -
0x0000ec25a0137000-0x0000ec25a7400000    120360960 ---p            0            0 4K   -                CODE                                  -
0x0000ec25a7400000-0x0000ec25afe3e000    144957440 r--s      1114112            0 4K   com              -                                     /big/jdks/jdk24/lib/modules
0x0000ec25afe40000-0x0000ec25afe50000        65536 r--s        65536            0 4K   com              -                                     /tmp/bigfile
```



- 变更跟踪：[Provide a diagnostic PrintMemoryMapAtExit switch on Linux - Enhancement issue on bugs.openjdk.org](https://bugs.openjdk.org/browse/JDK-8334026?page=com.atlassian.jira.plugin.system.issuetabpanels%3Acomment-tabpanel)


