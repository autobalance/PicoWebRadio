/*
    Helper functions for modifying data that can change in interrupts/threaded code.
    General principle found here:
        https://stm32f4-discovery.net/2015/06/how-to-properly-enabledisable-interrupts-in-arm-cortex-m/

    TODO: Look into using the locking mechanisms provided by the Pico SDK when porting
          the native module to use the Pico SDK standard library.
*/

#ifndef __CRITICAL_SECTION_H__
#define __CRITICAL_SECTION_H__

#include "core_cm0plus.h"

static inline volatile uint32_t critical_section_enter(void)
{
    volatile uint32_t primask = __get_PRIMASK();

    __disable_irq();

    return primask;
}

static inline void critical_section_exit(volatile uint32_t primask)
{
    if (!primask)
    {
        __enable_irq();
    }
}

#endif
