#include "stm32f3xx.h"
#include "fsm.h"
#include "pwm_modulator.h"
#include "sensing.h"
#include "spi_mcp3201.h"
#include "uart_telem.h"
#include <stdint.h>

#define TIMER_CLK_HZ 64000000u

static void SystemClock_Config(void);
static void GPIO_Config(void);
static void NVIC_Config(void);
static void System_Init(void);

static void SystemClock_Config(void)
{
    /* HSI -> PLL 64 MHz (no external crystal required, avoids unsupported PLL macros). */
    RCC->CR |= RCC_CR_HSION;
    while ((RCC->CR & RCC_CR_HSIRDY) == 0) {
    }

    FLASH->ACR = FLASH_ACR_PRFTBE | FLASH_ACR_LATENCY_2;

    RCC->CFGR = 0;
    RCC->CFGR |= RCC_CFGR_HPRE_DIV1;
    RCC->CFGR |= RCC_CFGR_PPRE1_DIV2;
    RCC->CFGR |= RCC_CFGR_PPRE2_DIV1;

    RCC->CFGR2 = RCC_CFGR2_PREDIV_DIV2;
    RCC->CFGR |= RCC_CFGR_PLLSRC_HSI_PREDIV | RCC_CFGR_PLLMUL16;

    RCC->CR |= RCC_CR_PLLON;
    while ((RCC->CR & RCC_CR_PLLRDY) == 0) {
    }

    RCC->CFGR &= ~RCC_CFGR_SW;
    RCC->CFGR |= RCC_CFGR_SW_PLL;
    while ((RCC->CFGR & RCC_CFGR_SWS) != RCC_CFGR_SWS_PLL) {
    }
}

static void GPIO_Config(void)
{
    RCC->AHBENR |= RCC_AHBENR_GPIOAEN | RCC_AHBENR_GPIOBEN;

    /* TIM1 on GPIOA: PA8/PA7/PA9/PA12 (CH1/CH1N/CH2/CH2N).
     * Build guide v3.1 lists PA10 for CH2N but PA10 has no TIM1_CH2N
     * alternate function on F303RE; PA12 is the correct pin. */
    GPIOA->MODER &= ~(GPIO_MODER_MODER7 | GPIO_MODER_MODER8 | GPIO_MODER_MODER9 |
                      GPIO_MODER_MODER12);
    GPIOA->MODER |= GPIO_MODER_MODER7_1 | GPIO_MODER_MODER8_1 | GPIO_MODER_MODER9_1 |
                     GPIO_MODER_MODER12_1;
    GPIOA->AFR[0] &= ~(0xFu << (7 * 4));
    GPIOA->AFR[1] &= ~((0xFu << ((8 - 8) * 4)) | (0xFu << ((9 - 8) * 4)) |
                      (0xFu << ((12 - 8) * 4)));
    GPIOA->AFR[0] |= (0x6u << (7 * 4));
    GPIOA->AFR[1] |= (0x6u << ((8 - 8) * 4)) | (0x6u << ((9 - 8) * 4)) |
                     (0x6u << ((12 - 8) * 4));

    /* TIM8 on GPIOB: PB6/PB3/PB8/PB0 (CH1/CH1N/CH2/CH2N).
     * Build guide v3.1 lists PC6-PC9 but only PC6 actually maps to TIM8_CH1;
     * PC7/PC8/PC9 map to CH2/CH3/CH4 not CH1N/CH2/CH2N. PB6/PB3/PB8/PB0 is
     * the correct combination for TIM8 complementary pairs on this package. */
    GPIOB->MODER &= ~(GPIO_MODER_MODER0 | GPIO_MODER_MODER3 | GPIO_MODER_MODER6 |
                      GPIO_MODER_MODER8);
    GPIOB->MODER |= GPIO_MODER_MODER0_1 | GPIO_MODER_MODER3_1 | GPIO_MODER_MODER6_1 |
                     GPIO_MODER_MODER8_1;
    GPIOB->AFR[0] &= ~((0xFu << (0 * 4)) | (0xFu << (3 * 4)) | (0xFu << (6 * 4)));
    GPIOB->AFR[1] &= ~(0xFu << ((8 - 8) * 4));
    GPIOB->AFR[0] |= (0x4u << (0 * 4)) | (0x4u << (3 * 4)) | (0x5u << (6 * 4));
    GPIOB->AFR[1] |= (0xAu << ((8 - 8) * 4));

    GPIOA->OTYPER &= ~(GPIO_OTYPER_OT_7 | GPIO_OTYPER_OT_8 | GPIO_OTYPER_OT_9 |
                       GPIO_OTYPER_OT_12);
    GPIOB->OTYPER &= ~(GPIO_OTYPER_OT_0 | GPIO_OTYPER_OT_3 | GPIO_OTYPER_OT_6 |
                       GPIO_OTYPER_OT_8);

    GPIOA->PUPDR &= ~(GPIO_PUPDR_PUPDR7 | GPIO_PUPDR_PUPDR8 | GPIO_PUPDR_PUPDR9 |
                      GPIO_PUPDR_PUPDR12);
    GPIOB->PUPDR &= ~(GPIO_PUPDR_PUPDR0 | GPIO_PUPDR_PUPDR3 | GPIO_PUPDR_PUPDR6 |
                      GPIO_PUPDR_PUPDR8);

    /* Medium speed reduces edge ringing on gate-drive traces while keeping timing margin. */
    GPIOA->OSPEEDR &= ~(GPIO_OSPEEDER_OSPEEDR7 | GPIO_OSPEEDER_OSPEEDR8 | GPIO_OSPEEDER_OSPEEDR9 |
                        GPIO_OSPEEDER_OSPEEDR12);
    GPIOA->OSPEEDR |= GPIO_OSPEEDER_OSPEEDR7_0 | GPIO_OSPEEDER_OSPEEDR8_0 |
                      GPIO_OSPEEDER_OSPEEDR9_0 | GPIO_OSPEEDER_OSPEEDR12_0;
    GPIOB->OSPEEDR &= ~(GPIO_OSPEEDER_OSPEEDR0 | GPIO_OSPEEDER_OSPEEDR3 | GPIO_OSPEEDER_OSPEEDR6 |
                        GPIO_OSPEEDER_OSPEEDR8);
    GPIOB->OSPEEDR |= GPIO_OSPEEDER_OSPEEDR0_0 | GPIO_OSPEEDER_OSPEEDR3_0 |
                      GPIO_OSPEEDER_OSPEEDR6_0 | GPIO_OSPEEDER_OSPEEDR8_0;

    /* FAULT_OUT on PB5: push-pull GPIO output, active-low. Driven HIGH here
     * (no fault) before the FSM starts; the FSM pulls it LOW on a latched
     * fault and releases it HIGH again on return to IDLE. */
    GPIOB->MODER &= ~GPIO_MODER_MODER5;
    GPIOB->MODER |= GPIO_MODER_MODER5_0;            /* general-purpose output */
    GPIOB->OTYPER &= ~GPIO_OTYPER_OT_5;             /* push-pull */
    GPIOB->PUPDR &= ~GPIO_PUPDR_PUPDR5;
    GPIOB->OSPEEDR &= ~GPIO_OSPEEDER_OSPEEDR5;      /* low speed is fine */
    GPIOB->BSRR = (1u << FAULT_OUT_PIN);            /* HIGH = no fault */
}

static void NVIC_Config(void)
{
    NVIC_SetPriority(TIM1_UP_TIM16_IRQn, 0);
    NVIC_EnableIRQ(TIM1_UP_TIM16_IRQn);
}

static void System_Init(void)
{
    SystemClock_Config();
    (void)SysTick_Config(TIMER_CLK_HZ / 1000u);
    NVIC_SetPriority(SysTick_IRQn, 15u);
    GPIO_Config();
    Pwm_Init();
    SPI_MCP3201_Init();
    UART_Init();
    Sensing_Init();
    NVIC_Config();
    FSM_Init();
}

int main(void)
{
    System_Init();

    while (1) {
        FSM_Run();
    }
}
