BUILD_DIR = build
TEST_DIR = test

MPY_NM_DIR = src/mpy/natmod
MPY_NM = WAVBuffer.mpy

MPY_DIR = src/mpy
MPY = $(shell find $(MPY_DIR)/* -maxdepth 1 -type f -name '*.py')

WEB_DIR = src/web

RP2_DEV = /dev/ttyACM0

.PHONY: all build natmod flash test clean

all: build

build: natmod
	@mkdir -p $(BUILD_DIR)
	@cp -a $(MPY_NM_DIR)/$(MPY_NM) $(BUILD_DIR)
	@cp -a $(MPY) $(BUILD_DIR)
	@cp -a $(WEB_DIR)/* $(BUILD_DIR)

natmod: $(MPY_NM)

$(MPY_NM):
	$(MAKE) -C $(MPY_NM_DIR) BUILD=build

flash: build
	rshell -p $(RP2_DEV) --buffer-size 512 "cp -r $(BUILD_DIR)/* /pyboard/"

test:
	@cp -r $(WEB_DIR) $(TEST_DIR)
	@cp $(TEST_DIR)/stations.xml $(TEST_DIR)/web/

clean:
	$(MAKE) -C $(MPY_NM_DIR) BUILD=build clean
	rm -rf $(BUILD_DIR)
	rm -rf $(TEST_DIR)/web
