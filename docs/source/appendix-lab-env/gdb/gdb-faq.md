# GDB JVM FAQ

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

