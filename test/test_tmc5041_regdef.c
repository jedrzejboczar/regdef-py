#include "unity.h"
#include "tmc5041_regdef.h"

void test_GCONF_address(void)
{
    TEST_ASSERT_EQUAL_HEX8(0x00u, TMC5041_GCONF_ADDRESS);
}

void test_GCONF_from_raw(void)
{
    TMC5041_GCONF reg = TMC5041_GCONF_FROM_RAW(0x00000008u);
    TEST_ASSERT_EQUAL_HEX32(0x00000008u, TMC5041_GCONF_RAW(reg));
    TEST_ASSERT_EQUAL_INT(1, reg.poscmp_enable);
    TEST_ASSERT_EQUAL_INT(0, reg.test_mode);
    TEST_ASSERT_EQUAL_INT(0, reg.shaft1);
    TEST_ASSERT_EQUAL_INT(0, reg.shaft2);
    TEST_ASSERT_EQUAL_INT(0, reg.lock_gconf);
}

void test_GCONF_to_raw(void)
{
    TMC5041_GCONF reg = {
        .poscmp_enable = 0,
        .test_mode = 1,
        .shaft1 = 0,
        .shaft2 = 1,
        .lock_gconf = 1,
    };
    TEST_ASSERT_EQUAL_HEX32((1 << 7) | (1 << 9) | (1 << 10), TMC5041_GCONF_RAW(reg));
}


void test_GSTAT_address(void)
{
    TEST_ASSERT_EQUAL_HEX8(0x01u, TMC5041_GSTAT_ADDRESS);
    TEST_ASSERT_EQUAL_INT(4, TMC5041_GSTAT_N_BITS);
}

void test_GSTAT_from_raw(void)
{
    TMC5041_GSTAT reg = TMC5041_GSTAT_FROM_RAW((1 << 0) | (1 << 3));
    TEST_ASSERT_EQUAL_HEX32((1 << 0) | (1 << 3), TMC5041_GSTAT_RAW(reg));
    TEST_ASSERT_EQUAL_INT(1, reg.reset);
    TEST_ASSERT_EQUAL_INT(0, reg.drv_err1);
    TEST_ASSERT_EQUAL_INT(0, reg.drv_err2);
    TEST_ASSERT_EQUAL_INT(1, reg.uv_cp);
}

void test_GSTAT_to_raw(void)
{
    TMC5041_GSTAT reg = {
        .reset = 0,
        .drv_err1 = 1,
        .drv_err2 = 1,
        .uv_cp = 0,
    };
    TEST_ASSERT_EQUAL_HEX32((1 << 1) | (1 << 2), TMC5041_GSTAT_RAW(reg));
}


// some examples from TMC5041 datasheet (Getting Started, p.72, ignore first address byte)
void test_datasheet_examples(void)
{
    TMC5041_GCONF gconf           = { .poscmp_enable = 1 };
    TMC5041_CHOPCONF chopconf     = { .toff = 5, .hstrt = 4, .hend = 1, .chm = 0, .tbl = 2 };
    TMC5041_IHOLD_IRUN ihold_irun = { .ihold = 5, .irun = 31, .iholddelay = 1 };
    TMC5041_TZEROWAIT tzerowait   = { .tzerowait = 10000 };
    TMC5041_PWMCONF pwmconf       = { .pwm_ampl = 200, .pwm_grad = 1, .pwm_freq = 0b00, .pwm_autoscale = 1 };
    TMC5041_VHIGH vhigh           = { .vhigh = 400000 };
    TMC5041_VCOOLTHRS vcoolthrs   = { .vcoolthrs = 30000 };
    TMC5041_AMAX amax             = { .amax = 5000 };
    TMC5041_VMAX vmax             = { .vmax = 20000 };
    TMC5041_RAMPMODE rampmode     = { .rampmode = 1 };

    TEST_ASSERT_EQUAL_HEX32(0x00000008u, TMC5041_GCONF_RAW(gconf));
    TEST_ASSERT_EQUAL_HEX32(0x000100c5u, TMC5041_CHOPCONF_RAW(chopconf));
    TEST_ASSERT_EQUAL_HEX32(0x00011f05u, TMC5041_IHOLD_IRUN_RAW(ihold_irun));
    TEST_ASSERT_EQUAL_HEX32(0x00002710u, TMC5041_TZEROWAIT_RAW(tzerowait));
    TEST_ASSERT_EQUAL_HEX32(0x000401c8u, TMC5041_PWMCONF_RAW(pwmconf));
    TEST_ASSERT_EQUAL_HEX32(0x00061a80u, TMC5041_VHIGH_RAW(vhigh));
    TEST_ASSERT_EQUAL_HEX32(0x00007530u, TMC5041_VCOOLTHRS_RAW(vcoolthrs));
    TEST_ASSERT_EQUAL_HEX32(0x00001388u, TMC5041_AMAX_RAW(amax));
    TEST_ASSERT_EQUAL_HEX32(0x00004e20u, TMC5041_VMAX_RAW(vmax));
    TEST_ASSERT_EQUAL_HEX32(0x00000001u, TMC5041_RAMPMODE_RAW(rampmode));

    // DO NOT do something like this:
    // (this is undefined behaviour, it may work or may not (really sometimes it does NOT work))
    // TMC5041_GCONF gconf_from_raw = TMC5041_GCONF_FROM_RAW(0x00000008u);
    // TEST_ASSERT_TRUE(*(uint32_t *) &gconf_from_raw == *(uint32_t *) &gconf);

    TEST_ASSERT_EQUAL_HEX32(TMC5041_GCONF_RAW(     TMC5041_GCONF_FROM_RAW     (0x00000008u)), TMC5041_GCONF_RAW(gconf));
    TEST_ASSERT_EQUAL_HEX32(TMC5041_CHOPCONF_RAW(  TMC5041_CHOPCONF_FROM_RAW  (0x000100c5u)), TMC5041_CHOPCONF_RAW(chopconf));
    TEST_ASSERT_EQUAL_HEX32(TMC5041_IHOLD_IRUN_RAW(TMC5041_IHOLD_IRUN_FROM_RAW(0x00011f05u)), TMC5041_IHOLD_IRUN_RAW(ihold_irun));
    TEST_ASSERT_EQUAL_HEX32(TMC5041_TZEROWAIT_RAW( TMC5041_TZEROWAIT_FROM_RAW (0x00002710u)), TMC5041_TZEROWAIT_RAW(tzerowait));
    TEST_ASSERT_EQUAL_HEX32(TMC5041_PWMCONF_RAW(   TMC5041_PWMCONF_FROM_RAW   (0x000401c8u)), TMC5041_PWMCONF_RAW(pwmconf));
    TEST_ASSERT_EQUAL_HEX32(TMC5041_VHIGH_RAW(     TMC5041_VHIGH_FROM_RAW     (0x00061a80u)), TMC5041_VHIGH_RAW(vhigh));
    TEST_ASSERT_EQUAL_HEX32(TMC5041_VCOOLTHRS_RAW( TMC5041_VCOOLTHRS_FROM_RAW (0x00007530u)), TMC5041_VCOOLTHRS_RAW(vcoolthrs));
    TEST_ASSERT_EQUAL_HEX32(TMC5041_AMAX_RAW(      TMC5041_AMAX_FROM_RAW      (0x00001388u)), TMC5041_AMAX_RAW(amax));
    TEST_ASSERT_EQUAL_HEX32(TMC5041_VMAX_RAW(      TMC5041_VMAX_FROM_RAW      (0x00004e20u)), TMC5041_VMAX_RAW(vmax));
    TEST_ASSERT_EQUAL_HEX32(TMC5041_RAMPMODE_RAW(  TMC5041_RAMPMODE_FROM_RAW  (0x00000001u)), TMC5041_RAMPMODE_RAW(rampmode));
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

