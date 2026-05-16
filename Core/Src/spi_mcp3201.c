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

void SPI_MCP3201_Read(uint8_t mask, mcp3201_samples_t *samples)
{
    uint16_t raw_dc1 = 0u;
    uint16_t raw_dc2 = 0u;
    uint16_t raw_cur = 0u;
    uint32_t dc1_mask = pin_mask(MCP3201_MISO_DC1_PIN);
    uint32_t dc2_mask = pin_mask(MCP3201_MISO_DC2_PIN);
    uint32_t cur_mask = pin_mask(MCP3201_MISO_CUR_PIN);

    if (samples == (mcp3201_samples_t *)0) {
        return;
    }

    samples->dc1 = 0u;
    samples->dc2 = 0u;
    samples->current = 0u;

    if ((mask & SENSOR_MASK_ALL) == 0u) {
        return;
    }

    /* The 6N137-isolated outputs are independent GPIO inputs instead of a
     * shared MISO bus; some optocoupler outputs do not release cleanly enough
     * to be wire-shared. */
    gpio_reset(MCP3201_SCK_PORT, MCP3201_SCK_PIN);
    cs_reset(mask);
    delay_half_period();

    for (uint32_t i = 0; i < 16u; i++) {
        gpio_set(MCP3201_SCK_PORT, MCP3201_SCK_PIN);
        delay_half_period();

        raw_dc1 <<= 1;
        raw_dc2 <<= 1;
        raw_cur <<= 1;

        if ((mask & SENSOR_MASK_DC1) != 0u) {
            raw_dc1 |= ((MCP3201_MISO_DC1_PORT->IDR & dc1_mask) != 0u) ? 1u : 0u;
        }
        if ((mask & SENSOR_MASK_DC2) != 0u) {
            raw_dc2 |= ((MCP3201_MISO_DC2_PORT->IDR & dc2_mask) != 0u) ? 1u : 0u;
        }
        if ((mask & SENSOR_MASK_CUR) != 0u) {
            raw_cur |= ((MCP3201_MISO_CUR_PORT->IDR & cur_mask) != 0u) ? 1u : 0u;
        }

        gpio_reset(MCP3201_SCK_PORT, MCP3201_SCK_PIN);
        delay_half_period();
    }

    cs_set(mask);
    delay_half_period();

    /* MCP3201 SPI mode 0,0: 1.5 SCK sample, NULL bit clocked out on SCK 3 rising
     * edge, B11..B0 on SCK 4..15. After 16 shifts the 12 data bits land at
     * raw[12:1], so the correct extraction is (raw >> 1) & 0x0FFF. */
    if ((mask & SENSOR_MASK_DC1) != 0u) {
        samples->dc1 = (uint16_t)((raw_dc1 >> 1) & 0x0FFFu);
    }
    if ((mask & SENSOR_MASK_DC2) != 0u) {
        samples->dc2 = (uint16_t)((raw_dc2 >> 1) & 0x0FFFu);
    }
    if ((mask & SENSOR_MASK_CUR) != 0u) {
        samples->current = (uint16_t)((raw_cur >> 1) & 0x0FFFu);
    }
}
