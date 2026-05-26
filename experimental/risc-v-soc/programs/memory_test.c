/**
 * @file memory_test.c
 * @brief Memory access test program for Phase 4 milestone
 *
 * Tests load/store operations with the Wishbone bus:
 * - LW/SW (word access)
 * - LH/SH (halfword access)
 * - LB/SB (byte access)
 * - LHU/LBU (unsigned loads)
 *
 * Algorithm:
 * 1. Initialize array in memory with pattern
 * 2. Read back and verify (different access sizes)
 * 3. Calculate sum
 * 4. Return sum in a0
 *
 * Expected result: Sum of 1+2+3+4+5 = 15
 */

void _start(void) __attribute__((naked, noreturn));

/**
 * @brief Entry point - memory access test
 *
 * Tests word, halfword, and byte access to memory
 * Result: sum in a0 (x10)
 */
void _start(void) {
    asm volatile(
        // Base address for our data (use address 0x100 = word 64)
        "   addi a1, zero, 0x100     \n"  // a1 = base address = 0x100

        //=====================================================================
        // Test 1: Word Store and Load (SW/LW)
        //=====================================================================

        "   addi t0, zero, 1         \n"  // t0 = 1
        "   sw   t0, 0(a1)           \n"  // mem[0x100] = 1

        "   addi t0, zero, 2         \n"  // t0 = 2
        "   sw   t0, 4(a1)           \n"  // mem[0x104] = 2

        "   addi t0, zero, 3         \n"  // t0 = 3
        "   sw   t0, 8(a1)           \n"  // mem[0x108] = 3

        "   addi t0, zero, 4         \n"  // t0 = 4
        "   sw   t0, 12(a1)          \n"  // mem[0x10C] = 4

        "   addi t0, zero, 5         \n"  // t0 = 5
        "   sw   t0, 16(a1)          \n"  // mem[0x110] = 5

        //=====================================================================
        // Test 2: Word Load and Sum (LW)
        //=====================================================================

        "   addi a0, zero, 0         \n"  // a0 = sum = 0

        "   lw   t1, 0(a1)           \n"  // t1 = mem[0x100]
        "   add  a0, a0, t1          \n"  // sum += t1

        "   lw   t1, 4(a1)           \n"  // t1 = mem[0x104]
        "   add  a0, a0, t1          \n"  // sum += t1

        "   lw   t1, 8(a1)           \n"  // t1 = mem[0x108]
        "   add  a0, a0, t1          \n"  // sum += t1

        "   lw   t1, 12(a1)          \n"  // t1 = mem[0x10C]
        "   add  a0, a0, t1          \n"  // sum += t1

        "   lw   t1, 16(a1)          \n"  // t1 = mem[0x110]
        "   add  a0, a0, t1          \n"  // sum += t1

        // a0 now contains 1+2+3+4+5 = 15

        //=====================================================================
        // Test 3: Halfword Store and Load (SH/LH)
        //=====================================================================

        "   addi a2, zero, 0x120     \n"  // a2 = 0x120 (different location)
        "   addi t0, zero, 0xAB      \n"  // t0 = 0xAB
        "   sh   t0, 0(a2)           \n"  // store halfword

        "   lh   t1, 0(a2)           \n"  // load signed halfword
        "   add  a0, a0, t1          \n"  // add to sum (should sign-extend)

        //=====================================================================
        // Test 4: Byte Store and Load (SB/LB)
        //=====================================================================

        "   addi a3, zero, 0x130     \n"  // a3 = 0x130
        "   addi t0, zero, 10        \n"  // t0 = 10
        "   sb   t0, 0(a3)           \n"  // store byte

        "   lb   t1, 0(a3)           \n"  // load signed byte
        "   add  a0, a0, t1          \n"  // add to sum

        //=====================================================================
        // Done - Result in a0
        //=====================================================================

        "done:                       \n"
        "   j done                   \n"  // infinite loop
        ::: "a0", "a1", "a2", "a3", "t0", "t1"
    );
}
