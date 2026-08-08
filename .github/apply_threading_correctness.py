from pathlib import Path


def replace_once(path: str, old: str, new: str) -> None:
    p = Path(path)
    text = p.read_text()
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"expected exactly one match in {path}, found {count}")
    p.write_text(text.replace(old, new, 1))


replace_once(
    "src/polesitter.h",
    "#endif // POLESITTER_H\n\n#define POLESITTER_IMPLEMENTATION\n#ifdef POLESITTER_IMPLEMENTATION",
    "#endif // POLESITTER_H\n\n#ifdef POLESITTER_IMPLEMENTATION",
)

replace_once(
    "src/polesitter.h",
    """#if defined(__x86_64__) || defined(__i386__) || defined(_M_X64) ||             \\
    defined(_M_IX86)\n\n#define PS_YIELD() _mm_pause()\n#elif defined(__aarch64__) || defined(_M_ARM64) || defined(__arm__)\n#define PS_YIELD() __asm__ volatile(\"yield\" ::: \"memory\")\n#else\n#define PS_YIELD()\n#endif""",
    """#if defined(__x86_64__) || defined(__i386__) || defined(_M_X64) ||             \\
    defined(_M_IX86)\n\n#ifdef _WIN32\n#define PS_YIELD() YieldProcessor()\n#else\n#define PS_YIELD() __asm__ volatile(\"pause\" ::: \"memory\")\n#endif\n#elif defined(__aarch64__) || defined(_M_ARM64) || defined(__arm__)\n#define PS_YIELD() __asm__ volatile(\"yield\" ::: \"memory\")\n#else\n#define PS_YIELD()\n#endif""",
)

replace_once(
    "src/polesitter.h",
    """    ps_job_t     queue[PS_MAX_JOBS];\n    volatile int hd;\n    volatile int tl;\n    volatile int cnt;\n    volatile int active_jobs;\n    volatile int shutdown_flag;\n\n    ps_spinlock_t lock;""",
    """    ps_job_t queue[PS_MAX_JOBS];\n    int      hd;\n    int      tl;\n    int      cnt;\n    int      active_jobs;\n    int      shutdown_flag;\n\n    ps_spinlock_t lock;""",
)

replace_once(
    "src/polesitter.h",
    """        // block if buffer is full\n        while (pool->cnt == PS_MAX_JOBS && !pool->shutdown_flag) {\n            PS_YIELD();\n        }\n\n        // enqueue\n        ps_spin_lock(&pool->lock);\n        pool->queue[pool->tl] = job;\n        pool->tl              = (pool->tl + 1) % PS_MAX_JOBS;\n        pool->cnt++;\n        ps_spin_unlock(&pool->lock);\n        return;""",
    """        // Queue state is shared with workers; inspect and update it only\n        // while holding the spinlock. volatile does not make these accesses\n        // atomic or establish inter-thread ordering in C.\n        while (1) {\n            ps_spin_lock(&pool->lock);\n\n            if (pool->shutdown_flag) {\n                ps_spin_unlock(&pool->lock);\n                return;\n            }\n\n            if (pool->cnt < PS_MAX_JOBS) {\n                pool->queue[pool->tl] = job;\n                pool->tl              = (pool->tl + 1) % PS_MAX_JOBS;\n                pool->cnt++;\n                ps_spin_unlock(&pool->lock);\n                return;\n            }\n\n            ps_spin_unlock(&pool->lock);\n            PS_YIELD();\n        }""",
)

replace_once(
    "src/polesitter.h",
    """    while (1) {\n        if (pool->cnt == 0 && pool->active_jobs == 0) {\n\n            ps_spin_lock(&pool->lock);\n            int done = (pool->cnt == 0 && pool->active_jobs == 0);\n            ps_spin_unlock(&pool->lock);\n\n            if (done)\n                return;\n        }\n        PS_YIELD();\n    }""",
    """    while (1) {\n        ps_spin_lock(&pool->lock);\n        int done = (pool->cnt == 0 && pool->active_jobs == 0);\n        ps_spin_unlock(&pool->lock);\n\n        if (done) {\n            return;\n        }\n\n        PS_YIELD();\n    }""",
)

replace_once(
    "src/polesitter.h",
    """    while (1) {\n        while (pool->cnt == 0 && !pool->shutdown_flag) {\n            PS_YIELD();\n        }\n\n        ps_spin_lock(&pool->lock);\n\n        if (pool->cnt == 0) {\n            ps_spin_unlock(&pool->lock);\n            if (pool->shutdown_flag) {\n                break;\n            }\n\n            continue;\n        }\n\n        // dequeue\n        ps_job_t job = pool->queue[pool->hd];\n        pool->hd     = (pool->hd + 1) % PS_MAX_JOBS;\n\n        pool->active_jobs++;\n        pool->cnt--;\n        ps_spin_unlock(&pool->lock);""",
    """    while (1) {\n        ps_spin_lock(&pool->lock);\n\n        if (pool->cnt == 0) {\n            int shutdown = pool->shutdown_flag;\n            ps_spin_unlock(&pool->lock);\n\n            if (shutdown) {\n                break;\n            }\n\n            PS_YIELD();\n            continue;\n        }\n\n        // dequeue\n        ps_job_t job = pool->queue[pool->hd];\n        pool->hd     = (pool->hd + 1) % PS_MAX_JOBS;\n\n        pool->active_jobs++;\n        pool->cnt--;\n        ps_spin_unlock(&pool->lock);""",
)

replace_once(
    "tests/accuracy.c",
    """            printf(\"[%s] Force mismatch at array index %zu (ID %u): \"\n                   \"ST(%.2f,%.2f,%.2f) MT(%.2f,%.2f,%.2f)\",\n                   phase, i, st->id[i], st->fx[i], st->fy[i], st->fz[i],\n                   mt->fx[i], mt->fy[i], mt->fz[i]);\n\n            if (mismatches >= 5) {""",
    """            printf(\"[%s] Force mismatch at array index %zu (ID %u): \"\n                   \"ST(%.2f,%.2f,%.2f) MT(%.2f,%.2f,%.2f)\",\n                   phase, i, st->id[i], st->fx[i], st->fy[i], st->fz[i],\n                   mt->fx[i], mt->fy[i], mt->fz[i]);\n            mismatches++;\n\n            if (mismatches >= 5) {""",
)

replace_once(
    "README.md",
    """Include the header in one C file with `POLESITTER_IMPLEMENTATION` defined.\n\n```c\n#define POLESITTER_IMPLEMENTATION\n#include \"polesitter.h\"\n```""",
    """Include the header in one C file with `POLESITTER_IMPLEMENTATION` defined. Define `PS_MULTITHREADING` as well when using more than one thread.\n\n```c\n#define PS_MULTITHREADING\n#define POLESITTER_IMPLEMENTATION\n#include \"polesitter.h\"\n```""",
)

replace_once(
    "README.md",
    """#include <stdint.h>\n#include <stdlib.h>""",
    """#include <stdbool.h>\n#include <stdint.h>\n#include <stdlib.h>""",
)

replace_once(
    "README.md",
    """    // initialize the context\n    ps_config_t cfg = { memory_block, MEMORY_SIZE };\n    ps_context_t* ctx = NULL;\n    ps_init(&ctx, &cfg);""",
    """    // initialize the context\n    ps_config_t cfg = {\n        .buff = memory_block,\n        .buff_size = MEMORY_SIZE,\n        .max_particles = PARTICLE_CNT,\n        .theta = 2.0F,\n        .thrd_cnt = 4,\n    };\n    ps_context_t* ctx = NULL;\n    ps_init(&ctx, &cfg);""",
)

replace_once(
    "README.md",
    """        // reset arena and force accumulators for the new frame\n        ps_arena_clear(&ctx->arena);\n        for (int i = 0; i < PARTICLE_CNT; ++i) {""",
    """        // reset IDs and force accumulators for the new frame\n        for (int i = 0; i < PARTICLE_CNT; ++i) {""",
)

replace_once(
    "README.md",
    """    // cleanup\n    free(memory_block);\n    return 0;""",
    """    // cleanup\n    ps_destroy(ctx);\n    free(memory_block);\n    return 0;""",
)
