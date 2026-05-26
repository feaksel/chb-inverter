# MDU vs Zpec: Performance Comparison and Design Trade-offs

**Understanding When to Use Each and Why Zpec is Faster**

---

## The Core Question: Why is Zpec Faster?

### Short Answer

**MDU is sequential** (optimized for area, slow but small)
**Zpec is parallel** (optimized for speed, fast but larger)

It's a **hardware trade-off**: area vs speed.

---

## Detailed Comparison

### 1. MDU (RV32M Extension) - Sequential Implementation

**Your current `mdu.v` uses shift-and-add algorithm:**

```verilog
// Multiply: Shift-and-add (32 iterations)
for (i = 0; i < 32; i++) {
    if (multiplier[0]) {
        product += multiplicand;
    }
    multiplicand <<= 1;
    multiplier >>= 1;
}
```

**Hardware:**
```
┌──────────────────────────────────────────────┐
│         Sequential Multiplier                 │
│                                               │
│  32-bit Register ─┐                          │
│  32-bit Register ─┼──► 32-bit Adder         │
│  64-bit Accumulator                           │
│                                               │
│  Cost: ~500 LUTs                             │
│  Time: 33 cycles                              │
└──────────────────────────────────────────────┘
```

**Why 33 cycles?**
- 1 cycle to start
- 32 cycles to iterate (one per bit)
- Result: slow but small

---

### 2. Zpec MAC - Parallel Implementation

**Zpec uses dedicated multiplier hardware:**

```verilog
// Combinational or pipelined multiplier
// (Not shift-and-add!)

// Option 1: Pipelined (recommended)
Stage 1: Partial products
Stage 2: Wallace tree reduction
Stage 3: Final addition
Result: 3 cycles

// Option 2: Combinational (if desperate for speed)
All stages in one cycle
Result: 1 cycle (but HUGE area)
```

**Hardware:**
```
┌──────────────────────────────────────────────┐
│         Pipelined Multiplier                  │
│                                               │
│  ┌────────────┐  ┌────────────┐             │
│  │  Partial   │─►│  Wallace   │─►           │
│  │  Products  │  │    Tree    │  Final Sum  │
│  └────────────┘  └────────────┘             │
│                                               │
│  Cost: ~2000-3000 LUTs (4-6x larger!)       │
│  Time: 3 cycles (11x faster!)                │
└──────────────────────────────────────────────┘
```

**Why 3 cycles?**
- Cycle 1: Generate partial products in parallel
- Cycle 2: Reduce with Wallace tree
- Cycle 3: Final addition + accumulate + saturate
- Result: fast but larger

---

## Why Can Zpec Be Faster?

### The Trade-off: Silicon Area vs Speed

```
                    Area (LUTs)      Speed (cycles)
                    ────────────────────────────────
Sequential MDU:         ~500              33
Pipelined Zpec:      ~2500-3000            3
Combinational Zpec:  ~8000-10000           1

FPGA/ASIC has limited area, so you choose:
  - Many slow units? OR
  - Few fast units?
```

### For Your Application (Inverter Control)

**Your needs:**
- Fast control loop (10 kHz = 100 µs period)
- Limited number of multiplications per loop (~3-5)
- Real-time critical

**Best approach: Hybrid**
- One fast Zpec MAC for control loop (critical path)
- One slow MDU for general math (non-critical)

---

## Performance Comparison

### Scenario 1: PR Controller (Your Use Case)

**Using MDU only:**
```assembly
# Proportional term
lw      t0, Kp
mul     t1, a0, t0        # 33 cycles
srai    t1, t1, 15        # 1 cycle

# Resonant term
lw      t2, Kr
mul     t3, a1, t2        # 33 cycles
srai    t3, t3, 15        # 1 cycle

# Combine
add     a0, t1, t3        # 1 cycle

# Total: 69 cycles
# At 50 MHz: 1.38 µs
```

**Using Zpec MAC:**
```assembly
# Proportional + Resonant in one instruction
lw      t0, Kp
lw      t1, resonant_state
zpec.mac a0, t1, a0, t0   # 3 cycles (does multiply-accumulate!)

# Total: 3 cycles
# At 50 MHz: 0.06 µs
# 23x faster!
```

**Key insight:** Zpec MAC does **multiply + add + saturate** in 3 cycles,
while MDU does just **multiply** in 33 cycles!

---

## Do You Need Both MDU and Zpec?

### Option 1: MDU Only (RV32IM Compliant)

**Pros:**
- ✅ RV32IM ISA compliance
- ✅ Smaller area (~500 LUTs)
- ✅ Works with standard RISC-V toolchain
- ✅ Can compile any C code with multiply

**Cons:**
- ❌ Slow (33 cycles per multiply)
- ❌ Control loop takes ~200 cycles
- ❌ 4% CPU utilization @ 10 kHz

**Best for:**
- General purpose computing
- Non-real-time applications
- When area is critical
- When you need full RV32IM compliance

---

### Option 2: Zpec Only (Custom, Specialized)

**Pros:**
- ✅ Very fast (3 cycles for MAC)
- ✅ Control loop takes ~20 cycles
- ✅ 0.4% CPU utilization @ 10 kHz
- ✅ Optimized for control algorithms

**Cons:**
- ❌ Not RV32IM compliant (no M extension)
- ❌ Can't use standard multiply instructions (MUL/DIV)
- ❌ Need custom intrinsics or inline assembly
- ❌ Larger area (~2500 LUTs)

**Best for:**
- Dedicated control applications
- Real-time critical systems
- When performance is critical
- When you control all software

---

### Option 3: Both MDU and Zpec (Hybrid - RECOMMENDED)

**Pros:**
- ✅ RV32IM compliant (can run any RISC-V code)
- ✅ Fast control loops (use Zpec)
- ✅ General multiply available (use MDU)
- ✅ Flexible: choose fast or compliant per use

**Cons:**
- ❌ Larger area (~3000 LUTs total)
- ❌ More complex design
- ❌ Need to decide when to use each

**Best for:**
- Your 5-level inverter project! ← **RECOMMENDED**
- Mixed applications (control + general compute)
- When you need both speed and compatibility

**Implementation:**
```verilog
// In decoder
if (is_m_extension) begin
    use_mdu = 1;  // Standard RV32IM multiply
end else if (is_zpec) begin
    use_zpec = 1;  // Fast custom MAC
end

// In execute stage
if (use_mdu) begin
    mdu_start = 1;
    wait_for(mdu_done);  // 33 cycles
end else if (use_zpec) begin
    zpec_start = 1;
    wait_for(zpec_done); // 3 cycles
end
```

---

## Resource Usage Comparison

### FPGA Resource Estimates (Artix-7)

| Component | LUTs | FFs | DSPs | BRAM |
|-----------|------|-----|------|------|
| **Core (RV32I only)** | 2000 | 1500 | 0 | 2 |
| **+ MDU (sequential)** | +500 | +100 | 0 | 0 |
| **+ Zpec (pipelined)** | +2500 | +200 | 2-3 | 0 |
| **+ Both** | +3000 | +300 | 2-3 | 0 |
| **Total with Both** | ~5000 | ~2000 | 2-3 | 2 |

**Target FPGA: Artix-7 (XC7A35T)**
- Available LUTs: 20,800
- Available FFs: 41,600
- Available DSPs: 90
- Available BRAM: 50

**Utilization with both:**
- LUTs: 24% (plenty of room!)
- FFs: 5% (no problem)
- DSPs: 3% (barely using any)
- BRAM: 4% (minimal)

**Conclusion: You can afford both!** 🎉

---

## Recommended Design for Your Inverter

### Architecture

```
┌────────────────────────────────────────────────────────────┐
│                    RV32IM + Zpec Core                       │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │                  Execution Units                      │  │
│  │                                                       │  │
│  │  ┌──────┐  ┌──────┐  ┌──────────┐  ┌──────────┐    │  │
│  │  │ ALU  │  │ MDU  │  │  Branch  │  │  Zpec    │    │  │
│  │  │(RV32I)│  │(M ext)│  │   Unit   │  │   MAC    │    │  │
│  │  └──────┘  └──────┘  └──────────┘  └──────────┘    │  │
│  │      │         │            │              │         │  │
│  │      └─────────┴────────────┴──────────────┘         │  │
│  │                      │                                │  │
│  └──────────────────────┼────────────────────────────────┘  │
│                         ▼                                   │
│                   Result Mux                                │
└─────────────────────────────────────────────────────────────┘
```

### Software Usage Pattern

```c
// Interrupt Service Routine (10 kHz)
void control_loop_isr(void) {
    // CRITICAL PATH: Use Zpec (inline assembly)
    int32_t error = ref - measured;

    // Zpec MAC: fast path
    asm volatile (
        "zpec.mac %0, %1, %2, %3"
        : "=r"(output)
        : "r"(integrator), "r"(error), "r"(Kp)
    );

    // Zpec PWM: fast PWM calculation
    asm volatile (
        "zpec.pwm %0, %1, %2"
        : "=r"(duty)
        : "r"(output), "r"(period)
    );

    update_pwm(duty);
}

// Background Task: Use MDU (standard C)
void calculate_rms(void) {
    // NON-CRITICAL: Use standard multiply
    // Compiler generates MUL instruction
    uint32_t sum = 0;
    for (int i = 0; i < N; i++) {
        sum += samples[i] * samples[i];  // Uses MDU (slow but OK)
    }
    rms = sqrt(sum / N);
}

// Use the right tool for the job!
// - Critical loops: Zpec
// - Background math: MDU
```

---

## Decision Matrix

### When to Use MDU

✅ **Use MDU when:**
- General purpose multiplication in background tasks
- Non-time-critical calculations
- You want RV32IM compliance
- Compiling C code with multiply operations
- Division operations (Zpec doesn't have DIV)
- Need both quotient and remainder

**Examples:**
```c
// These use MDU (from C compiler)
uint32_t checksum = crc32(data) * 0x12345678;
int32_t quotient = numerator / denominator;
float scaled = value * 3.14159f;  // (if using soft-float)
```

### When to Use Zpec

✅ **Use Zpec when:**
- Time-critical control loops (ISRs)
- Need multiply + accumulate (common in control)
- Need saturation (anti-windup)
- PWM calculations
- Reference generation (sine/cosine)
- RMS calculations (with SQRT)

**Examples:**
```assembly
# These use Zpec (inline assembly in ISR)
zpec.mac    # PI/PR controller
zpec.sat    # Output limiting
zpec.pwm    # Duty cycle calculation
zpec.sincos # Reference generation
```

---

## Performance Summary

### 10 kHz Control Loop Breakdown

| Task | Without Zpec | With Zpec | Improvement |
|------|--------------|-----------|-------------|
| Read ADC | 2 cycles | 2 cycles | - |
| **Generate ref** | **50 cycles** (table) | **4 cycles** (SINCOS) | **12.5x** |
| Calculate error | 2 cycles | 2 cycles | - |
| **PR controller** | **~70 cycles** (MUL×2) | **3 cycles** (MAC) | **23x** |
| **Saturate** | **6 cycles** | **1 cycle** (SAT) | **6x** |
| **PWM calc** | **~40 cycles** (MUL) | **2 cycles** (PWM) | **20x** |
| Update hardware | 3 cycles | 3 cycles | - |
| **TOTAL** | **~173 cycles** | **~17 cycles** | **~10x** |

**Impact:**
- **Without Zpec:** 173 cycles × 2 (for 2 H-bridges) = 346 cycles = 6.92 µs @ 50 MHz
- **With Zpec:** 17 cycles × 2 = 34 cycles = 0.68 µs @ 50 MHz

**CPU Utilization @ 10 kHz:**
- Without: 6.92%
- With: 0.68%

**Available cycles for other tasks:**
- Without: 4653 cycles (93%)
- With: 4966 cycles (99.3%)

---

## Recommended Implementation Strategy

### Phase 1: Start with MDU (RV32IM)

**Week 1-2:**
1. Implement MDU (you have this!)
2. Get RV32IM working
3. Pass compliance tests
4. Implement control algorithm using standard MUL

**Result:** Working but slow control loop (~6.9 µs ISR)

### Phase 2: Add Zpec (Optional Performance Boost)

**Week 3-4:**
1. Keep MDU (for compatibility)
2. Add Zpec unit (parallel implementation)
3. Modify critical ISR to use Zpec
4. Keep background tasks using MDU

**Result:** Fast control loop (~0.7 µs ISR) + RV32IM compliance

### Phase 3: Optimize

**Week 5:**
1. Profile code
2. Identify bottlenecks
3. Use Zpec for critical paths
4. Use MDU for everything else

**Result:** Optimal balance of speed and area

---

## Cost-Benefit Analysis

### Option A: MDU Only

**Cost:**
- Area: 500 LUTs
- Time: 2 weeks implementation

**Benefit:**
- RV32IM compliance ✓
- Works with any RISC-V code ✓

**Performance:**
- Control loop: ~173 cycles (6.9 µs)
- CPU usage: ~7% @ 10 kHz

**Verdict:** Good enough for your inverter? **Maybe, but tight.**

---

### Option B: Zpec Only

**Cost:**
- Area: 2500 LUTs
- Time: 4 weeks implementation

**Benefit:**
- Very fast control ✓
- Low CPU usage ✓

**Performance:**
- Control loop: ~17 cycles (0.7 µs)
- CPU usage: ~0.7% @ 10 kHz

**Verdict:** Fast, but no RV32IM compliance. **Risky.**

---

### Option C: Both (Recommended)

**Cost:**
- Area: 3000 LUTs (still only 15% of Artix-7!)
- Time: 5-6 weeks implementation

**Benefit:**
- RV32IM compliance ✓
- Fast control when needed ✓
- Flexible ✓
- Best of both worlds ✓

**Performance:**
- Control loop: ~17 cycles with Zpec
- Background: Works with standard C and multiply

**Verdict:** **BEST CHOICE for your project!** ✅

---

## Final Recommendation

### For Your 5-Level Inverter Project:

**Implement Both MDU and Zpec**

**Why:**
1. **Area is not a problem** - You have plenty of FPGA resources
2. **Flexibility** - Use fast path when needed, standard path otherwise
3. **Future-proof** - Can run any RISC-V code
4. **Performance** - Get 10x speedup where it matters
5. **Safety** - Fast enough for protection and control

**Implementation Priority:**
1. **First:** Get MDU working (RV32IM compliance)
   - Use this for initial testing
   - Implement control algorithms
   - Verify functionality

2. **Then:** Add Zpec (performance boost)
   - Optimize critical ISRs
   - Measure improvement
   - Compare THD before/after

**Effort Estimate:**
- MDU: Already done! ✅
- CSR/Interrupts: 4-5 weeks (essential)
- Zpec: 4-5 weeks (optional but recommended)
- Total: ~8-10 weeks for complete system

---

## Summary Table

| Feature | MDU Only | Zpec Only | Both (Recommended) |
|---------|----------|-----------|-------------------|
| **RV32IM Compliance** | ✅ Yes | ❌ No | ✅ Yes |
| **Control Loop Speed** | ❌ Slow (173 cyc) | ✅ Fast (17 cyc) | ✅ Fast (17 cyc) |
| **FPGA Area** | ✅ Small (500 LUT) | ⚠️ Medium (2500 LUT) | ⚠️ Medium (3000 LUT) |
| **Flexibility** | ⚠️ Limited | ⚠️ Limited | ✅ High |
| **Development Time** | ✅ Short (2 weeks) | ⚠️ Long (4 weeks) | ⚠️ Longer (5-6 weeks) |
| **CPU Utilization** | ❌ High (7%) | ✅ Low (0.7%) | ✅ Low (0.7%) |
| **Standard C Code** | ✅ Works | ❌ Needs asm | ✅ Works |
| **Performance Critical** | ❌ Marginal | ✅ Excellent | ✅ Excellent |
| **For Your Project** | ⚠️ Acceptable | ⚠️ Risky | ✅ **BEST** |

---

## Conclusion

**Answer to your questions:**

1. **"How is Zpec faster?"**
   - Zpec uses parallel/pipelined multiplier (3 cycles)
   - MDU uses sequential shift-and-add (33 cycles)
   - Trade-off: Zpec is 5-6x larger but 11x faster

2. **"Do I need MDU if I use Zpec?"**
   - **Technically no** - Zpec can handle control loops
   - **Practically yes** - MDU gives RV32IM compliance
   - **Recommended: Use both** - Get speed AND compatibility

**For your inverter:**
- Start with MDU (RV32IM compliance)
- Add Zpec later for performance
- Use Zpec in ISRs, MDU in background
- Total area: 3000 LUTs (only 15% of FPGA)

**You can afford both, and it's worth it!** 🚀

---

**Document Version:** 1.0
**Last Updated:** 2025-12-08

**Next Steps:**
1. Keep your MDU implementation ✓
2. Finish CSR/interrupts first (essential)
3. Add Zpec for performance boost (optional)
4. Profile and optimize
