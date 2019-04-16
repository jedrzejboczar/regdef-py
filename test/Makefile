UNITY_ROOT = ../Unity

CC = gcc
CXX = g++
FLAGS = -O2 \
		-I$(UNITY_ROOT)/src \
		-Wall -Wextra -Wno-missing-field-initializers
CFLAGS = $(FLAGS) -std=gnu99
CXXFLAGS = $(FLAGS) -std=c++2a

all: run

# code generation
gen: ../regdef.py tmc5041_regdef.gen.hpp tmc5041_regdef.gen.h

tmc5041_regdef.gen.hpp: tmc5041.regdef.json
	python ../regdef.py code tmc5041.regdef.json > tmc5041_regdef.gen.hpp

tmc5041_regdef.gen.h: tmc5041.regdef.json
	python ../regdef.py code -C -p TMC5041_ tmc5041.regdef.json > tmc5041_regdef.gen.h

# compilation
build: test_tmc5041_regdef-cpp test_tmc5041_regdef-c

test_tmc5041_regdef-cpp: test_tmc5041_regdef.cpp tmc5041_regdef.hpp tmc5041_regdef.gen.hpp
	$(CXX) $(CXXFLAGS) $(UNITY_ROOT)/src/unity.c test_tmc5041_regdef.cpp -o test_tmc5041_regdef-cpp

test_tmc5041_regdef-c: test_tmc5041_regdef.c tmc5041_regdef.h tmc5041_regdef.gen.h
	$(CC) $(CFLAGS) $(UNITY_ROOT)/src/unity.c test_tmc5041_regdef.c -o test_tmc5041_regdef-c

run: build
	./test_tmc5041_regdef-c
	./test_tmc5041_regdef-cpp

clean:
	rm -f test_tmc5041_regdef-c test_tmc5041_regdef-cpp *.gen.*

touch:
	touch *.json *.h *.hpp *.c *.cpp

.PHONY: all gen build run clean touch
