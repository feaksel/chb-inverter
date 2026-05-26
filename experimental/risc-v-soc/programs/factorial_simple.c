/**
 * @file factorial_simple.c
 * @brief Simple factorial program - all code in _start
 *
 * Calculates factorial(5) = 120
 * Uses only RV32I base instructions (no multiply)
 * No function calls - everything inline in _start
 */

void _start(void) __attribute__((naked, noreturn));

/**
 * @brief Entry point - calculate factorial(5) inline
 *
 * Result stored in register a0 (x10) = 120
 */
void _start(void) {
    asm volatile(
        // Calculate factorial(5) using only RV32I instructions
        // result = 1, n = 5

        "   addi a0, zero, 1   \n"  // a0 = result = 1
        "   addi a1, zero, 5   \n"  // a1 = n = 5

        "outer_loop:           \n"
        "   addi t0, zero, 1   \n"  // t0 = 1 (to compare with)
        "   ble  a1, t0, done  \n"  // if n <= 1, we're done

        // Multiply result (a0) by n (a1) using repeated addition
        "   addi t1, a0, 0     \n"  // t1 = temp = result
        "   addi a0, zero, 0   \n"  // result = 0
        "   addi t2, a1, 0     \n"  // t2 = counter = n

        "inner_loop:           \n"
        "   beq  t2, zero, end_inner \n"  // if counter == 0, exit inner loop
        "   add  a0, a0, t1    \n"  // result += temp
        "   addi t2, t2, -1    \n"  // counter--
        "   j    inner_loop    \n"  // repeat

        "end_inner:            \n"
        "   addi a1, a1, -1    \n"  // n--
        "   j    outer_loop    \n"  // repeat outer loop

        "done:                 \n"
        // a0 now contains factorial(5) = 120
        // Infinite loop
        "loop_forever:         \n"
        "   j loop_forever     \n"
        ::: "a0", "a1", "t0", "t1", "t2"
    );
}
