#include <stdio.h>
#include <stdint.h>
#include <immintrin.h>

void execute_pouw_matrix_task(const float* input_matrix, float* output_matrix, size_t count) {
    __m256 v_threshold = _mm256_set1_ps(0.02719f);

    for (size_t i = 0; i < count; i += 8) {
        __m256 v_data = _mm256_loadu_ps(&input_matrix[i]);
        __m256 v_mask = _mm256_cmp_ps(v_data, v_threshold, _CMP_GE_OQ);
        __m256 v_result = _mm256_and_ps(v_data, v_mask);
        _mm256_storeu_ps(&output_matrix[i], v_result);
    }
}

int main() {
    printf("VITAPROOF Bare-Metal Worker Daemon v1.0 Started.\n");
    printf("Ready to process matrix workloads and generate YAZ PoUW proofs.\n");
    return 0;
}
