#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <x86intrin.h>

static inline uint64_t read_cycles(void) {
    unsigned int aux;
    return __rdtscp(&aux);
}

int main() {
    size_t capacity = 100000;
    size_t count = 0;
    float *buffer = (float *)malloc(capacity * sizeof(float));

    // 1. Dynamic stream reading from stdin (no truncation cap)
    float chunk_buf[1024];
    size_t n;
    while ((n = fread(chunk_buf, sizeof(float), 1024, stdin)) > 0) {
        if (count + n > capacity) {
            capacity *= 2;
            buffer = (float *)realloc(buffer, capacity * sizeof(float));
        }
        for (size_t k = 0; k < n; ++k) {
            buffer[count + k] = chunk_buf[k];
        }
        count += n;
    }

    if (count == 0) {
        free(buffer);
        printf("VP_SIMD_ACCUMULATOR_00000000:1\n");
        return 0;
    }

    uint64_t start_cycles = read_cycles();

    // 2. Iterative AVX2 State-Collapse Loop (50 compute passes per state)
    __m256 state_vec = _mm256_setzero_ps();
    for (int pass = 0; pass < 50; ++pass) {
        size_t i = 0;
        for (; i + 7 < count; i += 8) {
            __m256 chunk = _mm256_loadu_ps(&buffer[i + (pass % 8)]);
            state_vec = _mm256_add_ps(state_vec, chunk);
            state_vec = _mm256_mul_ps(state_vec, _mm256_set1_ps(1.000001f)); // State transformation
        }
    }

    // Horizontal reduction
    float result_array[8];
    _mm256_storeu_ps(result_array, state_vec);
    float final_state = 0.0f;
    for (int k = 0; k < 8; ++k) final_state += result_array[k];

    uint64_t end_cycles = read_cycles();
    uint64_t total_cycles = (end_cycles > start_cycles) ? (end_cycles - start_cycles) : 1;

    uint32_t raw_bits;
    __builtin_memcpy(&raw_bits, &final_state, sizeof(raw_bits));
    printf("VP_SIMD_ACCUMULATOR_%08X:%lu\n", raw_bits, total_cycles);

    free(buffer);
    return 0;
}
