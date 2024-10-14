# jhsdb 

## 命令示例

### Inspect JavaThread

```
hsdb> threads
513811 main
State: BLOCKED
Stack in use by Java: 0x00007ffff5285740 .. 0x00007ffff5285830
Base of Stack: 0x00007ffff5287000
Last_Java_SP: 0x00007ffff5285740
Last_Java_FP: null
Last_Java_PC: 0x00007fffed72c9af
Thread id: 513811

hsdb> threadcontext 513811
Thread "main" id=513811 Address=0x00007ffff002b3c0
```

Open `Tools->Inspector` input address "0x00007ffff002b3c0". or use command:
```
hsdb> inspect 0x00007ffff002b3c0
Type is JavaThread (size of 1904)
oop ThreadShadow::_pending_exception: null
char* ThreadShadow::_exception_file: char @ null
int ThreadShadow::_exception_line: 0
ThreadLocalAllocBuffer Thread::_tlab: ThreadLocalAllocBuffer @ 0x00007ffff002b580
jlong Thread::_allocated_bytes: 0
ResourceArea* Thread::_resource_area: ResourceArea @ 0x00007ffff0018ba0
LockStack JavaThread::_lock_stack: LockStack @ 0x00007ffff002bae8
OopHandle JavaThread::_threadObj: OopHandle @ 0x00007ffff002b770
OopHandle JavaThread::_vthread: OopHandle @ 0x00007ffff002b778
OopHandle JavaThread::_jvmti_vthread: OopHandle @ 0x00007ffff002b780
OopHandle JavaThread::_scopedValueCache: OopHandle @ 0x00007ffff002b788
JavaFrameAnchor JavaThread::_anchor: JavaFrameAnchor @ 0x00007ffff002b798
oop JavaThread::_vm_result: null
Metadata* JavaThread::_vm_result_2: Metadata @ null
ObjectMonitor* JavaThread::_current_pending_monitor: ObjectMonitor @ null
bool JavaThread::_current_pending_monitor_is_from_java: 1
ObjectMonitor* JavaThread::_current_waiting_monitor: ObjectMonitor @ null
uint32_t JavaThread::_suspend_flags: 0
oop JavaThread::_exception_oop: null
address JavaThread::_exception_pc: address @ 0x00007ffff002b918
int JavaThread::_is_method_handle_return: 0
address JavaThread::_saved_exception_pc: address @ 0x00007ffff002b868
JavaThreadState JavaThread::_thread_state: 10
OSThread* JavaThread::_osthread: OSThread @ 0x00007ffff002d9a0
address JavaThread::_stack_base: address @ 0x00007ffff002b718
size_t JavaThread::_stack_size: 1048576
vframeArray* JavaThread::_vframe_array_head: vframeArray @ null
vframeArray* JavaThread::_vframe_array_last: vframeArray @ 0x00007ffff031da90
JNIHandleBlock* JavaThread::_active_handles: JNIHandleBlock @ 0x00007ffff01686f0
JavaThread::TerminatedTypes JavaThread::_terminated: 57002
```

