#include <immintrin.h>
#include <stdint.h>
#include <stdlib.h>

void avx2_state_collapse(const float* input, float* output, size_t count, int passes) {
    size_t vec_size = count - (count % 8);
    for (int p = 0; p < passes; p++) {
        for (size_t i = 0; i < vec_size; i += 8) {
            __m256 v = _mm256_loadu_ps(&input[i]);
            __m256 v2 = _mm256_mul_ps(v, v);
            __m256 res = _mm256_fmadd_ps(v, v2, v);
            _mm256_storeu_ps(&output[i], res);
        }
    }
}
