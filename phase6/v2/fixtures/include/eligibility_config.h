#ifndef ELIGIBILITY_CONFIG_H
#define ELIGIBILITY_CONFIG_H
typedef struct { const char *label; int values[2]; } EligibilityItem;
static inline int header_value(void) { return 1; }
#endif
