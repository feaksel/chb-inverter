# Zpec Implementation Quick Checklist

**Quick Reference for Implementing Custom Power Electronics Instructions**

---

## Overview

**Goal:** Add 6 custom instructions to accelerate inverter control
**Time Estimate:** 25-35 hours
**Prerequisite:** Working RV32IM core

---

## Phase 1: Setup and Definitions (2-3 hours)

### Add to riscv_defines.vh

- [ ] Define `OPCODE_ZPEC` (0x5B - custom-2)
- [ ] Define all 6 funct3 codes:
  - [ ] `FUNCT3_ZPEC_MAC` (0x0)
  - [ ] `FUNCT3_ZPEC_SAT` (0x1)
  - [ ] `FUNCT3_ZPEC_ABS` (0x2)
  - [ ] `FUNCT3_ZPEC_PWM` (0x3)
  - [ ] `FUNCT3_ZPEC_SINCOS` (0x4)
  - [ ] `FUNCT3_ZPEC_SQRT` (0x5)
- [ ] Define `FUNCT7_ZPEC` (0x00)

### Documentation

- [ ] Document instruction encoding
- [ ] Create instruction reference card
- [ ] Write usage examples

**Deliverable:** Opcode definitions ready

---

## Phase 2: Zpec Execution Unit (12-15 hours)

### Create zpec_unit.v

#### Basic Structure (2 hours)

- [ ] Create module skeleton
- [ ] Define input/output ports
- [ ] Create state machine (IDLE, EXEC, DONE)
- [ ] Add cycle counter

#### Implement Instructions (10-13 hours)

**Simple Instructions (1-2 cycles each):**

- [ ] **ZPEC.ABS** (Absolute Value) - 2 hours
  - [ ] Implement absolute value logic
  - [ ] Test with positive/negative values
  - [ ] Test edge cases (0, INT_MIN)

- [ ] **ZPEC.SAT** (Saturate) - 2 hours
  - [ ] Implement min/max clamping
  - [ ] Test within range
  - [ ] Test below min, above max
  - [ ] Test equal to boundaries

**Medium Instructions (2-4 cycles each):**

- [ ] **ZPEC.PWM** (PWM Calculation) - 3 hours
  - [ ] Implement normalization (shift from ±32K to 0-65K)
  - [ ] Implement scaling to PWM period
  - [ ] Test with various control outputs
  - [ ] Test with different PWM periods
  - [ ] Verify output range [0, period]

- [ ] **ZPEC.MAC** (Multiply-Accumulate) - 4 hours
  - [ ] Implement 64-bit multiply
  - [ ] Implement accumulate with rs1
  - [ ] Implement Q15 scaling (>> 15)
  - [ ] Implement saturation logic
  - [ ] Test overflow/underflow
  - [ ] Test with typical control gains

**Complex Instructions (4-8 cycles each):**

- [ ] **ZPEC.SINCOS** (Sine/Cosine) - 4 hours
  - [ ] Implement Bhaskara I approximation
  - [ ] Calculate sine
  - [ ] Calculate cosine (cos = sin(π/2 - x))
  - [ ] Test at key angles (0°, 30°, 45°, 60°, 90°)
  - [ ] Measure error (should be < 0.1%)
  - [ ] Optimize for speed

- [ ] **ZPEC.SQRT** (Square Root) - 4 hours
  - [ ] Implement Newton-Raphson iteration
  - [ ] Calculate initial guess
  - [ ] Implement 4 iterations
  - [ ] Test with perfect squares (100, 10000, etc.)
  - [ ] Test with non-perfect squares
  - [ ] Verify accuracy (< 1 LSB error)

### Helper Functions

- [ ] Implement `saturate()` function
- [ ] Implement `abs_value()` function
- [ ] Implement `pwm_calc()` function
- [ ] Implement `sine_approx()` function
- [ ] Implement Newton-Raphson sqrt logic

**Deliverable:** Working zpec_unit.v module

---

## Phase 3: Decoder Integration (3-4 hours)

### Modify decoder.v

- [ ] Add control signal outputs:
  - [ ] `is_zpec` - Zpec instruction flag
  - [ ] `zpec_funct3` - Operation select
- [ ] Add `OPCODE_ZPEC` case in decoder
- [ ] Decode register addresses for each instruction:
  - [ ] MAC: rd, rs1, rs2, rs3 (R4-type)
  - [ ] SAT: rd, rs1, rs2, rs3
  - [ ] ABS: rd, rs1
  - [ ] PWM: rd, rs1, rs2
  - [ ] SINCOS: rd, rs1, rs2 (dual write)
  - [ ] SQRT: rd, rs1
- [ ] Set `reg_write` appropriately
- [ ] Handle illegal instruction detection

### Test Decoder

- [ ] Verify each Zpec instruction decodes correctly
- [ ] Check register addresses extracted properly
- [ ] Verify control signals set correctly

**Deliverable:** Decoder recognizes all Zpec instructions

---

## Phase 4: Core Integration (4-5 hours)

### Connect Zpec Unit

- [ ] Instantiate `zpec_unit` in core
- [ ] Connect clock and reset
- [ ] Connect control signals:
  - [ ] `zpec_start` from state machine
  - [ ] `zpec_done` to state machine
  - [ ] `zpec_funct3` from decoder
- [ ] Connect data signals:
  - [ ] `rs1_data`, `rs2_data`, `rs3_data` from register file
  - [ ] `rd_data` to writeback mux
  - [ ] `rs2_result` for SINCOS dual write

### Modify State Machine

- [ ] Add `STATE_ZPEC_WAIT` state
- [ ] In `STATE_EXECUTE`:
  - [ ] Check `is_zpec`
  - [ ] Assert `zpec_start`
  - [ ] Transition to `STATE_ZPEC_WAIT`
- [ ] In `STATE_ZPEC_WAIT`:
  - [ ] Wait for `zpec_done`
  - [ ] Latch `rd_data`
  - [ ] Handle SINCOS dual write (special case)
  - [ ] Transition to `STATE_WB`

### Handle Special Cases

- [ ] **SINCOS dual write:**
  - [ ] Write `rd_data` to `rd`
  - [ ] Write `rs2_result` to `rs2` address
  - [ ] May require extra writeback cycle

**Deliverable:** Zpec instructions execute in core

---

## Phase 5: Unit Testing (4-6 hours)

### Create tb_zpec_unit.v

- [ ] Set up testbench infrastructure
- [ ] Add clock generation
- [ ] Add reset sequence

### Test Each Instruction

**ZPEC.ABS:**
- [ ] Test abs(positive) = positive
- [ ] Test abs(negative) = positive
- [ ] Test abs(0) = 0
- [ ] Test abs(INT_MIN) edge case

**ZPEC.SAT:**
- [ ] Test value within range
- [ ] Test value below minimum → clamped to min
- [ ] Test value above maximum → clamped to max
- [ ] Test value equal to min/max boundaries

**ZPEC.PWM:**
- [ ] Test control_out = 0 → duty ≈ 50%
- [ ] Test control_out = +32767 → duty ≈ 100%
- [ ] Test control_out = -32768 → duty ≈ 0%
- [ ] Test various PWM periods (100, 1000, 10000)

**ZPEC.MAC:**
- [ ] Test simple MAC: acc + (a × b)
- [ ] Test with positive values
- [ ] Test with negative values
- [ ] Test saturation on overflow
- [ ] Test saturation on underflow
- [ ] Test with Q15 fixed-point values

**ZPEC.SINCOS:**
- [ ] Test sin(0) ≈ 0
- [ ] Test sin(π/2) ≈ 1
- [ ] Test sin(π) ≈ 0
- [ ] Test cos(0) ≈ 1
- [ ] Test cos(π/2) ≈ 0
- [ ] Test cos(π) ≈ -1
- [ ] Measure maximum error (should be < 0.1%)

**ZPEC.SQRT:**
- [ ] Test sqrt(0) = 0
- [ ] Test sqrt(1) = 1
- [ ] Test sqrt(100) = 10
- [ ] Test sqrt(10000) = 100
- [ ] Test sqrt(65536) = 256
- [ ] Test non-perfect squares
- [ ] Verify accuracy within ±1

### Waveform Verification

- [ ] Generate VCD files for each test
- [ ] View waveforms in GTKWave
- [ ] Verify cycle counts:
  - [ ] ABS: 1 cycle
  - [ ] SAT: 1 cycle
  - [ ] PWM: 2 cycles
  - [ ] MAC: 3 cycles
  - [ ] SINCOS: 4 cycles
  - [ ] SQRT: 8 cycles

**Deliverable:** All instructions pass unit tests

---

## Phase 6: Integration Testing (3-4 hours)

### Create Assembly Test Programs

**Test 1: Simple Zpec Operations**
```assembly
# test_zpec_basic.s
li      x1, -12345
zpec.abs x2, x1          # x2 = 12345

li      x3, 50000
li      x4, -1000
li      x5, 1000
zpec.sat x6, x3, x4, x5  # x6 = 1000 (clamped)
```

- [ ] Write test program
- [ ] Compile to hex
- [ ] Run in core simulation
- [ ] Verify results in registers

**Test 2: PR Controller Fragment**
```assembly
# test_pr_controller.s
# Implement key PR controller operations
```

- [ ] Generate sine reference (SINCOS)
- [ ] Calculate error
- [ ] Apply proportional gain (MAC)
- [ ] Saturate output (SAT)
- [ ] Convert to PWM (PWM)
- [ ] Verify control flow

**Test 3: Protection Logic**
```assembly
# test_overcurrent.s
# Simulate overcurrent detection
```

- [ ] Read simulated current
- [ ] Get absolute value (ABS)
- [ ] Compare to threshold
- [ ] Verify fault behavior

**Test 4: RMS Calculation**
```assembly
# test_rms.s
# Calculate RMS of sample buffer
```

- [ ] Sum squares of samples
- [ ] Divide by count
- [ ] Calculate square root (SQRT)
- [ ] Verify result

### Full System Test

- [ ] Run all test programs in sequence
- [ ] Verify no hangs or crashes
- [ ] Check register values match expected
- [ ] Verify memory unchanged (if not expected to change)

**Deliverable:** Zpec works in integrated system

---

## Phase 7: Performance Validation (2-3 hours)

### Benchmark Control Loop

Without Zpec:
- [ ] Write control loop in pure RV32IM
- [ ] Count cycles
- [ ] Measure execution time
- [ ] Calculate CPU utilization @ 10 kHz

With Zpec:
- [ ] Write control loop using Zpec
- [ ] Count cycles
- [ ] Measure execution time
- [ ] Calculate CPU utilization @ 10 kHz

Compare:
- [ ] Calculate speedup factor (target: 8-10x)
- [ ] Compare CPU utilization (target: <1%)
- [ ] Verify timing improvements

### Measure Instruction Latencies

- [ ] ZPEC.ABS: Verify 1 cycle
- [ ] ZPEC.SAT: Verify 1 cycle
- [ ] ZPEC.PWM: Verify 2 cycles
- [ ] ZPEC.MAC: Verify 3 cycles
- [ ] ZPEC.SINCOS: Verify 4 cycles
- [ ] ZPEC.SQRT: Verify 8 cycles

### Verify Accuracy

- [ ] SINCOS error: < 0.1% across full range
- [ ] SQRT error: < 1 LSB
- [ ] MAC saturation: Correct at limits
- [ ] PWM: Output in valid range [0, period]

**Deliverable:** Performance meets specifications

---

## Phase 8: Documentation (2-3 hours)

### User Documentation

- [ ] Write instruction reference manual
- [ ] Document each instruction:
  - [ ] Syntax
  - [ ] Operation
  - [ ] Encoding
  - [ ] Cycle count
  - [ ] Use cases
  - [ ] Examples
- [ ] Create programming guide
- [ ] Write example code snippets

### Technical Documentation

- [ ] Document zpec_unit.v architecture
- [ ] Explain algorithm choices (Bhaskara, Newton-Raphson)
- [ ] Document integration points
- [ ] Update core documentation

### Code Comments

- [ ] Add detailed comments to zpec_unit.v
- [ ] Document state machine behavior
- [ ] Explain complex calculations
- [ ] Add usage examples in comments

**Deliverable:** Complete Zpec documentation

---

## Optional Enhancements

### Compiler Intrinsics (5-8 hours)

- [ ] Define GCC intrinsics
- [ ] Create header file with inline assembly
- [ ] Test intrinsics in C code
- [ ] Benchmark C vs assembly

Example:
```c
// zpec_intrinsics.h
static inline int32_t __zpec_abs(int32_t x) {
    int32_t result;
    asm volatile ("zpec.abs %0, %1" : "=r"(result) : "r"(x));
    return result;
}
```

### C Library Wrappers (3-5 hours)

- [ ] Write C library for Zpec operations
- [ ] Create convenient API
- [ ] Add error checking
- [ ] Write examples

Example:
```c
// zpec_lib.c
typedef struct {
    int32_t Kp, Ki, integrator;
} pi_controller_t;

int32_t pi_update(pi_controller_t *pi, int32_t error) {
    // Uses ZPEC.MAC internally
    return zpec_mac(pi->integrator, error, pi->Kp);
}
```

### Advanced Optimizations (4-6 hours)

- [ ] Pipeline Zpec operations (if possible)
- [ ] Add result forwarding
- [ ] Optimize critical paths
- [ ] Reduce latency where possible

---

## Time Estimates

| Phase | Minimum | Typical | Maximum |
|-------|---------|---------|---------|
| Phase 1: Setup | 1.5 hours | 2 hours | 3 hours |
| Phase 2: Zpec Unit | 10 hours | 13 hours | 15 hours |
| Phase 3: Decoder | 2.5 hours | 3 hours | 4 hours |
| Phase 4: Integration | 3 hours | 4 hours | 5 hours |
| Phase 5: Unit Testing | 3 hours | 5 hours | 6 hours |
| Phase 6: Integration Testing | 2.5 hours | 3 hours | 4 hours |
| Phase 7: Performance | 1.5 hours | 2 hours | 3 hours |
| Phase 8: Documentation | 1.5 hours | 2 hours | 3 hours |
| **Total** | **25 hours** | **34 hours** | **43 hours** |

**Timeline:**
- **Aggressive:** 3 weeks @ 10 hours/week
- **Comfortable:** 5 weeks @ 7 hours/week
- **Relaxed:** 8 weeks @ 4 hours/week

---

## Success Criteria

### Minimum (Zpec Working)
- ✅ All 6 instructions implemented
- ✅ Unit tests passing
- ✅ Integrated with core
- ✅ Basic assembly tests work
- ✅ No crashes or hangs

### Target (Production Ready)
- ✅ All tests passing (unit + integration)
- ✅ Performance: 8-10x speedup in control loop
- ✅ Accuracy: SINCOS < 0.1% error, SQRT < 1 LSB
- ✅ Cycle counts match specification
- ✅ Documentation complete
- ✅ Example code provided

### Excellent (Optimized)
- ✅ 10x+ speedup achieved
- ✅ Compiler intrinsics available
- ✅ C library wrappers provided
- ✅ Full control algorithm tested on hardware
- ✅ THD measured < 5% with Zpec
- ✅ No synthesis warnings
- ✅ Timing closure at target frequency

---

## Common Issues and Quick Fixes

**Issue: SINCOS accuracy poor**
```
Fix checklist:
□ Check angle normalization (0 to π range)
□ Verify fixed-point scaling (Q15)
□ Test polynomial coefficients
□ Compare with reference (MATLAB/Python)
□ Consider adding lookup table for key angles
```

**Issue: MAC overflow/saturation incorrect**
```
Fix checklist:
□ Check 64-bit intermediate calculation
□ Verify Q15 scaling (>> 15 correct?)
□ Test saturation limits (0x7FFFFFFF, 0x80000000)
□ Verify signed/unsigned handling
□ Check accumulator size
```

**Issue: SQRT converges slowly**
```
Fix checklist:
□ Check initial guess calculation
□ Verify Newton-Raphson formula: (x + n/x) / 2
□ Test with perfect squares first
□ Increase iteration count if needed
□ Consider different initial guess algorithm
```

**Issue: PWM output out of range**
```
Fix checklist:
□ Verify normalization: control ± 32K → 0-65K
□ Check scaling factor (should be / 65536)
□ Test with edge values: -32768, 0, +32767
□ Verify period parameter correct
□ Check for integer overflow in multiplication
```

**Issue: Dual write for SINCOS not working**
```
Fix checklist:
□ Verify decoder provides rs2 address
□ Check state machine has dual-write logic
□ May need extra writeback cycle
□ Test with different register combinations
□ Verify register file supports dual write
```

---

## Testing Checklist

### Unit Tests
- [ ] All 6 instructions tested individually
- [ ] Edge cases covered
- [ ] Waveforms verified
- [ ] Cycle counts confirmed

### Integration Tests
- [ ] Assembly programs run successfully
- [ ] Zpec instructions work with standard RV32IM
- [ ] No conflicts with other instructions
- [ ] Register forwarding works (if applicable)

### Performance Tests
- [ ] Speedup measured and documented
- [ ] CPU utilization calculated
- [ ] Cycle counts match specification
- [ ] Latency acceptable for control loop

### Accuracy Tests
- [ ] SINCOS error < 0.1%
- [ ] SQRT error < 1 LSB
- [ ] MAC saturation correct
- [ ] PWM output in valid range

### System Tests
- [ ] Control algorithm runs correctly
- [ ] No crashes under load
- [ ] Interrupts still work
- [ ] Memory access unaffected

---

## Next Steps After Completion

1. **Hardware Validation**
   - Synthesize for FPGA
   - Test on real hardware
   - Measure actual performance
   - Verify with oscilloscope

2. **Control Algorithm Development**
   - Port MATLAB PR controller using Zpec
   - Write optimized ISRs
   - Test closed-loop control
   - Measure THD and performance

3. **Software Ecosystem**
   - Create C library
   - Write example applications
   - Document best practices
   - Create tutorials

4. **Optimization**
   - Profile hot spots
   - Optimize critical paths
   - Reduce latency further
   - Improve accuracy if needed

---

**Document Version:** 1.0
**Last Updated:** 2025-12-08

**Ready to start? Begin with Phase 1: Setup!** ⚡
