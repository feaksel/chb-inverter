/**
 * @file factorial.c
 * @brief Simple factorial program for RISC-V core testing
 *
 * Calculates factorial(5) = 120
 * Uses only RV32I base instructions (no multiply)
 */

// Prevent compiler from adding standard library dependencies
void _start(void) __attribute__((naked, noreturn));

/**
 * @brief Multiply two numbers using only addition
 *
 * @param a First operand
 * @param b Second operand
 * @return a * b
 */
int multiply_add(int a, int b) {
    volatile int result = 0;
    volatile int i;

    for (i = 0; i < b; i++) {
        result = result + a;
    }

    return result;
}

/**
 * @brief Calculate factorial using only addition (no multiply)
 *
 * Since we don't have the M extension (multiply), we implement
 * multiplication using repeated addition.
 *
 * @param n Input number
 * @return n! (factorial of n)
 */
int factorial(int n) {
    volatile int result = 1;
    volatile int current = n;

    while (current > 1) {
        result = multiply_add(result, current);
        current = current - 1;
    }

    return result;
}

/**
 * @brief Entry point - calculate factorial(5)
 *
 * Result should be stored in register a0 (x10) = 120
 */
void _start(void) {
    register int result asm("a0");

    result = factorial(5);

    // Infinite loop - halt execution
    while (1) {
        asm volatile("nop");
    }
}
