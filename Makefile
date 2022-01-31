PY_FILES = fancontrol.py constants.py mpu6050.py simplelog.py switch.py
MPY_FILES = $(PY_FILES:.py=.mpy)

%.mpy: %.py
	mpy-cross -o $@ $<

%.svg: %.dot
	dot -Tsvg -o $@ $<

all: $(MPY_FILES)
