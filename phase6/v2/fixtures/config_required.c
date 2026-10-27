#ifndef ENABLE_FEATURE
#error ENABLE_FEATURE is required for this configuration
#endif
int configured(void) { return ENABLE_FEATURE; }
