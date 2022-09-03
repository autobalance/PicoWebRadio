#include "ADC_DMA.h"
#include "fifo.h"

// error check the input channel elsewhere
#define ADC_PIN(adc_chan) (26 + (adc_chan))

// TODO: set these channels based on the helper functions in the Pico SDK ('claim unused')
#define DMA_CHAN_A 9
#define DMA_CHAN_B 10

fifo_t *fifos[MAX_FIFOS];

uint32_t adc_buf_idx;

// set the buffer as uint16_t type for alignment
#if BITS_PER_SAMPLE == 8
#if ((NSAMPLES / 2) * 2) == NSAMPLES
    uint16_t adc_buf[NBUFS][NSAMPLES/2];
#else
    #error NSAMPLES should be divisible by 2
#endif
#elif BITS_PER_SAMPLE == 12
    uint16_t adc_buf[NBUFS][NSAMPLES];
#else
    #error Unsupported BITS_PER_SAMPLE (specify 8 or 12)
#endif

// could use uPythons memory alignment helper functions to allow ring transfers,
// avoiding the use of interrupts (but still would need it to push buffer pointers
// to registered FIFOs)
void dma_handler(void)
{
    if (dma_hw->ints0 & (1 << DMA_CHAN_A))
    {
        for (int i = 0; i < MAX_FIFOS; i++)
        {
            fifo_push(fifos[i], (uint32_t *) adc_buf[(adc_buf_idx - 1) % NBUFS]);
        }

        adc_buf_idx = (adc_buf_idx + 1) % NBUFS;
        dma_hw->ch[DMA_CHAN_A].write_addr = (io_rw_32) adc_buf[adc_buf_idx];
        dma_hw->ints0 = 1u << DMA_CHAN_A;
    }
    else if (dma_hw->ints0 & (1 << DMA_CHAN_B))
    {
        for (int i = 0; i < MAX_FIFOS; i++)
        {
            fifo_push(fifos[i], (uint32_t *) adc_buf[(adc_buf_idx - 1) % NBUFS]);
        }

        adc_buf_idx = (adc_buf_idx + 1) % NBUFS;
        dma_hw->ch[DMA_CHAN_B].write_addr = (io_rw_32) adc_buf[adc_buf_idx];
        dma_hw->ints0 = 1u << DMA_CHAN_B;
    }
}

void adc_io_init(uint32_t adc_pin)
{
    // the macro 'IO_BANK0_GPIO26_CTRL_FUNCSEL_VALUE_NULL' is the same regardless of GPIO number
    iobank0_hw->io[adc_pin].ctrl = IO_BANK0_GPIO26_CTRL_FUNCSEL_VALUE_NULL;
    padsbank0_hw->io[adc_pin] = 0;
}

void adc_init(uint32_t adc_chan)
{
    adc_io_init(ADC_PIN(adc_chan));

    adc_hw->cs = 0;
    adc_hw->cs |= ADC_CS_EN_BITS;
    adc_hw->cs |= adc_chan << ADC_CS_AINSEL_LSB;

    adc_hw->fcs = 0;
    adc_hw->fcs |= ADC_FCS_EN_BITS | ADC_FCS_DREQ_EN_BITS;
    adc_hw->fcs |= 1 << ADC_FCS_THRESH_LSB;
    adc_hw->fcs |= 1 << ADC_FCS_OVER_LSB;
    adc_hw->fcs |= 1 << ADC_FCS_UNDER_LSB;
    if (BITS_PER_SAMPLE == 8)
        adc_hw->fcs |= 1 << ADC_FCS_SHIFT_LSB;

    adc_hw->div = (48000000ul / SAMPLE_RATE - 1) << ADC_DIV_INT_LSB;

    while (adc_hw->fcs & ADC_FCS_LEVEL_BITS)
    {
        adc_hw->fifo;
    }
}

void adc_dma_chan_init(uint32_t dma_chan, uint32_t dma_chainto_chan, void *p_buf)
{
    dma_hw->ch[dma_chan].read_addr = (io_rw_32) &(adc_hw->fifo);
    dma_hw->ch[dma_chan].write_addr = (io_rw_32) p_buf;
    dma_hw->ch[dma_chan].transfer_count = NSAMPLES;

    dma_hw->inte0 |= 1u << dma_chan;

    // macros for ctrl_trig bits seems the same for all channels
    dma_hw->ch[dma_chan].ctrl_trig = 0;
    dma_hw->ch[dma_chan].ctrl_trig |= dma_chainto_chan << DMA_CH0_CTRL_TRIG_CHAIN_TO_LSB;
    dma_hw->ch[dma_chan].ctrl_trig |= DMA_CH0_CTRL_TRIG_INCR_WRITE_BITS;
    dma_hw->ch[dma_chan].ctrl_trig |= DREQ_ADC << DMA_CH0_CTRL_TRIG_TREQ_SEL_LSB;
    #if BITS_PER_SAMPLE == 8
        dma_hw->ch[dma_chan].ctrl_trig |= DMA_CH0_CTRL_TRIG_DATA_SIZE_VALUE_SIZE_BYTE << DMA_CH0_CTRL_TRIG_DATA_SIZE_LSB;
    #elif BITS_PER_SAMPLE == 12
        dma_hw->ch[dma_chan].ctrl_trig |= DMA_CH0_CTRL_TRIG_DATA_SIZE_VALUE_SIZE_HALFWORD << DMA_CH0_CTRL_TRIG_DATA_SIZE_LSB;
    #endif
    dma_hw->ch[dma_chan].ctrl_trig |= DMA_CH0_CTRL_TRIG_EN_BITS;
}

void dma_init(void)
{
    adc_buf_idx = 0;

    adc_dma_chan_init(DMA_CHAN_A, DMA_CHAN_B, adc_buf[adc_buf_idx]);
    adc_dma_chan_init(DMA_CHAN_B, DMA_CHAN_A, adc_buf[++adc_buf_idx]);

    // may interfere with other modules built for MicroPython
    NVIC_SetVector(DMA_IRQ_0_IRQn, (uint32_t) dma_handler);
    NVIC_EnableIRQ(DMA_IRQ_0_IRQn);
}

void adc_dma_init(uint32_t adc_chan)
{
    for (int i = 0; i < MAX_FIFOS; i++)
    {
        fifos[i] = fifo_create(NBUFS);
    }

    adc_init(adc_chan);
    dma_init();
}

void adc_dma_start(void)
{
    adc_hw->cs |= ADC_CS_START_MANY_BITS;
}

// non-blocking buffer acquisition (to work with uPython asyncio)
uint16_t * adc_dma_get_buf(uint32_t fifo_id)
{
    if (fifo_id >= MAX_FIFOS)
    {
        return NULL;
    }

    return (uint16_t *) fifo_pop(fifos[fifo_id]);
}
