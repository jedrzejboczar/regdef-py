# regdef-py

Simple script for generating C/C++ register access code based on a register description written as JSON file.


Why did I do this? Maybe I have to much time. But whenever I have to access registers of some chip, I try to find some libraries/headers on the internet. But, if I find something, then it is usually some Arduino code, or just a simple list of register addresses, or some BSP that just does and weights too much. I just wanted to check if the approach taken here is general enough to be useful in regular projects (and no, I didn't find any free to use thing like this on the web).

The code in *regdef.py* is quite...bad, but it has been done quickly, this is still just a proof of concept. If this proves to be useful, then we can think about refactoring or something.

Most probably it could have been done better, any feedback welcome.

## Register description

Register is defined by a name, address. A list of addresses for registers that are the same internally but correspond e.g. to different peripherals. Then we define fields in the register using a syntax `NAME:POSITION`. `NAME` can be set to `_` if we want to described reserved area (currently reserved areas are always set to 0). `POSITION` can take one of 3 forms:

- `BIT`, which means that the field is a single bit at given position (starting from 0)
- `START:END`, which defines a bitfield from `START` to `END` (inclusive, e.g. `0:2` means bits 0, 1 and 2); also the order can be changed to `END:START`
- `@NUM`, which defines a bitfield with length of `NUM` bits, starting from last defined field; if this is the first field, then it starts from bit 0

The important thing is to define fields sequentially. By default order starting from 0 is assumed, but it can be reversed, i.e. we can define fields as `FIELD1:31:20 FIELD2:19:2 FIELD3:@1 FIELD4:0` (in such case, positions of the first field have to be explicit).

## Generated code API

Register access has always been somewhat problematic and error prone. If we are concerned about super-efficiency, then probably the best we can do is to use `#define` only. Or maybe some cpp-fu black magic with templates.

The approach taken here is to use structures with bitfields. This gives quite a nice and elegant way for bit access and the compiler has to do the hard work for us. Unfortunately C/C++ standards don't give any guarantee on memory layout of such a struct, so we can't access the raw memory directly. Because of this a pair of methods/macros is generated for converting to/from raw data to the register structure. These should probably be fast and optimized away with compiler optimizations enabled, while allow for quite nice-to-use API. Then, to resolve endianess problems, we can just use standard C library functions, like `htonl()` and `ntohl()`.

One could want the registers in C++ code to derive from some abstract `Register` base class. But I feel like this would unnecessarily complicate the whole design. These structures are meant to be used temporarily for accessing fields. When we need to store multiple registers continuously in memory, an array of unsigned integers would do. And we would just convert to structures when actually needed. And for dispatching on the register type, we can just check the register's address and use a switch.

## Tests

In *test/* there are some Unity tests for register description of Trinamic TMC5041 chip. Unity is added here as a git-submodule so it has to the repository has to be cloned recursively. Then just use the *Makefile* provided, it should hopefully just work (on Linux).

## Requirements

The script is simple, is written in Python 3 and has no other dependencies. The generated code in the current form requires C99 or C++20 (yes, -std=c++2a, we use the, so called, "designated initializers" that are in C since C99 but C++ didn't have them for quite a long time). Maybe this could be done more portably but for now I didn't care.

## Example

Let's take the TMC5041 Trinamic stepper motor driver chip. Some example registers of the chip can be described in *tmc5041.regdef.json* as follows:

```json
"X_COMPARE": {
    "address": "0x05",
    "defs": [
        "x_compare:@32"
    ]
},
"IHOLD_IRUN": {
    "address": ["0x30", "0x50"],
    "defs": [
        "ihold:0:4",
        "_:5:7",
        "irun:12:8",
        "_:15:13",
        "iholddelay:19:16"
    ]
},
"SW_MODE": {
    "address": ["0x34", "0x54"],
    "defs": [
        "stop_l_enable:0",
        "stop_r_enable:1",
        "pol_stop_l:2",
        "pol_stop_r:3",
        "swap_lr:4",
        "latch_l_active:5",
        "latch_l_inactive:6",
        "latch_r_active:7",
        "latch_r_inactive:8",
        "_:9",
        "sg_stop:10",
        "en_softstop:11"
    ]
},
```

To see the internal representation of the registers run:

```bash
python ../regdef.py show tmc5041.regdef.json
```

We can generate the code using:

```bash
python ../regdef.py code tmc5041.regdef.json > tmc5041_regdef.gen.hpp
python ../regdef.py code -C -p TMC5041_ tmc5041.regdef.json > tmc5041_regdef.gen.h
```

The corresponding generated C code can look like this:

```c
#define TMC5041_X_COMPARE_ADDRESS   (0x05)
#define TMC5041_X_COMPARE_N_BITS    (32)
#define TMC5041_X_COMPARE_RAW(reg)   ((reg.x_compare << 0U))
#define TMC5041_X_COMPARE_FROM_RAW(raw) ((TMC5041_X_COMPARE) { .x_compare = ((raw) & (0b11111111111111111111111111111111U << 0U)) >> 0U })
typedef struct TMC5041_X_COMPARE {
    uint32_t x_compare:32;
} TMC5041_X_COMPARE;

#define TMC5041_IHOLD_IRUN_ADDRESS_0   (0x30)
#define TMC5041_IHOLD_IRUN_ADDRESS_1   (0x50)
#define TMC5041_IHOLD_IRUN_N_BITS    (20)
#define TMC5041_IHOLD_IRUN_RAW(reg)   ((reg.ihold << 0U) | (reg.irun << 8U) | (reg.iholddelay << 16U))
#define TMC5041_IHOLD_IRUN_FROM_RAW(raw) ((TMC5041_IHOLD_IRUN) { .ihold = ((raw) & (0b11111U << 0U)) >> 0U, .irun = ((raw) & (0b11111U << 8U)) >> 8U, .iholddelay = ((raw) & (0b1111U << 16U)) >> 16U })
typedef struct TMC5041_IHOLD_IRUN {
    uint32_t ihold:5;
    uint32_t :3;
    uint32_t irun:5;
    uint32_t :3;
    uint32_t iholddelay:4;
} TMC5041_IHOLD_IRUN;

#define TMC5041_SW_MODE_ADDRESS_0   (0x34)
#define TMC5041_SW_MODE_ADDRESS_1   (0x54)
#define TMC5041_SW_MODE_N_BITS    (12)
#define TMC5041_SW_MODE_RAW(reg)   ((reg.stop_l_enable << 0U) | (reg.stop_r_enable << 1U) | (reg.pol_stop_l << 2U) | (reg.pol_stop_r << 3U) | (reg.swap_lr << 4U) | (reg.latch_l_active << 5U) | (reg.latch_l_inactive << 6U) | (reg.latch_r_active << 7U) | (reg.latch_r_inactive << 8U) | (reg.sg_stop << 10U) | (reg.en_softstop << 11U))
#define TMC5041_SW_MODE_FROM_RAW(raw) ((TMC5041_SW_MODE) { .stop_l_enable = ((raw) & (0b1U << 0U)) >> 0U, .stop_r_enable = ((raw) & (0b1U << 1U)) >> 1U, .pol_stop_l = ((raw) & (0b1U << 2U)) >> 2U, .pol_stop_r = ((raw) & (0b1U << 3U)) >> 3U, .swap_lr = ((raw) & (0b1U << 4U)) >> 4U, .latch_l_active = ((raw) & (0b1U << 5U)) >> 5U, .latch_l_inactive = ((raw) & (0b1U << 6U)) >> 6U, .latch_r_active = ((raw) & (0b1U << 7U)) >> 7U, .latch_r_inactive = ((raw) & (0b1U << 8U)) >> 8U, .sg_stop = ((raw) & (0b1U << 10U)) >> 10U, .en_softstop = ((raw) & (0b1U << 11U)) >> 11U })
typedef struct TMC5041_SW_MODE {
    uint32_t stop_l_enable:1;
    uint32_t stop_r_enable:1;
    uint32_t pol_stop_l:1;
    uint32_t pol_stop_r:1;
    uint32_t swap_lr:1;
    uint32_t latch_l_active:1;
    uint32_t latch_l_inactive:1;
    uint32_t latch_r_active:1;
    uint32_t latch_r_inactive:1;
    uint32_t :1;
    uint32_t sg_stop:1;
    uint32_t en_softstop:1;
} TMC5041_SW_MODE;
```

or for C++:

```cpp
struct X_COMPARE {
    static constexpr uint8_t address = 0x05;
    static constexpr size_t n_bits = 32;

    inline uint32_t raw() {
        return (x_compare << 0U);
    }

    static X_COMPARE from_raw(uint32_t raw) {
        return {
            .x_compare = ((raw) & (0b11111111111111111111111111111111U << 0U)) >> 0U
        };
    }
    uint32_t x_compare:32;
};

struct IHOLD_IRUN {
    static constexpr uint8_t address[2] = {0x30, 0x50};
    static constexpr size_t n_bits = 20;

    inline uint32_t raw() {
        return (ihold << 0U) | (irun << 8U) | (iholddelay << 16U);
    }

    static IHOLD_IRUN from_raw(uint32_t raw) {
        return {
            .ihold = ((raw) & (0b11111U << 0U)) >> 0U,
            .irun = ((raw) & (0b11111U << 8U)) >> 8U,
            .iholddelay = ((raw) & (0b1111U << 16U)) >> 16U
        };
    }
    uint32_t ihold:5;
    uint32_t :3;
    uint32_t irun:5;
    uint32_t :3;
    uint32_t iholddelay:4;
};

struct SW_MODE {
    static constexpr uint8_t address[2] = {0x34, 0x54};
    static constexpr size_t n_bits = 12;

    inline uint32_t raw() {
        return (stop_l_enable << 0U) | (stop_r_enable << 1U) | (pol_stop_l << 2U) | (pol_stop_r << 3U) | (swap_lr << 4U) | (latch_l_active << 5U) | (latch_l_inactive << 6U) | (latch_r_active << 7U) | (latch_r_inactive << 8U) | (sg_stop << 10U) | (en_softstop << 11U);
    }

    static SW_MODE from_raw(uint32_t raw) {
        return {
            .stop_l_enable = ((raw) & (0b1U << 0U)) >> 0U,
            .stop_r_enable = ((raw) & (0b1U << 1U)) >> 1U,
            .pol_stop_l = ((raw) & (0b1U << 2U)) >> 2U,
            .pol_stop_r = ((raw) & (0b1U << 3U)) >> 3U,
            .swap_lr = ((raw) & (0b1U << 4U)) >> 4U,
            .latch_l_active = ((raw) & (0b1U << 5U)) >> 5U,
            .latch_l_inactive = ((raw) & (0b1U << 6U)) >> 6U,
            .latch_r_active = ((raw) & (0b1U << 7U)) >> 7U,
            .latch_r_inactive = ((raw) & (0b1U << 8U)) >> 8U,
            .sg_stop = ((raw) & (0b1U << 10U)) >> 10U,
            .en_softstop = ((raw) & (0b1U << 11U)) >> 11U
        };
    }

    uint32_t stop_l_enable:1;
    uint32_t stop_r_enable:1;
    uint32_t pol_stop_l:1;
    uint32_t pol_stop_r:1;
    uint32_t swap_lr:1;
    uint32_t latch_l_active:1;
    uint32_t latch_l_inactive:1;
    uint32_t latch_r_active:1;
    uint32_t latch_r_inactive:1;
    uint32_t :1;
    uint32_t sg_stop:1;
    uint32_t en_softstop:1;
};
```

## Minimal API usage example

This is a minimal demonstration of how these structures could be used. This is in C++, but for C it is almost the same.

```cpp
// define the register value
// this initialization part requires C++20, but of course it could be omitted
SW_MODE reg = {
    .stop_l_enable = 1,
    .stop_r_enable = 1,
    .latch_l_active = 1,
    .latch_r_active = 1,
    .en_softstop = 1,
};

// convert it to raw register value
uint32_t val = reg.raw();

// avoid problems with endianness by converting to network order
uint32_t val_big_endian = htonl(val);
uint8_t *bytes = (uint8_t *) val_big_endian;

// prepare SPI message
uint8_t address = reg.address[0];
uint8_t buf[] = { address, bytes[0], bytes[1], bytes[2], bytes[3] };

// send the message
spi_send(buf, sizeof(buf));

// for reading we do similar...
// assuming we've got register value in uint32_t and know which register it is
uint32_t val_received = get_raw_received_value();

// convert to our structure
auto reg_received = SW_MODE::from_raw(val_received);

// and use it...
if (reg_received.stop_l_enable && reg_received.stop_r_enable) {
    // ...
}
```

