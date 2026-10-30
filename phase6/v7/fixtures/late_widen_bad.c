#include <limits.h>
_Static_assert(INT_MAX==2147483647,"32-bit int oracle");
long long probe(void){int a=50000,b=50000;return (long long)(a*b);}
