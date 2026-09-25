#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <immintrin.h>

#define VECTOR_SIZE 10000000

int main() {
    float *a = (float *)aligned_alloc(32, VECTOR_SIZE * sizeof(float));
    float *b = (float *)aligned_alloc(32, VECTOR_SIZE * sizeof(float));
    float *c = (float *)aligned_alloc(32, VECTOR_SIZE * sizeof(float));

    for (int i = 0; i < VECTOR_SIZE; i++) {
        a[i] = 1.0f + (i % 100) * 0.01f;
        b[i] = 2.0f + (i % 50) * 0.02f;
    }

    struct timespec start, end;
    clock_gettime(CLOCK_MONOTONIC, &start);

    for (int i = 0; i < VECTOR_SIZE; i += 8) {
        __m256 va = _mm256_load_ps(&a[i]);
        __m256 vb = _mm256_load_ps(&b[i]);
        __m256 vc = _mm256_mul_ps(va, vb);
        _mm256_store_ps(&c[i], vc);
    }

    clock_gettime(CLOCK_MONOTONIC, &end);

    double elapsed_ms = (end.tv_sec - start.tv_sec) * 1000.0 + 
                         (end.tv_nsec - start.tv_nsec) / 1000000.0;
    double gflops = (VECTOR_SIZE / (elapsed_ms / 1000.0)) / 1e9;

    printf("{\"status\":\"SUCCESS\",\"latency_ms\":%.2f,\"gflops\":%.2f}\n", elapsed_ms, gflops);

    free(a); free(b); free(c);
    return 0;
}
