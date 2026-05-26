# CSR Implementation Quick Checklist

**Quick Reference for Implementing CSR, Exceptions, Interrupts, and Compliance**

---

## Phase 1: CSR Unit (8-10 hours)

### Implementation

- [ ] Create `rtl/core/csr_unit.v`
- [ ] Implement CSR registers:
  - [ ] mstatus (status register)
  - [ ] mie (interrupt enable)
  - [ ] mip (interrupt pending)
  - [ ] mtvec (trap vector)
  - [ ] mscratch (scratch register)
  - [ ] mepc (exception PC)
  - [ ] mcause (trap cause)
  - [ ] mtval (trap value)
  - [ ] mcycle / mcycleh (cycle counter)
  - [ ] minstret / minstreth (instruction counter)
- [ ] Implement CSR read logic
- [ ] Implement CSR write logic (RW, RS, RC operations)
- [ ] Implement trap entry logic (save PC, disable interrupts)
- [ ] Implement trap return logic (restore state, enable interrupts)
- [ ] Implement trap vector calculation (direct/vectored mode)

### Testing

- [ ] Create `sim/testbenches/tb_csr_unit.v`
- [ ] Test: Read read-only registers (MISA, MVENDORID)
- [ ] Test: Write and read mstatus
- [ ] Test: CSRRS (set bits)
- [ ] Test: CSRRC (clear bits)
- [ ] Test: Trap entry (save state)
- [ ] Test: Trap return (restore state)
- [ ] Test: Interrupt pending detection
- [ ] Test: Performance counters increment

**Deliverable:** Working CSR unit that passes all tests

---

## Phase 2: Exception Handling (6-8 hours)

### Implementation

- [ ] Create `rtl/core/exception_unit.v`
- [ ] Detect instruction address misaligned (PC not 4-byte aligned)
- [ ] Detect illegal instruction
- [ ] Detect breakpoint (EBREAK)
- [ ] Detect load address misaligned
- [ ] Detect load access fault (bus error)
- [ ] Detect store address misaligned
- [ ] Detect store access fault
- [ ] Detect ECALL instruction
- [ ] Generate exception_taken signal
- [ ] Generate exception_cause code
- [ ] Generate exception_val (bad address/instruction)

### Testing

- [ ] Test: Illegal instruction triggers exception
- [ ] Test: Misaligned load triggers exception
- [ ] Test: Misaligned store triggers exception
- [ ] Test: ECALL triggers exception
- [ ] Test: EBREAK triggers exception
- [ ] Test: Exception saves PC correctly
- [ ] Test: Exception jumps to trap handler
- [ ] Test: Exception disables interrupts

**Deliverable:** Exception detection working, traps to handler

---

## Phase 3: Interrupt Handling (8-10 hours)

### Implementation

- [ ] Create `rtl/core/interrupt_controller.v`
- [ ] Connect timer interrupt input
- [ ] Connect external interrupt input
- [ ] Connect software interrupt input
- [ ] Connect peripheral interrupt inputs
- [ ] Implement interrupt pending register
- [ ] Implement interrupt enable masking
- [ ] Implement priority encoder (external > software > timer)
- [ ] Generate interrupt_req signal
- [ ] Generate interrupt_cause code

### Testing

- [ ] Create `sim/testbenches/tb_interrupt_controller.v`
- [ ] Test: Interrupt disabled when global enable = 0
- [ ] Test: Timer interrupt triggers when enabled
- [ ] Test: External interrupt triggers when enabled
- [ ] Test: Priority: external > software > timer
- [ ] Test: Interrupt clears when source removed
- [ ] Test: Multiple interrupts handled by priority

**Deliverable:** Interrupt controller working with priority

---

## Phase 4: System Instructions (4-6 hours)

### Implementation in Decoder

- [ ] Detect OPCODE_SYSTEM (7'b1110011)
- [ ] Decode funct3:
  - [ ] 000: Privileged (ECALL, EBREAK, MRET, WFI)
  - [ ] 001: CSRRW (read/write)
  - [ ] 010: CSRRS (read and set)
  - [ ] 011: CSRRC (read and clear)
  - [ ] 101: CSRRWI (read/write immediate)
  - [ ] 110: CSRRSI (read and set immediate)
  - [ ] 111: CSRRCI (read and clear immediate)
- [ ] Decode funct12 for privileged:
  - [ ] 0x000: ECALL
  - [ ] 0x001: EBREAK
  - [ ] 0x302: MRET
  - [ ] 0x105: WFI
- [ ] Generate control signals:
  - [ ] is_ecall, is_ebreak, is_mret, is_wfi
  - [ ] is_csr, csr_op, csr_addr

### Implementation in Core

- [ ] Handle ECALL in execute stage (trigger exception)
- [ ] Handle EBREAK in execute stage (trigger exception)
- [ ] Handle MRET in execute stage (restore state, jump to mepc)
- [ ] Handle WFI in execute stage (stall until interrupt)
- [ ] Handle CSR instructions:
  - [ ] Read CSR → rd
  - [ ] Modify CSR (RW/RS/RC)
  - [ ] Write CSR
- [ ] Connect CSR unit to core
- [ ] Connect decoder to CSR unit

### Testing

- [ ] Test: CSRRW reads old value and writes new
- [ ] Test: CSRRS sets bits
- [ ] Test: CSRRC clears bits
- [ ] Test: CSR immediate variants work
- [ ] Test: ECALL triggers exception with correct cause
- [ ] Test: EBREAK triggers exception with correct cause
- [ ] Test: MRET returns to mepc
- [ ] Test: WFI stalls until interrupt

**Deliverable:** All system instructions working

---

## Phase 5: Integration (10-15 hours)

### Core Modifications

- [ ] Add STATE_TRAP to state machine
- [ ] Add trap entry logic to state machine:
  - [ ] Check for interrupts before fetch
  - [ ] Check for exceptions after execute
  - [ ] Assert trap_entry signal
  - [ ] Save trap_pc, trap_cause, trap_val
  - [ ] Jump to trap_vector
- [ ] Add trap return logic:
  - [ ] Detect MRET instruction
  - [ ] Assert trap_return signal
  - [ ] Load PC from mepc
- [ ] Connect exception_unit:
  - [ ] Feed PC, instruction, mem_addr
  - [ ] Feed bus_error from Wishbone
  - [ ] Read exception_taken, exception_cause
- [ ] Connect interrupt_controller:
  - [ ] Feed interrupt inputs
  - [ ] Feed global_int_en, mie from CSR
  - [ ] Read interrupt_req, interrupt_cause
- [ ] Connect csr_unit:
  - [ ] CSR address from decoder
  - [ ] CSR write data from rs1 or zimm
  - [ ] CSR operation from decoder
  - [ ] CSR read data to rd
  - [ ] Trap entry/return signals
  - [ ] Interrupt inputs
  - [ ] Performance counter signals

### Testing

- [ ] Write integration test program:
  - [ ] Setup trap vector
  - [ ] Enable interrupts
  - [ ] Trigger exception (illegal instruction)
  - [ ] Verify trap handler called
  - [ ] Verify state saved correctly
  - [ ] Return from trap
  - [ ] Trigger interrupt
  - [ ] Verify interrupt handler called
  - [ ] Clear interrupt and return
- [ ] Run test and check waveforms
- [ ] Verify all signals correct
- [ ] Verify timing correct

**Deliverable:** Fully integrated core with traps working

---

## Phase 6: Compliance Testing (5-10 hours)

### Setup

- [ ] Clone RISC-V compliance test repository
  ```bash
  cd verification
  git clone https://github.com/riscv/riscv-arch-test.git
  ```
- [ ] Create test harness for your core
- [ ] Write run_compliance.sh script
- [ ] Configure test parameters

### Test Categories

**RV32I Base Integer (40 tests)**

Arithmetic:
- [ ] ADD, ADDI
- [ ] SUB
- [ ] LUI, AUIPC

Logic:
- [ ] AND, ANDI
- [ ] OR, ORI
- [ ] XOR, XORI

Shifts:
- [ ] SLL, SLLI
- [ ] SRL, SRLI
- [ ] SRA, SRAI

Comparisons:
- [ ] SLT, SLTI
- [ ] SLTU, SLTIU

Branches:
- [ ] BEQ, BNE
- [ ] BLT, BGE
- [ ] BLTU, BGEU

Jumps:
- [ ] JAL, JALR

Memory:
- [ ] LW, LH, LB
- [ ] LHU, LBU
- [ ] SW, SH, SB

Fence (can be NOP):
- [ ] FENCE
- [ ] FENCE.I

**RV32M Extension (8 tests)**

Multiply:
- [ ] MUL
- [ ] MULH
- [ ] MULHSU
- [ ] MULHU

Divide:
- [ ] DIV
- [ ] DIVU
- [ ] REM
- [ ] REMU

**Privilege Tests (if available)**

System:
- [ ] ECALL
- [ ] EBREAK
- [ ] MRET

CSR:
- [ ] CSRRW, CSRRWI
- [ ] CSRRS, CSRRSI
- [ ] CSRRC, CSRRCI

### Running Tests

```bash
cd verification
./run_compliance.sh
```

### Debugging Failed Tests

For each failed test:
- [ ] Read test source code (understand what it tests)
- [ ] Run in simulator with waveforms
- [ ] Check signature output vs expected
- [ ] Identify incorrect instruction or behavior
- [ ] Fix bug in RTL
- [ ] Re-run test
- [ ] Verify fix doesn't break other tests

**Target: 100% Passing**
- [ ] All RV32I tests pass (40/40)
- [ ] All RV32M tests pass (8/8)
- [ ] All privilege tests pass

**Deliverable:** Core passes all RISC-V compliance tests

---

## Final Verification Checklist

### Functionality

- [ ] All 48 instructions execute correctly
- [ ] Register x0 always reads 0
- [ ] PC updates correctly (sequential, branch, jump)
- [ ] Immediate values decoded correctly
- [ ] Memory access works (load/store, byte/half/word)
- [ ] Sign extension correct (LB, LH, SRA)
- [ ] Zero extension correct (LBU, LHU)
- [ ] Multiply/divide operations correct
- [ ] CSR operations correct (RW, RS, RC)
- [ ] Exceptions trigger and trap correctly
- [ ] Interrupts trigger and trap correctly
- [ ] MRET returns correctly
- [ ] State saved/restored correctly

### Timing

- [ ] No combinational loops
- [ ] No setup/hold violations
- [ ] Clock frequency meets target (50-100 MHz)
- [ ] Interrupt latency acceptable (<1 µs)

### Code Quality

- [ ] All modules documented
- [ ] Clear signal naming
- [ ] No magic numbers (use parameters)
- [ ] Simulation warnings addressed
- [ ] Synthesis warnings addressed

### Documentation

- [ ] Architecture diagram updated
- [ ] Module descriptions written
- [ ] Interface specifications documented
- [ ] Test results documented
- [ ] Known issues/limitations documented

---

## Common Issues and Quick Fixes

**Issue: Interrupts not firing**
```
Fix checklist:
□ mstatus.MIE = 1?
□ mie[interrupt_bit] = 1?
□ Interrupt line actually asserted?
□ Priority encoder working?
```

**Issue: Exceptions not trapping**
```
Fix checklist:
□ exception_taken signal asserted?
□ State machine enters TRAP state?
□ trap_entry signal asserted?
□ PC jumps to trap_vector?
```

**Issue: MRET doesn't return**
```
Fix checklist:
□ mepc contains correct address?
□ mepc[1:0] cleared (aligned)?
□ trap_return signal asserted?
□ PC loaded from mepc?
```

**Issue: CSR writes don't work**
```
Fix checklist:
□ csr_op correct? (001=RW, 010=RS, 011=RC)
□ CSR address correct?
□ csr_wdata correct?
□ CSR write timing correct?
```

**Issue: Compliance test fails**
```
Debug steps:
1. Read test source (understand what it tests)
2. Run in simulator with waveforms
3. Compare signature with expected
4. Find first differing value
5. Trace back to instruction that produced it
6. Fix instruction implementation
7. Re-run test
```

---

## Time Estimates

| Phase | Minimum | Typical | Maximum |
|-------|---------|---------|---------|
| Phase 1: CSR Unit | 6 hours | 8 hours | 10 hours |
| Phase 2: Exceptions | 4 hours | 6 hours | 8 hours |
| Phase 3: Interrupts | 6 hours | 8 hours | 10 hours |
| Phase 4: System Instructions | 3 hours | 4 hours | 6 hours |
| Phase 5: Integration | 8 hours | 10 hours | 15 hours |
| Phase 6: Compliance | 5 hours | 8 hours | 15 hours |
| **Total** | **32 hours** | **44 hours** | **64 hours** |

**Timeline:**
- **Aggressive:** 4 weeks @ 10 hours/week
- **Comfortable:** 6 weeks @ 8 hours/week
- **Relaxed:** 10 weeks @ 5 hours/week

---

## Success Criteria

### Minimum (Core Working)
- ✅ CSR read/write operations work
- ✅ Exceptions trap to handler
- ✅ MRET returns from trap
- ✅ At least one interrupt works
- ✅ Basic integration test passes

### Target (Compliance Ready)
- ✅ All CSRs implemented
- ✅ All exceptions handled
- ✅ All interrupts work with priority
- ✅ All system instructions work
- ✅ 80%+ compliance tests pass

### Excellent (Production Ready)
- ✅ 100% compliance tests pass
- ✅ Interrupt latency < 1 µs
- ✅ Performance counters working
- ✅ No synthesis warnings
- ✅ Comprehensive test coverage
- ✅ Well documented

---

## Next Steps After Completion

1. **SOC Integration**
   - Connect to timer peripheral
   - Connect to ADC interface
   - Connect to PWM accelerator
   - Connect to protection unit

2. **Software Development**
   - Port control algorithms from MATLAB
   - Write interrupt service routines
   - Write startup code (crt0.S)
   - Write linker script

3. **FPGA Deployment**
   - Synthesize for FPGA
   - Implement on board
   - Test with real peripherals
   - Tune performance

4. **Custom Instructions (Optional)**
   - Design Zpec extension
   - Add custom instructions for DSP
   - Optimize control algorithms
   - Re-test compliance

---

**Document Version:** 1.0
**Last Updated:** 2025-12-08

**Ready to start? Begin with Phase 1: CSR Unit!** 🚀
