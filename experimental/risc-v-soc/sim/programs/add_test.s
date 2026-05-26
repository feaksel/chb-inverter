# add_test.s
# Simple test program for RISC-V core
# Tests basic ADD instructions

.section .text
.global _start

_start:
    # Test 1: ADD x1, x0, x0 (x1 = 0 + 0 = 0)
    add  x1, x0, x0

    # Test 2: ADDI x2, x0, 10 (x2 = 0 + 10 = 10)
    addi x2, x0, 10

    # Test 3: ADDI x3, x0, 20 (x3 = 0 + 20 = 20)
    addi x3, x0, 20

    # Test 4: ADD x4, x2, x3 (x4 = 10 + 20 = 30)
    add  x4, x2, x3

    # Test 5: SUB x5, x4, x2 (x5 = 30 - 10 = 20)
    sub  x5, x4, x2

    # Test 6: ADDI x6, x5, -5 (x6 = 20 + (-5) = 15)
    addi x6, x5, -5

    # Infinite loop (for simulation)
loop:
    j loop

.section .data
# No data section needed for this test
