#include "uart_telem.h"
#include "protection.h"
#include <string.h>

#define UART_TX_BUFFER_SIZE 512u
#define UART_RX_LINE_SIZE 40u

static volatile uint8_t g_tx_buffer[UART_TX_BUFFER_SIZE];
static volatile uint16_t g_tx_head = 0u;
static volatile uint16_t g_tx_tail = 0u;

static volatile char g_rx_line[UART_RX_LINE_SIZE];
static volatile uint8_t g_rx_len = 0u;
static volatile uint8_t g_rx_ready = 0u;
static volatile char g_rx_ready_line[UART_RX_LINE_SIZE];

static inline uint32_t pin_mask(uint32_t pin)
{
    return (1u << pin);
}

static void append_char(char *buf, uint32_t *pos, uint32_t max, char c)
{
    if (*pos < (max - 1u)) {
        buf[*pos] = c;
        *pos += 1u;
        buf[*pos] = '\0';
    }
}

static void append_str(char *buf, uint32_t *pos, uint32_t max, const char *text)
{
    while (*text != '\0') {
        append_char(buf, pos, max, *text);
        text++;
    }
}

static void append_u32(char *buf, uint32_t *pos, uint32_t max, uint32_t value)
{
    char tmp[10];
    uint32_t count = 0u;

    if (value == 0u) {
        append_char(buf, pos, max, '0');
        return;
    }

    while ((value != 0u) && (count < sizeof(tmp))) {
        tmp[count] = (char)('0' + (value % 10u));
        value /= 10u;
        count++;
    }
    while (count > 0u) {
        count--;
        append_char(buf, pos, max, tmp[count]);
    }
}

static void append_hex8(char *buf, uint32_t *pos, uint32_t max, uint8_t value)
{
    static const char hex[] = "0123456789ABCDEF";
    append_str(buf, pos, max, "0x");
    append_char(buf, pos, max, hex[(value >> 4) & 0x0Fu]);
    append_char(buf, pos, max, hex[value & 0x0Fu]);
}

static void append_i32(char *buf, uint32_t *pos, uint32_t max, int32_t value)
{
    uint32_t mag;

    if (value < 0) {
        append_char(buf, pos, max, '-');
        mag = (uint32_t)(-value);
    } else {
        mag = (uint32_t)value;
    }
    append_u32(buf, pos, max, mag);
}

static void append_fixed2(char *buf, uint32_t *pos, uint32_t max, float value)
{
    int32_t scaled;
    int32_t whole;
    int32_t frac;

    if (value < 0.0f) {
        scaled = (int32_t)((value * 100.0f) - 0.5f);
    } else {
        scaled = (int32_t)((value * 100.0f) + 0.5f);
    }

    whole = scaled / 100;
    frac = scaled % 100;
    if (frac < 0) {
        frac = -frac;
    }

    append_i32(buf, pos, max, whole);
    append_char(buf, pos, max, '.');
    append_char(buf, pos, max, (char)('0' + (frac / 10)));
    append_char(buf, pos, max, (char)('0' + (frac % 10)));
}

static void append_sensor_value(char *buf, uint32_t *pos, uint32_t max, float value, uint8_t valid)
{
    if (valid == 0u) {
        append_str(buf, pos, max, "NAN");
    } else {
        append_fixed2(buf, pos, max, value);
    }
}

static void append_fault_names(char *buf, uint32_t *pos, uint32_t max, uint8_t faults)
{
    uint8_t first = 1u;

    if (faults == FAULT_NONE) {
        append_str(buf, pos, max, "NONE");
        return;
    }

#define APPEND_FAULT(bit, name)                       \
    do {                                              \
        if ((faults & (bit)) != 0u) {                  \
            if (first == 0u) {                         \
                append_char(buf, pos, max, '|');       \
            }                                         \
            append_str(buf, pos, max, (name));         \
            first = 0u;                                \
        }                                             \
    } while (0)

    APPEND_FAULT(FAULT_UV, "UV");
    APPEND_FAULT(FAULT_OV, "OV");
    APPEND_FAULT(FAULT_OC, "OC");
    APPEND_FAULT(FAULT_IMBAL, "IMBAL");
    APPEND_FAULT(FAULT_SENSOR_LOST, "SENSOR_LOST");

#undef APPEND_FAULT
}

static uint8_t nmea_checksum(const char *payload)
{
    uint8_t chk = 0u;

    while (*payload != '\0') {
        chk ^= (uint8_t)(*payload);
        payload++;
    }
    return chk;
}

static void send_nmea_payload(const char *payload)
{
    char line[160];
    uint32_t pos = 0u;
    uint8_t chk = nmea_checksum(payload);
    static const char hex[] = "0123456789ABCDEF";

    append_char(line, &pos, sizeof(line), '$');
    append_str(line, &pos, sizeof(line), payload);
    append_char(line, &pos, sizeof(line), '*');
    append_char(line, &pos, sizeof(line), hex[(chk >> 4) & 0x0Fu]);
    append_char(line, &pos, sizeof(line), hex[chk & 0x0Fu]);
    append_str(line, &pos, sizeof(line), "\r\n");
    UART_WriteString(line);
}

static void uart_write_byte(uint8_t byte)
{
    uint16_t next = (uint16_t)((g_tx_head + 1u) % UART_TX_BUFFER_SIZE);

    if (next == g_tx_tail) {
        return;
    }

    g_tx_buffer[g_tx_head] = byte;
    g_tx_head = next;
    USART2->CR1 |= USART_CR1_TXEIE;
}

void UART_Init(void)
{
    RCC->AHBENR |= RCC_AHBENR_GPIOAEN;
    RCC->APB1ENR |= RCC_APB1ENR_USART2EN;

    GPIOA->MODER &= ~(GPIO_MODER_MODER2 | GPIO_MODER_MODER3);
    GPIOA->MODER |= GPIO_MODER_MODER2_1 | GPIO_MODER_MODER3_1;
    GPIOA->AFR[0] &= ~((0xFu << (UART_VCP_TX_PIN * 4u)) | (0xFu << (UART_VCP_RX_PIN * 4u)));
    GPIOA->AFR[0] |= (0x7u << (UART_VCP_TX_PIN * 4u)) | (0x7u << (UART_VCP_RX_PIN * 4u));
    GPIOA->PUPDR &= ~(GPIO_PUPDR_PUPDR2 | GPIO_PUPDR_PUPDR3);
    GPIOA->PUPDR |= GPIO_PUPDR_PUPDR3_0;
    GPIOA->OSPEEDR &= ~(GPIO_OSPEEDER_OSPEEDR2 | GPIO_OSPEEDER_OSPEEDR3);
    GPIOA->OSPEEDR |= GPIO_OSPEEDER_OSPEEDR2_0 | GPIO_OSPEEDER_OSPEEDR3_0;

    USART2->CR1 = 0u;
    USART2->CR2 = 0u;
    USART2->CR3 = 0u;
    USART2->BRR = (CONFIG_APB1_CLK_HZ + (CONFIG_UART_BAUD / 2u)) / CONFIG_UART_BAUD;
    USART2->ICR = 0xFFFFFFFFu;
    USART2->CR1 = USART_CR1_TE | USART_CR1_RE | USART_CR1_RXNEIE | USART_CR1_UE;

    NVIC_SetPriority(USART2_IRQn, 3u);
    NVIC_EnableIRQ(USART2_IRQn);
}

void UART_USART2_IRQHandler(void)
{
    uint32_t isr = USART2->ISR;

    if ((isr & (USART_ISR_ORE | USART_ISR_FE | USART_ISR_NE | USART_ISR_PE)) != 0u) {
        USART2->ICR = USART_ICR_ORECF | USART_ICR_FECF | USART_ICR_NCF | USART_ICR_PECF;
    }

    if ((isr & USART_ISR_RXNE) != 0u) {
        char c = (char)(USART2->RDR & 0xFFu);

        if ((c == '\n') || (c == '\r')) {
            if ((g_rx_len > 0u) && (g_rx_ready == 0u)) {
                for (uint32_t i = 0; i < g_rx_len; i++) {
                    g_rx_ready_line[i] = g_rx_line[i];
                }
                g_rx_ready_line[g_rx_len] = '\0';
                g_rx_ready = 1u;
            }
            g_rx_len = 0u;
        } else if (g_rx_len < (UART_RX_LINE_SIZE - 1u)) {
            g_rx_line[g_rx_len] = c;
            g_rx_len++;
        } else {
            g_rx_len = 0u;
        }
    }

    if (((USART2->CR1 & USART_CR1_TXEIE) != 0u) && ((USART2->ISR & USART_ISR_TXE) != 0u)) {
        if (g_tx_tail != g_tx_head) {
            USART2->TDR = g_tx_buffer[g_tx_tail];
            g_tx_tail = (uint16_t)((g_tx_tail + 1u) % UART_TX_BUFFER_SIZE);
        } else {
            USART2->CR1 &= ~USART_CR1_TXEIE;
        }
    }
}

void UART_WriteString(const char *text)
{
    while ((text != (const char *)0) && (*text != '\0')) {
        uart_write_byte((uint8_t)(*text));
        text++;
    }
}

static uint8_t parse_mode_arg(const char *text, uint8_t *mode)
{
    if ((text[0] >= '0') && (text[0] <= '5') && (text[1] == '\0')) {
        *mode = (uint8_t)(text[0] - '0');
        return 1u;
    }
    return 0u;
}

static uint8_t parse_mi_arg(const char *text, float *value)
{
    uint32_t i = 0u;
    uint32_t int_part = 0u;
    uint32_t frac_part = 0u;
    uint32_t frac_div = 1u;
    uint8_t saw_digit = 0u;

    while ((text[i] >= '0') && (text[i] <= '9')) {
        saw_digit = 1u;
        int_part = (int_part * 10u) + (uint32_t)(text[i] - '0');
        i++;
    }

    if (text[i] == '.') {
        i++;
        while ((text[i] >= '0') && (text[i] <= '9') && (frac_div < 1000000u)) {
            saw_digit = 1u;
            frac_part = (frac_part * 10u) + (uint32_t)(text[i] - '0');
            frac_div *= 10u;
            i++;
        }
    }

    if ((saw_digit == 0u) || (text[i] != '\0')) {
        return 0u;
    }

    *value = (float)int_part + ((float)frac_part / (float)frac_div);
    return 1u;
}

static void parse_command(uart_command_t *cmd, const char *line)
{
    uint32_t i = 0u;

    cmd->type = UART_CMD_INVALID;
    cmd->mode_arg = 0u;
    cmd->float_arg = 0.0f;
    while ((line[i] != '\0') && (i < (sizeof(cmd->raw) - 1u))) {
        cmd->raw[i] = line[i];
        i++;
    }
    cmd->raw[i] = '\0';

    if (strcmp(line, "START") == 0) {
        cmd->type = UART_CMD_START;
    } else if (strcmp(line, "STOP") == 0) {
        cmd->type = UART_CMD_STOP;
    } else if (strcmp(line, "CLEAR") == 0) {
        cmd->type = UART_CMD_CLEAR;
    } else if (strcmp(line, "STATUS") == 0) {
        cmd->type = UART_CMD_STATUS;
    } else if (strcmp(line, "HELP") == 0) {
        cmd->type = UART_CMD_HELP;
    } else if (strncmp(line, "MODE ", 5u) == 0) {
        if (parse_mode_arg(&line[5], &cmd->mode_arg) != 0u) {
            cmd->type = UART_CMD_MODE;
        }
    } else if (strncmp(line, "MI ", 3u) == 0) {
        if (parse_mi_arg(&line[3], &cmd->float_arg) != 0u) {
            cmd->type = UART_CMD_MI;
        }
    }
}

uint8_t UART_GetCommand(uart_command_t *cmd)
{
    char local[UART_RX_LINE_SIZE];
    uint8_t ready;

    if (cmd == (uart_command_t *)0) {
        return 0u;
    }

    __disable_irq();
    ready = g_rx_ready;
    if (ready != 0u) {
        for (uint32_t i = 0u; i < UART_RX_LINE_SIZE; i++) {
            local[i] = (char)g_rx_ready_line[i];
            if (local[i] == '\0') {
                break;
            }
        }
        g_rx_ready = 0u;
    }
    __enable_irq();

    if (ready == 0u) {
        return 0u;
    }

    parse_command(cmd, local);
    return 1u;
}

void UART_SendAck(const char *cmd)
{
    UART_WriteString("$A,");
    UART_WriteString(cmd);
    UART_WriteString("\r\n");
}

void UART_SendError(const char *reason)
{
    UART_WriteString("$E,");
    UART_WriteString(reason);
    UART_WriteString("\r\n");
}

void UART_SendFault(uint8_t faults)
{
    char line[96];
    uint32_t pos = 0u;

    append_str(line, &pos, sizeof(line), "$F,");
    append_hex8(line, &pos, sizeof(line), faults);
    append_char(line, &pos, sizeof(line), ',');
    append_fault_names(line, &pos, sizeof(line), faults);
    append_str(line, &pos, sizeof(line), "\r\n");
    UART_WriteString(line);
}

void UART_SendHelp(void)
{
    UART_WriteString("$H,START STOP CLEAR MODE 0..5 STATUS HELP MI 0.0..0.95\r\n");
}

const char *UART_StateName(fsm_state_t state)
{
    switch (state) {
    case FSM_STATE_BOOT:
        return "BOOT";
    case FSM_STATE_IDLE:
        return "IDLE";
    case FSM_STATE_PRECHARGE:
        return "PRECHARGE";
    case FSM_STATE_RUN:
        return "RUN";
    case FSM_STATE_FAULT:
    default:
        return "FAULT";
    }
}

const char *UART_ModeName(sensing_mode_t mode)
{
    switch (mode) {
    case MODE_FULL:
        return "FULL";
    case MODE_DC_ONLY:
        return "DC_ONLY";
    case MODE_CURRENT_ONLY:
        return "CUR_ONLY";
    case MODE_OPEN_LOOP:
        return "OPEN";
    case MODE_DC1_ONLY:
        return "DC1";
    case MODE_DC2_ONLY:
    default:
        return "DC2";
    }
}

void UART_SendStatus(uint32_t ms,
                     fsm_state_t state,
                     sensing_mode_t mode,
                     uint8_t faults,
                     const sensing_data_t *data,
                     float modulation_index)
{
    char line[180];
    uint32_t pos = 0u;
    uint8_t avail = Sensing_GetAvailableMask();

    append_str(line, &pos, sizeof(line), "$S,ms=");
    append_u32(line, &pos, sizeof(line), ms);
    append_str(line, &pos, sizeof(line), ",state=");
    append_str(line, &pos, sizeof(line), UART_StateName(state));
    append_str(line, &pos, sizeof(line), ",mode=");
    append_str(line, &pos, sizeof(line), UART_ModeName(mode));
    append_str(line, &pos, sizeof(line), ",fault=");
    append_hex8(line, &pos, sizeof(line), faults);
    append_str(line, &pos, sizeof(line), ",avail=");
    append_hex8(line, &pos, sizeof(line), avail);
    append_str(line, &pos, sizeof(line), ",vdc1=");
    append_sensor_value(line, &pos, sizeof(line), data->dc1.filtered_value, data->dc1.initialized);
    append_str(line, &pos, sizeof(line), ",vdc2=");
    append_sensor_value(line, &pos, sizeof(line), data->dc2.filtered_value, data->dc2.initialized);
    append_str(line, &pos, sizeof(line), ",iout=");
    append_sensor_value(line, &pos, sizeof(line), data->current.filtered_value, data->current.initialized);
    append_str(line, &pos, sizeof(line), ",mi=");
    append_fixed2(line, &pos, sizeof(line), modulation_index);
    append_str(line, &pos, sizeof(line), "\r\n");
    UART_WriteString(line);
}

void UART_SendTelemetry(uint32_t ms,
                        fsm_state_t state,
                        sensing_mode_t mode,
                        uint8_t faults,
                        const sensing_data_t *data,
                        int8_t level)
{
    char payload[150];
    uint32_t pos = 0u;
    uint8_t vdc1_valid = ((Sensing_ModeUsesDc1ForTelemetry(mode) != 0u) &&
                          (data->dc1.available != 0u)) ? 1u : 0u;
    uint8_t vdc2_valid = ((Sensing_ModeUsesDc2ForTelemetry(mode) != 0u) &&
                          (data->dc2.available != 0u)) ? 1u : 0u;
    uint8_t cur_valid = ((Sensing_ModeUsesCurrentForTelemetry(mode) != 0u) &&
                         (data->current.available != 0u)) ? 1u : 0u;

    append_str(payload, &pos, sizeof(payload), "T,");
    append_u32(payload, &pos, sizeof(payload), ms);
    append_char(payload, &pos, sizeof(payload), ',');
    append_str(payload, &pos, sizeof(payload), UART_StateName(state));
    append_char(payload, &pos, sizeof(payload), ',');
    append_str(payload, &pos, sizeof(payload), UART_ModeName(mode));
    append_char(payload, &pos, sizeof(payload), ',');
    append_hex8(payload, &pos, sizeof(payload), faults);
    append_char(payload, &pos, sizeof(payload), ',');
    append_sensor_value(payload, &pos, sizeof(payload), data->dc1.filtered_value, vdc1_valid);
    append_char(payload, &pos, sizeof(payload), ',');
    append_sensor_value(payload, &pos, sizeof(payload), data->dc2.filtered_value, vdc2_valid);
    append_char(payload, &pos, sizeof(payload), ',');
    append_sensor_value(payload, &pos, sizeof(payload), data->current.filtered_value, cur_valid);
    append_char(payload, &pos, sizeof(payload), ',');
    append_i32(payload, &pos, sizeof(payload), (int32_t)level);

    send_nmea_payload(payload);
}
