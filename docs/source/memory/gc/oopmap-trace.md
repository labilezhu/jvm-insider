# OopMap

## GC oop trace

[src/hotspot/share/runtime/javaThread.hpp](https://github.com/openjdk/jdk//blob/890adb6410dab4606a4f26a942aed02fb2f55387/src/hotspot/share/runtime/javaThread.hpp#L244)

```c++
class JavaThread: public Thread {
...
  // Active_handles points to a block of handles
  JNIHandleBlock* _active_handles;
...
  JavaFrameAnchor _anchor;                       // Encapsulation of current java frame and it state
```



[src/hotspot/share/runtime/javaFrameAnchor.hpp](https://github.com/openjdk/jdk//blob/890adb6410dab4606a4f26a942aed02fb2f55387/src/hotspot/share/runtime/javaFrameAnchor.hpp#L40)

```c++
class JavaFrameAnchor {
...
 private:
  //
  // Whenever _last_Java_sp != nullptr other anchor fields MUST be valid!
  // The stack may not be walkable [check with walkable() ] but the values must be valid.
  // The profiler apparently depends on this.
  //
  intptr_t* volatile _last_Java_sp;

  // Whenever we call from Java to native we can not be assured that the return
  // address that composes the last_Java_frame will be in an accessible location
  // so calls from Java to native store that pc (or one good enough to locate
  // the oopmap) in the frame anchor. Since the frames that call from Java to
  // native are never deoptimized we never need to patch the pc and so this
  // is acceptable.
  volatile  address _last_Java_pc;

  // tells whether the last Java frame is set
  // It is important that when last_Java_sp != nullptr that the rest of the frame
  // anchor (including platform specific) all be valid.

  bool has_last_Java_frame() const                   { return _last_Java_sp != nullptr; }
```





> [来自: HotSpot JVM Deep Dive - Safepoint](https://www.youtube.com/watch?v=JkbWPPNc4SI&ab_channel=Java)
>
> Global jvm state the second clause was that thread local gc routes for all java threads are accessible or published to the jvm. All current garbage collectors are tracing collectors which means they follow or trace the reachability trees starting out from what is called a root set. That is a set of immediately available oops. 
>
> Proper subset of the route set is the set of routes that is local to and reachable from java threads.
>
> 
>
> Let's take a look at what some of these thread local gc routes are.
>
> 
>
> ###  oop Handles
>
> - Local jni handles
>
>   A `JavaThread` has a field called `JNIHandleBlock* _active_handles`. A `local jni handle` provides indirect access to an `oop` for jni code running in `state native` . But allocating/deallocating and even dereferencing a jni handle involve first performing a `vm state transition` which will perform a safe point check.  `Local jni handles` are auto managed so when the code returns from a jni method that is it transitions from `state native` doing a safe point check into `state java` the `local jni handles` allocated by that method are deallocated. 
>
> - HandleArea *(missed in OpenJDK21)*
>
>   The `JavaThread` also has a field called `handle area` and handle area and its companion the handle provides pretty much the same indirection functionality as a `local jni handle` but these are targeted for code running in the `vm state`.  The important difference is that these handles are NOT auto managed but instead must be manually managed by the openjdk programmer. `Handle marks` are used to describe a `handle scope`. And the `handle mark` destructor will deallocate the allocated handles for that particular scope and the scopes can also be nested.
>
> ### Last Java Frame
>
> The thread also has an embedded struct called the `JavaFrameAnchor _anchor` field. It consists of three pointers:
>
> - `_last_Java_sp` for last java stack pointer 
>
> - `_last_Java_pc` for last java program counter
>
> - `_last_Java_fp`*(missed in OpenJDK21, because of virtual thread ?)* for last java frame pointer. the last java frame is the entry point for external stack walking. It is set if a thread has at least one java activation record or frame on its stack and it's currently not in `state java`. So the `_last_Java_fp` is set in `state java` before the thread transitions out. And conversely it is cleared upon thread reentry. 
>
> The anchor struct here requires only that the `last java stack pointer` is set as the other fields are either not relevant for that context or they can be derived by the stack walking code. 
>
> Java frames on the stack may contain `ordinary narrow oops` or `derived oops`. So if you compared to the handles we discussed previously these are naked oops that is they do not have a handling direction they are direct pointers. 
>
> - An `ordinary oop` is a regular oop, 
> - a `narrow oop` is a compressed version of an oop it's a 32-bit size oop. 
> - And the `derived oop` is a pointer into an object not pointing directly to its header. 
>
> So for example we can think of an a pointer that points out an element in an array and a `derived oop` is always associated with a base for a specific code position in java for a specific code position like a` program counter` which stack slots and registers contain oops relative to that `pc` is described by a piece of metadata generated by the compilers something called an `oop map`. 
>
> For a specific code position (pc), which stack slots and registers contain oops is described by a piece of metadata generated by the compilers, called an `OopMap`. To pinpoint an oop in a frame, the `OopMap` describes a location using a relative address, either from the `frame stackpointer (sp)` or as an index into a `RegisterMap`. Not all code positions have `OopMaps`; mainly call sites and safepoint poll page instructions. For stackwalks, the return address of each frame is associated with an `OopMap`.
>
> ### JavaThread CPU Context
>
> A thread executing Java code also has a CPU context. Per the calling convention and performance reasons, oops are ideally placed in registers. Hotspot widely employs something called `Stubs` or `StubRoutines`, which are special platform-specific assembly helper routines. An important feature of most `Stubs` is to save the CPU context when a thread leaves, or suspends its Java execution, and restoring it when the thread re-enters, resuming execution. A `Register Map` is used to resolve a location described by an `OopMap` to be in a register. 

