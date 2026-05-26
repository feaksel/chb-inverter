/**
 * @file linker.ld
 * @brief Linker script for bare-metal RISC-V programs
 *
 * Maps program to start at address 0x00000000
 */

OUTPUT_ARCH("riscv")
ENTRY(_start)

MEMORY {
    RAM (rwx) : ORIGIN = 0x00000000, LENGTH = 1K
}

SECTIONS {
    .text : {
        *(.text._start)      /* _start MUST be first */
        *(.text.factorial)   /* Then factorial */
        *(.text.multiply_add) /* Then multiply_add */
        *(.text*)            /* Then everything else */
    } > RAM

    .data : {
        *(.data*)
    } > RAM

    .bss : {
        *(.bss*)
        *(COMMON)
    } > RAM
}
