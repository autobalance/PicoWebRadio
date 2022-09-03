MPY_DIR = ext/micropython
PICO_SDK_PATH = ext/pico-sdk

MOD = WAVBuffer
CLEAN_EXTRA=$(MOD).mpy

SRC += src/ADC_DMA.h src/ADC_DMA.c
SRC += src/critical_section.h
SRC += src/fifo.h
SRC += src/WAVBuffer.c

ARCH = armv6m

# for 'RP2040.h and 'core_cm0plus.h' from CMSIS
CFLAGS += -I$(PICO_SDK_PATH)/src/rp2_common/cmsis/stub/CMSIS/Device/RaspberryPi/RP2040/Include
CFLAGS += -I$(PICO_SDK_PATH)/src/rp2_common/cmsis/stub/CMSIS/Core/Include

# Raspberry Pi provided register macros and structs
CFLAGS += -I$(PICO_SDK_PATH)/src/rp2040/hardware_regs/include
CFLAGS += -I$(PICO_SDK_PATH)/src/rp2040/hardware_structs/include

# wrangled headers for regs/structs above, and hack to define necessary types/functions
CFLAGS += -Iinclude

CFLAGS += -Isrc

include $(MPY_DIR)/py/dynruntime.mk
