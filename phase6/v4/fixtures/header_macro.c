#include "header_macro.h"
int broken(void)
{
    return missing_identifier;
}
int independent(void)
{
    int *pointer = VALUE_ZERO;
    return *pointer;
}
