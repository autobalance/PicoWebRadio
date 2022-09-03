/*
    A quick-and-dirty lossy FIFO to help with managing access to the audio buffer.
    Pushing an item onto a full FIFO here will evict the first item entered.
    Allows for dropping data when the system (e.g. network) is too slow to keep up.
*/

#ifndef __FIFO_H__
#define __FIFO_H__

#include "py/dynruntime.h"
#include "py/misc.h"

#include "critical_section.h"

// a hack since '__aeabi_uidivmod' doesn't seem to be accesible when compiling for MicroPython
// NOTE: only does modulo with power of 2 divisors!
static inline uint32_t mod_pow2(uint32_t m, uint32_t n)
{
    return m & (n-1);
}

typedef struct fifo_struct
{
    uint32_t head_idx;
    uint32_t tail_idx;
    uint32_t **data;
    uint32_t length;
} fifo_t;

static inline fifo_t *fifo_create(uint32_t length)
{
    volatile uint32_t primask = critical_section_enter();

    fifo_t *fifo = m_new(fifo_t, 1);

    // TODO: deal with non-power of 2 FIFO lengths
    fifo->head_idx = 0;
    fifo->tail_idx = 0;
    fifo->data = m_new(uint32_t *, length);
    for (volatile uint32_t i = 0; i < length; i++)
        fifo->data[i] = NULL;
    fifo->length = length;

    critical_section_exit(primask);

    return fifo;
}

static inline bool fifo_empty(fifo_t *fifo)
{
    volatile uint32_t primask = critical_section_enter();

    uint32_t *head_data = fifo->data[fifo->head_idx];

    critical_section_exit(primask);

    return head_data == NULL;
}

static inline bool fifo_full(fifo_t *fifo)
{
    volatile uint32_t primask = critical_section_enter();

    uint32_t head_idx = fifo->head_idx;
    uint32_t tail_idx = fifo->tail_idx;
    uint32_t *head_data = fifo->data[fifo->head_idx];

    critical_section_exit(primask);

    return (head_idx == tail_idx) && (head_data != NULL);
}

static inline uint32_t *fifo_pop(fifo_t *fifo)
{
    volatile uint32_t primask = critical_section_enter();

    uint32_t *data = NULL;

    if (!fifo_empty(fifo))
    {
        data = fifo->data[fifo->head_idx];

        fifo->data[fifo->head_idx] = NULL;
        fifo->head_idx = mod_pow2(fifo->head_idx + 1, fifo->length);
    }

    critical_section_exit(primask);

    return data;
}

static inline void fifo_push(fifo_t *fifo, uint32_t *new_data)
{
    volatile uint32_t primask = critical_section_enter();

    if (fifo_full(fifo))
    {
        fifo->head_idx = mod_pow2(fifo->head_idx + 1, fifo->length);
    }

    fifo->data[fifo->tail_idx] = new_data;
    fifo->tail_idx = mod_pow2(fifo->tail_idx + 1, fifo->length);

    critical_section_exit(primask);
}

static inline void fifo_destroy(fifo_t **fifo)
{
    volatile uint32_t primask = critical_section_enter();

    if ((fifo == NULL) || (*fifo == NULL))
    {
        return;
    }

    m_del(uint32_t *, (*fifo)->data, (*fifo)->length);
    m_del(fifo_t, *fifo, 1);

    critical_section_exit(primask);
}

#endif
