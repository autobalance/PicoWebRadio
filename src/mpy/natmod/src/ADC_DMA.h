/*******

    ADC acquisition using the DMA of the Raspberry Pi Pico.

    Idea from:
        https://iosoft.blog/2021/10/26/pico-adc-dma/

    but done using a native C module for MicroPython to use interrupts,
    though this may not have needed C.

    Ultimately, this would be better suited to using the standard Pico C/C++ SDK with CMake as
    the build tool. That is, use the modules provided in 'pico-sdk/src/rp2_common' without
    building anything extraneous (e.g. system init functions). For now this native MicroPython
    module is built using the register macros/structs (wrangled from the SDK by a custom utility),
    as mentioned in the RP2040 datasheet and the Pico C/C++ SDK manual.

    Note that total BSS memory used will be: NBUFS * NSAMPLES * ceil(BITS_PER_SAMPLE / 8).
    The default configuration here uses 48K (!) of memory to store about 1.6 seconds of audio.

    TODO: Until a way of doing real-time compression (MP3 or otherwise) is devised, maybe
          store the audio in memory using ADPCM. Note that it seems ADPCM-WAV files aren't
          supported in any browser, so we would need to decompress a buffer that is retrieved
          from a FIFO holding ADPCM data.

*******/

#ifndef __ADC_DMA_H__
#define __ADC_DMA_H__

#include "RP2040_structs.h"
#include "RP2040_regs.h"   // needed for DREQ constants, or just include "hardware/regs/dreq.h"

#define ADC_NCHANS 4

// make sure sample rate divides 48MHz, otherwise actual sample rate will be different
#define SAMPLE_RATE 30000
#define NCHANNELS 1
#define BITS_PER_SAMPLE 8

#define NSAMPLES 3000

// TODO: allow non power-of-2 buffer sizes in the FIFO
#define NBUFS 16

// TODO: investigate how to make more than 1 audio stream on the server work without hiccups
#define MAX_FIFOS 1

void adc_dma_init(uint32_t adc_chan);

void adc_dma_start(void);

uint16_t * adc_dma_get_buf(uint32_t fifo_id);

#endif
