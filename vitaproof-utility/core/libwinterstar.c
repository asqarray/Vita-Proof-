#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <x86intrin.h>

static inline uint64_t read_cycles(void) {
    unsigned int aux;
    return __rdtscp(&aux);
}

uint64_t run_state_collapse(const float* buffer, size_t count, uint32_t* out_raw_bits) {
    if (!buffer || count == 0) {
        if (out_raw_bits) *out_raw_bits = 0;
        return 1;
    }

    uint64_t start_cycles = read_cycles();

    // 50-pass AVX2 vector state collapse
    __m256 state_vec = _mm256_setzero_ps();
    for (int pass = 0; pass < 50; ++pass) {
        size_t i = 0;
        for (; i + 7 < count; i += 8) {
            __m256 chunk = _mm256_loadu_ps(&buffer[i + (pass % 8)]);
            state_vec = _mm256_add_ps(state_vec, chunk);
            state_vec = _mm256_mul_ps(state_vec, _mm256_set1_ps(1.000001f));
        }
    }

    // Horizontal reduction
    float result_array[8];
    _mm256_storeu_ps(result_array, state_vec);
    float final_state = 0.0f;
    for (int k = 0; k < 8; ++k) {
        final_state += result_array[k];
    }

    uint64_t end_cycles = read_cycles();
    uint64_t total_cycles = (end_cycles > start_cycles) ? (end_cycles - start_cycles) : 1;

    if (out_raw_bits) {
        uint32_t bits;
        memcpy(&bits, &final_state, sizeof(uint32_t));
        *out_raw_bits = bits;
    }

    return total_cycles;
}
