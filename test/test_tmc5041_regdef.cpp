#include "unity.h"
#include "tmc5041_regdef.hpp"

void test_GCONF_address()
{
    TEST_ASSERT_EQUAL_HEX8(0x00u, tmc5041::GCONF::address);
}

void test_GCONF_from_raw()
{
    auto reg = tmc5041::GCONF::from_raw(0x00000008u);
    TEST_ASSERT_EQUAL_HEX32(0x00000008u, reg.raw());
    TEST_ASSERT_EQUAL_INT(1, reg.poscmp_enable);
    TEST_ASSERT_EQUAL_INT(0, reg.test_mode);
    TEST_ASSERT_EQUAL_INT(0, reg.shaft1);
    TEST_ASSERT_EQUAL_INT(0, reg.shaft2);
    TEST_ASSERT_EQUAL_INT(0, reg.lock_gconf);
}

void test_GCONF_to_raw()
{
    tmc5041::GCONF reg = {
        .poscmp_enable = 0,
        .test_mode = 1,
        .shaft1 = 0,
        .shaft2 = 1,
        .lock_gconf = 1,
    };
    TEST_ASSERT_EQUAL_HEX32((1 << 7) | (1 << 9) | (1 << 10), reg.raw());
}


void test_GSTAT_address()
{
    TEST_ASSERT_EQUAL_HEX8(0x01u, tmc5041::GSTAT::address);
    TEST_ASSERT_EQUAL_INT(4, tmc5041::GSTAT::n_bits);
}

void test_GSTAT_from_raw()
{
    auto reg = tmc5041::GSTAT::from_raw((1 << 0) | (1 << 3));
    TEST_ASSERT_EQUAL_HEX32((1 << 0) | (1 << 3), reg.raw());
    TEST_ASSERT_EQUAL_INT(1, reg.reset);
    TEST_ASSERT_EQUAL_INT(0, reg.drv_err1);
    TEST_ASSERT_EQUAL_INT(0, reg.drv_err2);
    TEST_ASSERT_EQUAL_INT(1, reg.uv_cp);
}

void test_GSTAT_to_raw()
{
    tmc5041::GSTAT reg = {
        .reset = 0,
        .drv_err1 = 1,
        .drv_err2 = 1,
        .uv_cp = 0,
    };
    TEST_ASSERT_EQUAL_HEX32((1 << 1) | (1 << 2), reg.raw());
}


// some examples from TMC5041 datasheet (Getting Started, p.72, ignore first address byte)
void test_datasheet_examples()
{
    using namespace tmc5041;

    GCONF gconf           = { .poscmp_enable = 1 };
    CHOPCONF chopconf     = { .toff = 5, .hstrt = 4, .hend = 1, .chm = 0, .tbl = 2 };
    IHOLD_IRUN ihold_irun = { .ihold = 5, .irun = 31, .iholddelay = 1 };
    TZEROWAIT tzerowait   = { .tzerowait = 10'000 };
    PWMCONF pwmconf       = { .pwm_ampl = 200, .pwm_grad = 1, .pwm_freq = 0b00, .pwm_autoscale = 1 };
    VHIGH vhigh           = { .vhigh = 400'000 };
    VCOOLTHRS vcoolthrs   = { .vcoolthrs = 30'000 };
    AMAX amax             = { .amax = 5'000 };
    VMAX vmax             = { .vmax = 20'000 };
    RAMPMODE rampmode     = { .rampmode = 1 };

    TEST_ASSERT_EQUAL_HEX32(0x00000008u, gconf.raw());
    TEST_ASSERT_EQUAL_HEX32(0x000100c5u, chopconf.raw());
    TEST_ASSERT_EQUAL_HEX32(0x00011f05u, ihold_irun.raw());
    TEST_ASSERT_EQUAL_HEX32(0x00002710u, tzerowait.raw());
    TEST_ASSERT_EQUAL_HEX32(0x000401c8u, pwmconf.raw());
    TEST_ASSERT_EQUAL_HEX32(0x00061a80u, vhigh.raw());
    TEST_ASSERT_EQUAL_HEX32(0x00007530u, vcoolthrs.raw());
    TEST_ASSERT_EQUAL_HEX32(0x00001388u, amax.raw());
    TEST_ASSERT_EQUAL_HEX32(0x00004e20u, vmax.raw());
    TEST_ASSERT_EQUAL_HEX32(0x00000001u, rampmode.raw());

    // DO NOT do something like this:
    // (this is undefined behaviour, it may work or may not (really sometimes it does NOT work))
    // auto gconf_from_raw = GCONF::from_raw(0x00000008u);
    // TEST_ASSERT_TRUE(*(uint32_t *) &gconf_from_raw == *(uint32_t *) &gconf);

    TEST_ASSERT_EQUAL_HEX32(GCONF     ::from_raw(0x00000008u).raw(), gconf.raw());
    TEST_ASSERT_EQUAL_HEX32(CHOPCONF  ::from_raw(0x000100c5u).raw(), chopconf.raw());
    TEST_ASSERT_EQUAL_HEX32(IHOLD_IRUN::from_raw(0x00011f05u).raw(), ihold_irun.raw());
    TEST_ASSERT_EQUAL_HEX32(TZEROWAIT ::from_raw(0x00002710u).raw(), tzerowait.raw());
    TEST_ASSERT_EQUAL_HEX32(PWMCONF   ::from_raw(0x000401c8u).raw(), pwmconf.raw());
    TEST_ASSERT_EQUAL_HEX32(VHIGH     ::from_raw(0x00061a80u).raw(), vhigh.raw());
    TEST_ASSERT_EQUAL_HEX32(VCOOLTHRS ::from_raw(0x00007530u).raw(), vcoolthrs.raw());
    TEST_ASSERT_EQUAL_HEX32(AMAX      ::from_raw(0x00001388u).raw(), amax.raw());
    TEST_ASSERT_EQUAL_HEX32(VMAX      ::from_raw(0x00004e20u).raw(), vmax.raw());
    TEST_ASSERT_EQUAL_HEX32(RAMPMODE  ::from_raw(0x00000001u).raw(), rampmode.raw());
}


int main(void)
{
    UNITY_BEGIN();
    RUN_TEST(test_GCONF_address);
    RUN_TEST(test_GCONF_from_raw);
    RUN_TEST(test_GCONF_to_raw);
    RUN_TEST(test_GSTAT_address);
    RUN_TEST(test_GSTAT_from_raw);
    RUN_TEST(test_GSTAT_to_raw);
    RUN_TEST(test_datasheet_examples);
    return UNITY_END();
}
