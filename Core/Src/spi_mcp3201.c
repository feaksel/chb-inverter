#include "spi_mcp3201.h"

static inline uint32_t pin_mask(uint32_t pin)
{
    return (1u << pin);
}

static inline void gpio_set(GPIO_TypeDef *port, uint32_t pin)
{
    port->BSRR = pin_mask(pin);
}

static inline void gpio_reset(GPIO_TypeDef *port, uint32_t pin)
{
    port->BSRR = (pin_mask(pin) << 16u);
}

static void delay_half_period(void)
{
    for (volatile uint32_t i = 0; i < MCP3201_HALF_PERIOD_DELAY_CYCLES; i++) {
        __NOP();
    }
}

static void cs_set(uint8_t mask)
{
    if ((mask & SENSOR_MASK_DC1) != 0u) {
        gpio_set(MCP3201_CS_DC1_PORT, MCP3201_CS_DC1_PIN);
    }
    if ((mask & SENSOR_MASK_DC2) != 0u) {
        gpio_set(MCP3201_CS_DC2_PORT, MCP3201_CS_DC2_PIN);
    }
    if ((mask & SENSOR_MASK_CUR) != 0u) {
        gpio_set(MCP3201_CS_CUR_PORT, MCP3201_CS_CUR_PIN);
    }
}

static void cs_reset(uint8_t mask)
{
    if ((mask & SENSOR_MASK_DC1) != 0u) {
        gpio_reset(MCP3201_CS_DC1_PORT, MCP3201_CS_DC1_PIN);
    }
    if ((mask & SENSOR_MASK_DC2) != 0u) {
        gpio_reset(MCP3201_CS_DC2_PORT, MCP3201_CS_DC2_PIN);
    }
    if ((mask & SENSOR_MASK_CUR) != 0u) {
        gpio_reset(MCP3201_CS_CUR_PORT, MCP3201_CS_CUR_PIN);
    }
}

void SPI_MCP3201_Init(void)
{
    RCC->AHBENR |= RCC_AHBENR_GPIOAEN | RCC_AHBENR_GPIOCEN;

    GPIOA->MODER &= ~(GPIO_MODER_MODER5 | GPIO_MODER_MODER6);
    GPIOA->MODER |= GPIO_MODER_MODER5_0;
    GPIOC->MODER &= ~(GPIO_MODER_MODER0 | GPIO_MODER_MODER1 | GPIO_MODER_MODER2 |
                      GPIO_MODER_MODER3 | GPIO_MODER_MODER4);
    GPIOC->MODER |= GPIO_MODER_MODER0_0 | GPIO_MODER_MODER1_0 | GPIO_MODER_MODER2_0;

    GPIOA->OTYPER &= ~(GPIO_OTYPER_OT_5);
    GPIOC->OTYPER &= ~(GPIO_OTYPER_OT_0 | GPIO_OTYPER_OT_1 | GPIO_OTYPER_OT_2);

    GPIOA->PUPDR &= ~(GPIO_PUPDR_PUPDR5 | GPIO_PUPDR_PUPDR6);
    GPIOA->PUPDR |= GPIO_PUPDR_PUPDR6_0;
    GPIOC->PUPDR &= ~(GPIO_PUPDR_PUPDR0 | GPIO_PUPDR_PUPDR1 | GPIO_PUPDR_PUPDR2 |
                      GPIO_PUPDR_PUPDR3 | GPIO_PUPDR_PUPDR4);
    GPIOC->PUPDR |= GPIO_PUPDR_PUPDR3_0 | GPIO_PUPDR_PUPDR4_0;

    GPIOA->OSPEEDR &= ~(GPIO_OSPEEDER_OSPEEDR5);
    GPIOA->OSPEEDR |= GPIO_OSPEEDER_OSPEEDR5_0;
    GPIOC->OSPEEDR &= ~(GPIO_OSPEEDER_OSPEEDR0 | GPIO_OSPEEDER_OSPEEDR1 | GPIO_OSPEEDER_OSPEEDR2);
    GPIOC->OSPEEDR |= GPIO_OSPEEDER_OSPEEDR0_0 | GPIO_OSPEEDER_OSPEEDR1_0 | GPIO_OSPEEDER_OSPEEDR2_0;

    gpio_reset(MCP3201_SCK_PORT, MCP3201_SCK_PIN);
    cs_set(SENSOR_MASK_ALL);
}

/* Read one MCP3201 with exactly ONE chip-select asserted at a time, sampling
 * a single MISO GPIO. This is mandatory for boards that wire-share a MISO
 * line between channels (here: the upper-bridge island carries DC2 and the
 * current ADC on one isolated MISO return). Asserting two chip-selects on a
 * shared wire would put two MCP3201 DOUTs onto the same net. Reading strictly
 * one channel at a time guarantees only one ADC ever drives the wire.
 *
 * MCP3201 SPI mode 0,0 per build guide v3.1 section 7.3:
 *   DOUT returns [NULL][B11][B10]..[B0][X][X][X]
 * After 16 SCK rising-edge samples the NULL lands at raw[15], data B11..B0
 * at raw[14:3], so the extraction is (raw >> 3) & 0x0FFF.
 *
 * Bringup verification: apply a known low voltage (e.g. 5 V) to the DC bus
 * input. Expected raw at 5 V is 5 / (105.1/5.1 * 5.0/4096) ~= 199. If
 * readings come back ~3120 (~8x off), the NULL bit is appearing at raw[13]
 * instead and the correct shift is (raw >> 1). Adjust here. */
static uint16_t read_one_channel(uint8_t cs_bit,
                                 GPIO_TypeDef *miso_port,
                                 uint32_t miso_pin)
{
    uint16_t raw = 0u;
    uint32_t miso_bit = pin_mask(miso_pin);

    gpio_reset(MCP3201_SCK_PORT, MCP3201_SCK_PIN);
    cs_reset(cs_bit);              /* assert this one chip-select only */
    delay_half_period();

    for (uint32_t i = 0; i < 16u; i++) {
        gpio_set(MCP3201_SCK_PORT, MCP3201_SCK_PIN);
        delay_half_period();

        raw <<= 1;
        raw |= ((miso_port->IDR & miso_bit) != 0u) ? 1u : 0u;

        gpio_reset(MCP3201_SCK_PORT, MCP3201_SCK_PIN);
        delay_half_period();
    }

    cs_set(cs_bit);                /* deassert before the next channel */
    delay_half_period();

    return (uint16_t)((raw >> 3) & 0x0FFFu);
}

void SPI_MCP3201_Read(uint8_t mask, mcp3201_samples_t *samples)
{
    if (samples == (mcp3201_samples_t *)0) {
        return;
    }

    samples->dc1 = 0u;
    samples->dc2 = 0u;
    samples->current = 0u;

    /* Sequential, one chip-select at a time. DC1 has its own MISO line;
     * DC2 and the current ADC share the upper-bridge MISO line, so they
     * must never be selected together — handled naturally by reading each
     * channel in its own pass. */
    if ((mask & SENSOR_MASK_DC1) != 0u) {
        samples->dc1 = read_one_channel(SENSOR_MASK_DC1,
                                        MCP3201_MISO_DC1_PORT, MCP3201_MISO_DC1_PIN);
    }
    if ((mask & SENSOR_MASK_DC2) != 0u) {
        samples->dc2 = read_one_channel(SENSOR_MASK_DC2,
                                        MCP3201_MISO_DC2_PORT, MCP3201_MISO_DC2_PIN);
    }
    if ((mask & SENSOR_MASK_CUR) != 0u) {
        samples->current = read_one_channel(SENSOR_MASK_CUR,
                                            MCP3201_MISO_CUR_PORT, MCP3201_MISO_CUR_PIN);
    }
}
