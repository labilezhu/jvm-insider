# JVM 内部锁

## JVM 全局锁

[src/hotspot/share/runtime/mutexLocker.hpp](https://github.com/openjdk/jdk//blob/890adb6410dab4606a4f26a942aed02fb2f55387/src/hotspot/share/runtime/mutexLocker.hpp#L51)

```c++
extern Mutex*   CompiledIC_lock;                 // a lock used to guard compiled IC patching and access
extern Monitor* JNICritical_lock;                // a lock used while entering and exiting JNI critical regions, allows GC to sometimes get in
extern Mutex*   JvmtiThreadState_lock;           // a lock on modification of JVMTI thread data
extern Monitor* EscapeBarrier_lock;              // a lock to sync reallocating and relocking objects because of JVMTI access
extern Monitor* Heap_lock;                       // a lock on the heap
extern Monitor* CodeCache_lock;                  // a lock on the CodeCache
extern Monitor* VMOperation_lock;                // a lock on queue of vm_operations waiting to execute
extern Monitor* Threads_lock;                    // a lock on the Threads table of active Java threads
extern Mutex*   Metaspace_lock;                  // protects Metaspace virtualspace and chunk expansions

```


## JVM Mutex

[src/hotspot/share/runtime/mutex.hpp](https://github.com/openjdk/jdk//blob/890adb6410dab4606a4f26a942aed02fb2f55387/src/hotspot/share/runtime/mutex.hpp#L51)
```c++
// A Mutex/Monitor is a simple wrapper around a native lock plus condition
// variable that supports lock ownership tracking, lock ranking for deadlock
// detection and coordinates with the safepoint protocol.

// Locking is non-recursive: if you try to lock a mutex you already own then you
// will get an assertion failure in a debug build (which should suffice to expose
// usage bugs). If you call try_lock on a mutex you already own it will return false.
// The underlying PlatformMutex may support recursive locking but this is not exposed
// and we account for that possibility in try_lock.

// A thread is not allowed to safepoint while holding a mutex whose rank
// is nosafepoint or lower.

class Mutex : public CHeapObj<mtSynchronizer> {
...
 private:
  // The _owner field is only set by the current thread, either to itself after it has acquired
  // the low-level _lock, or to null before it has released the _lock. Accesses by any thread other
  // than the lock owner are inherently racy.
  Thread* volatile _owner;
  void raw_set_owner(Thread* new_owner) { Atomic::store(&_owner, new_owner); }

 protected:                              // Monitor-Mutex metadata
  PlatformMonitor _lock;                 // Native monitor implementation
  const char* _name;                     // Name of mutex/monitor

  // Debugging fields for naming, deadlock detection, etc. (some only used in debug mode)
#ifndef PRODUCT
  bool    _allow_vm_block;
#endif
#ifdef ASSERT
  Rank    _rank;                 // rank (to avoid/detect potential deadlocks)
  Mutex*  _next;                 // Used by a Thread to link up owned locks
  Thread* _last_owner;           // the last thread to own the lock
  bool _skip_rank_check;         // read only by owner when doing rank checks

  static Mutex* get_least_ranked_lock(Mutex* locks);
  Mutex* get_least_ranked_lock_besides_this(Mutex* locks);
  bool skip_rank_check() {
    assert(owned_by_self(), "only the owner should call this");
    return _skip_rank_check;
  }

 public:
  Rank   rank() const          { return _rank; }
  const char*  rank_name() const;
  Mutex* next()  const         { return _next; }
#endif // ASSERT

 protected:
  void set_owner_implementation(Thread* owner)                        NOT_DEBUG({ raw_set_owner(owner);});
  void check_block_state       (Thread* thread)                       NOT_DEBUG_RETURN;
  void check_safepoint_state   (Thread* thread)                       NOT_DEBUG_RETURN;
  void check_no_safepoint_state(Thread* thread)                       NOT_DEBUG_RETURN;
  void check_rank              (Thread* thread)                       NOT_DEBUG_RETURN;
  void assert_owner            (Thread* expected)                     NOT_DEBUG_RETURN;

 public:
  static const bool _allow_vm_block_flag        = true;

  // Locks can be acquired with or without a safepoint check. NonJavaThreads do not follow
  // the safepoint protocol when acquiring locks.

  // Each lock can be acquired by only JavaThreads, only NonJavaThreads, or shared between
  // Java and NonJavaThreads. When the lock is initialized with rank > nosafepoint,
  // that means that whenever the lock is acquired by a JavaThread, it will verify that
  // it is done with a safepoint check. In corollary, when the lock is initialized with
  // rank <= nosafepoint, that means that whenever the lock is acquired by a JavaThread
  // it will verify that it is done without a safepoint check.

  // TODO: Locks that are shared between JavaThreads and NonJavaThreads
  // should never encounter a safepoint check while they are held, or else a
  // deadlock can occur. We should check this by noting which
  // locks are shared, and walk held locks during safepoint checking.

  enum class SafepointCheckFlag {
    _safepoint_check_flag,
    _no_safepoint_check_flag
  };
  // Bring the enumerator names into class scope.
  static const SafepointCheckFlag _safepoint_check_flag =
    SafepointCheckFlag::_safepoint_check_flag;
  static const SafepointCheckFlag _no_safepoint_check_flag =
    SafepointCheckFlag::_no_safepoint_check_flag;

 public:
  Mutex(Rank rank, const char *name, bool allow_vm_block);

  Mutex(Rank rank, const char *name) :
    Mutex(rank, name, rank > nosafepoint ? false : true) {}

  ~Mutex();

  void lock(); // prints out warning if VM thread blocks
  void lock(Thread *thread); // overloaded with current thread
  void unlock();
  bool is_locked() const                     { return owner() != nullptr; }

  bool try_lock(); // Like lock(), but unblocking. It returns false instead
 private:
  void lock_contended(Thread *thread); // contended slow-path
  bool try_lock_inner(bool do_rank_checks);
 public:

  void release_for_safepoint();

  // Lock without safepoint check. Should ONLY be used by safepoint code and other code
  // that is guaranteed not to block while running inside the VM.
  void lock_without_safepoint_check();
  void lock_without_safepoint_check(Thread* self);
  // A thread should not call this if failure to acquire ownership will blocks its progress
  bool try_lock_without_rank_check();

  // Current owner - note not MT-safe. Can only be used to guarantee that
  // the current running thread owns the lock
  Thread* owner() const         { return Atomic::load(&_owner); }
  void set_owner(Thread* owner) { set_owner_implementation(owner); }
  bool owned_by_self() const;

  const char *name() const                  { return _name; }

  void print_on_error(outputStream* st) const;
  #ifndef PRODUCT
    void print_on(outputStream* st) const;
    void print() const;
  #endif
  ...
}
```

## JVM Monitor

[src/hotspot/share/runtime/mutex.hpp](https://github.com/openjdk/jdk//blob/890adb6410dab4606a4f26a942aed02fb2f55387/src/hotspot/share/runtime/mutex.hpp#L51)
```c++
class Monitor : public Mutex {
 public:
  Monitor(Rank rank, const char *name, bool allow_vm_block)  :
    Mutex(rank, name, allow_vm_block) {}

  Monitor(Rank rank, const char *name) :
    Mutex(rank, name) {}
  // default destructor

  // Wait until monitor is notified (or times out).
  // Defaults are to make safepoint checks, wait time is forever (i.e.,
  // zero). Returns true if wait times out; otherwise returns false.
  bool wait(uint64_t timeout = 0);
  bool wait_without_safepoint_check(uint64_t timeout = 0);
  void notify();
  void notify_all();
};
```

