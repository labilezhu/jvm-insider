---
typora-root-url: ../../
---

# JVM Launcher

这里说的 JVM Launcher，既包括 java.exe ，也包括 jstack / jcmd / jps / jconsole 等等基于 java 的 native execute file 入口。



## JVM Launcher 示例分析 - java.exe



> 以下参考了：[HotSpot Runtime Overview - Launcher - openjdk.org](https://openjdk.org/groups/hotspot/docs/RuntimeOverview.html#Command-Line%20Argument%20Processing|outline)



There are several HotSpot VM launchers in the Java Standard Edition, the general purpose launcher typically used is the `java` command on Unix and on Windows java and javaw commands.

The launcher operations pertaining to VM startup are:

1. Parse the command line options.
   - some of the command line options are consumed by the launcher itself, for example `-client` or `-server` is used to determine and load the appropriate VM library, 
   - others are passed to the VM using `JavaVMInitArgs`.
2. Establish(确定) the heap sizes and the compiler type (client or server) if these options are not explicitly specified on the command line.
3. Establish(确定) the environment variables such as `LD_LIBRARY_PATH` and `CLASSPATH`.
4. If the java Main-Class is not specified on the command line, fetch the Main-Class name from the JAR's manifest.
5. Create the VM using `JNI_CreateJavaVM` in a newly created thread (non primordial thread). Note: creating the VM in the primordial thread greatly reduces the ability to customize the VM, for example the stack size on Windows, and many other limitations
6. Once the VM is created and initialized, the Main-Class is loaded, and the launcher gets the main method's attributes from the Main-Class.
7. The java main method is then invoked in the VM using `CallStaticVoidMethod`, using the marshalled arguments from the command line.
8. Once the java main method completes, its very important to check and clear any pending exceptions that may have occurred and also pass back the exit status, the exception is cleared by calling `ExceptionOccurred`, the return value of this method is 0 if successful, any other value otherwise, this value is passed back to the calling process.
9. The `main thread` is detached using `DetachCurrentThread`, by doing so we decrement the thread count so the `DestroyJavaVM` can be called safely, also to ensure that the thread is not performing operations in the vm and that there are no active java frames on its stack.

The most important phases are the `JNI_CreateJavaVM` and `DestroyJavaVM` these are described in the next sections.

### JNI_CreateJavaVM

The JNI invocation method performs the following:

1. Ensures that no two threads call this method at the same time and that no two VM instances are created in the same process. Noting that a VM cannot be created in the same process space once a point in initialization is reached, “point of no return”. This is so because the VM creates static data structures that cannot be re-initialized, at this time.
2. Checks to make sure the JNI version is supported, and the ostream is initialized for gc logging. The OS modules are initialized such as the random number generator, the current pid, high-resolution time, memory page sizes, and the **guard pages**.
3. The arguments and properties passed in are parsed and stored away for later use. The standard java system properties are initialized.
4. The OS modules are further created and initialized, based on the parsed arguments and properties, are initialized for synchronization, stack, memory, and `safepoint pages`. At this time other libraries such as libzip, libhpi, libjava, libthread are loaded, signal handlers are initialized and set, and the thread library is initialized.
5. The output stream logger is initialized. Any agent libraries (hprof, jdi) required are initialized and started.
6. The thread states and the thread local storage (TLS), which holds several thread specific data required for the operation of threads, are initialized.
7. The global data is initialized as part of the I phase, such as event log, OS synchronization primitives, perfMemory (performance memory), chunkPool (memory allocator).
8. At this point, we can create Threads. **The Java version of the main thread is created and attached to the current OS thread**. However this thread will not be yet added to the known list of the Threads. The Java level synchronization is initialized and enabled.
9. The rest of the global modules are initialized such as the BootClassLoader, CodeCache, Interpreter, Compiler, JNI, SystemDictionary, and Universe. Noting that, we have reached our “point of no return”, ie. we can no longer create another VM in the same process address space.
10. The main thread is added to the list, by first locking the `Thread_Lock`. The Universe, a set of required global data structures, is sanity checked. The `VMThread`, which performs all the VM's critical functions, is created. At this point the appropriate JVMTI events are posted to notify the current state.
11. The following classes java.lang.String, java.lang.System, java.lang.Thread, java.lang.ThreadGroup, java.lang.reflect.Method, java.lang.ref.Finalizer, java.lang.Class, and the rest of the System classes, are loaded and initialized. At this point, the VM is initialized and operational, but not yet fully functional.
12. The Signal Handler thread is started, the compilers are initialized and the `CompileBroker thread` is started. The other helper threads StatSampler and WatcherThreads are started, at this time the VM is fully functional, the `JNIEnv` is populated and returned to the caller, and the VM is ready to service new JNI requests.

### DestroyJavaVM

This method can be called from the launcher to tear down the VM, it can also be called by the VM itself when a very serious error occurs.

The tear down of the VM takes the following steps:

1. Wait until we are the last non-daemon thread to execute, noting that the VM is still functional.
2. Call `java.lang.Shutdown.shutdown(),` which will invoke Java level shutdown hooks, run finalizers if finalization-on-exit.

1. Call `before_exit()`, prepare for VM exit, run VM level shutdown hooks (they are registered through `JVM_OnExit()`), stop the Profiler, StatSampler, Watcher and GC threads. Post the status events to JVMTI/PI, disable JVMPI, and stop the Signal thread.

1. Call `JavaThread::exit()`, to release JNI handle blocks, remove stack guard pages, and remove this thread from Threads list. From this point on we cannot execute any more Java code.
2. Stop `VM thread`, it will bring the remaining VM to a safepoint and stop the `compiler threads`. At a safepoint, care should that we should not use anything that could get blocked by a Safepoint.
3. Disable tracing at JNI/JVM/JVMPI barriers.
4. Set `_vm_exited` flag for threads that are still running native code.
5. Delete this thread.
6. Call `exit_globals()`, which deletes IO and PerfMemory resources.
7. Return to caller.







## Java Launcher 示例分析 - jstack

下面以 jstack 应用程序为例，说明一下 Java Launcher 的 JNI 使用。


:::{figure-md} 图: Java Launcher 示例: jstack.exe

<img src="/native-interface/launcher/launcher.drawio.svg" alt="图: Java Launcher 示例: jstack.exe">

*图: Java Launcher 示例: jstack.exe*
:::
*[用 Draw.io 打开](https://app.diagrams.net/?ui=sketch#Uhttps%3A%2F%2Fjvm-insider.mygraphql.com%2Fzh-cn%2Flatest%2F_images%2Flauncher.drawio.svg)*


当我了解到 jstack.exe 甚至是 java.exe 本身其实都是利用 JNI API 去嵌入 JVM(libjvm.so) 时，是有点开眼界的。其实 Java 设计之初就是支持桌面应用，Native Application 可以轻松嵌入 JVM。只是作为现在主流的后端开发界来说，已经很少提这个“初心”了。
