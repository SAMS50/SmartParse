int f(volatile int *p) { if (*p < 5 && *p > 10) return 1; return 0; }
