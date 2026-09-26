# Host-side unit tests for portable modules (run on the development machine).
#   make -C tests/host
CC     ?= cc
CFLAGS := -std=gnu99 -Wall -Wextra -Werror -g -fsanitize=address,undefined \
          -I../../arm9/include

.PHONY: all clean
all: test_qr_type
	./test_qr_type

test_qr_type: test_qr_type.c ../../arm9/src/qr_type.c ../../arm9/include/qr_type.h
	$(CC) $(CFLAGS) -o $@ test_qr_type.c ../../arm9/src/qr_type.c

clean:
	rm -rf test_qr_type test_qr_type.dSYM
