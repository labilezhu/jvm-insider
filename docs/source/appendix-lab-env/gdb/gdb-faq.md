# GDB JVM FAQ


(attach-process)=
## attach process

### ptrace attach process

默认的 Linux 配置下， attach 一个进程， gdb/vscode 使用的 ptrace 要求 root 用户。VSCode 在启动 debug 时，会说: "Superuser access is required to attach to a process" 。
以下配置可以不使用 root 用户：

```bash
echo 0 | sudo tee /proc/sys/kernel/yama/ptrace_scope

# and then, after I'm done :
echo 1 | sudo tee /proc/sys/kernel/yama/ptrace_scope
```

如果想修改永久化，使用：
```bash
vi /etc/sysctl.d/10-ptrace.conf 

kernel.yama.ptrace_scope = 0
```

### gdb attach 外部启动的 jvm 并观察 jvm 初始化

有时间，出于环境变量等等理由，不能用 gdb 在启动 jvm 。要在一个 terminal 中启动 JVM 。但又要在 jvm 启动前设置好断点，并观察 JVM 的启动过程。这时， bash 的 exec 可以救命。

```bash
$ bash
$ echo $$
709394
# Now in other terminal/window: gdb --pid 709394
$ exec java ... MyMainClass
# Happy gdb java
```


## signal handle
```
# Disable stopping on signals handled by the JVM
(gdb) handle SIGSEGV noprint nostop
```


## C++

(inspect-object-layout)=
### Inspect Object Layout

```
(gdb) ptype /xo 'Thread'
/* offset      |    size */  type = class Thread : public ThreadShadow {
                             private:
                               static class Thread *_thr_current;
/* 0x0020      |  0x0008 */    uint64_t _nmethod_disarmed_guard_value;
/* 0x0028      |  0x0158 */    GCThreadLocalData _gc_data;
...


(gdb) ptype /xo 'JavaThread'
/* offset      |    size */  type = class JavaThread : public Thread {
/* 0x03b8      |  0x0008 */    class OopHandle {
                                 private:
/* 0x03b8      |  0x0008 */        oop *_obj;

                                   /* total size (bytes):    8 */
                               } _vthread;

...
                             public:
/* 0x048c      |  0x0004 */    volatile enum JavaThreadState _thread_state;
                             private:
/* 0x0490      |  0x0010 */    struct SafepointMechanism::ThreadData {
/* 0x0490      |  0x0008 */        volatile uintptr_t _polling_word;
/* 0x0498      |  0x0008 */        volatile uintptr_t _polling_page;

                                   /* total size (bytes):   16 */
                               } _poll_data;
/* 0x04a0      |  0x0008 */    class ThreadSafepointState *_safepoint_state;
/* 0x04a8      |  0x0008 */    address _saved_exception_pc;



```

> - https://sourceware.org/gdb/current/onlinedocs/gdb.html/Memory.html
> - https://sourceware.org/gdb/current/onlinedocs/gdb.html/Output-Formats.html



#### Inspect Java Thread

```
(gdb) p *((JavaThread*)0x00007ffff002b3c0)
```

## JavaThread

### JavaThread Iterator

```c++
    JavaThreadIteratorWithHandle jtiwh;
      for (JavaThread* thr = jtiwh.next(); thr != nullptr; thr = jtiwh.next()) {
      }
```

要 gdb watch `JavaThread` 的 tid :
```
thr->_osthread._thread_id
```
