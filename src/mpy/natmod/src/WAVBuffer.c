/*******

    A WAV file buffer/encoder using the ADC_DMA module. See the header of 'ADC_DMA.h'
    for more info on the implementation details.

*******/

// Include the header file to get access to the MicroPython API
#include "py/dynruntime.h"
#include "ADC_DMA.h"

// for memcpy
#include <string.h>

// based on http://soundfile.sapp.org/doc/WaveFormat/
typedef struct wav_header_struct
{
    char      ChunkID[4];
    uint32_t  ChunkSize;
    char      Format[4];
    char      Subchunk1ID[4];
    uint32_t  Subchunk1Size;
    uint16_t  AudioFormat;
    uint16_t  NumChannels;
    uint32_t  SampleRate;
    uint32_t  ByteRate;
    uint16_t  BlockAlign;
    uint16_t  BitsPerSample;
    char      Subchunk2ID[4];
    uint32_t  Subchunk2Size;
} wav_header_t;

wav_header_t wav_header;

// TODO: Create an endian-independent header initializer.
void wav_header_init(void)
{
    memcpy(wav_header.ChunkID, "RIFF", 4);
    wav_header.ChunkSize = 0xffffffff; // max size to indicate endless stream
    memcpy(wav_header.Format, "WAVE", 4);

    memcpy(wav_header.Subchunk1ID, "fmt ", 4);
    wav_header.Subchunk1Size = 16; // PCM
    wav_header.AudioFormat = 1;    // PCM
    wav_header.NumChannels = NCHANNELS;
    wav_header.SampleRate = SAMPLE_RATE;
    wav_header.ByteRate = SAMPLE_RATE * NCHANNELS * (BITS_PER_SAMPLE / 8);
    wav_header.BlockAlign = NCHANNELS * (BITS_PER_SAMPLE / 8);
    wav_header.BitsPerSample = BITS_PER_SAMPLE;

    memcpy(wav_header.Subchunk2ID, "data", 4);
    wav_header.Subchunk2Size = 0xffffffff; // max size to indicate endless stream
}


STATIC mp_obj_t header(void)
{
    return mp_obj_new_bytearray_by_ref(sizeof(wav_header_t), &wav_header);
}
STATIC MP_DEFINE_CONST_FUN_OBJ_0(header_obj, header);


STATIC mp_obj_t init(mp_obj_t adc_chan_in)
{
    mp_int_t adc_chan = mp_obj_get_int(adc_chan_in);
    if (adc_chan < 0 || adc_chan >= ADC_NCHANS)
    {
        mp_raise_ValueError(MP_ERROR_TEXT("No such ADC channel: choose between 0 to 3"));
    }

    wav_header_init();
    adc_dma_init(adc_chan);

    return mp_const_none;
}
STATIC MP_DEFINE_CONST_FUN_OBJ_1(init_obj, init);

// would do this in 'init' above, but starting ADC_DMA before a WLAN connection crashes
// (maybe uPython network code uses DMA when connecting?)
STATIC mp_obj_t start(void)
{
    adc_dma_start();

    return mp_const_none;
}
STATIC MP_DEFINE_CONST_FUN_OBJ_0(start_obj, start);

// non-blocking buffer acquisition (to work with uPython asyncio)
// returns non-empty buffer iff FIFO is non-empty
STATIC mp_obj_t fetch(mp_obj_t idx_in)
{
    mp_int_t idx = mp_obj_get_int(idx_in);
    if (idx < 0 || idx >= MAX_FIFOS)
    {
        mp_raise_ValueError(MP_ERROR_TEXT("No more FIFOs available"));
    }

    uint16_t *p_buf = adc_dma_get_buf(idx);
    if (!p_buf)
    {   // works, but may be better to use a dummy variable?
        return mp_obj_new_bytearray_by_ref(0, NULL);
    }

    size_t bytes_per_sample = 0;
    #if BITS_PER_SAMPLE == 8
        bytes_per_sample = 1;
    #elif BITS_PER_SAMPLE == 12
        bytes_per_sample = 2;
    #endif

    return mp_obj_new_bytearray_by_ref(bytes_per_sample * NSAMPLES, p_buf);
}
STATIC MP_DEFINE_CONST_FUN_OBJ_1(fetch_obj, fetch);

// This is the entry point and is called when the module is imported
mp_obj_t mpy_init(mp_obj_fun_bc_t *self, size_t n_args, size_t n_kw, mp_obj_t *args)
{
    // This must be first, it sets up the globals dict and other things
    MP_DYNRUNTIME_INIT_ENTRY

    mp_store_global(MP_QSTR_header, MP_OBJ_FROM_PTR(&header_obj));
    mp_store_global(MP_QSTR_init, MP_OBJ_FROM_PTR(&init_obj));
    mp_store_global(MP_QSTR_start, MP_OBJ_FROM_PTR(&start_obj));
    mp_store_global(MP_QSTR_fetch, MP_OBJ_FROM_PTR(&fetch_obj));

    // This must be last, it restores the globals dict
    MP_DYNRUNTIME_INIT_EXIT
}
