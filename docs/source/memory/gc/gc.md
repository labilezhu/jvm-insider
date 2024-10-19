# GC

src/hotspot/share/gc/shared/genCollectedHeap.cpp

```c++
void GenCollectedHeap::do_collection(bool           full,
                                     bool           clear_all_soft_refs,
                                     size_t         size,
                                     bool           is_tlab,
                                     GenerationType max_generation) {
...
  if (do_young_collection) {
    GCIdMark gc_id_mark;
    GCTraceCPUTime tcpu(((DefNewGeneration*)_young_gen)->gc_tracer());
    GCTraceTime(Info, gc) t("Pause Young", nullptr, gc_cause(), true);

    print_heap_before_gc();

    if (run_verification && VerifyGCLevel <= 0 && VerifyBeforeGC) {
      prepare_for_verify();
      prepared_for_verification = true;
    }

    gc_prologue(complete);
    increment_total_collections(complete);

    collect_generation(_young_gen,
                       full,
                       size,
                       is_tlab,
                       run_verification && VerifyGCLevel <= 0,
                       do_clear_all_soft_refs);
```