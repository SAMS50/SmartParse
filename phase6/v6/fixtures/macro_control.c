#define LOW(x) ((x)<5)
int f(int x) { if (LOW(x) && x > 10) return 1; return 0; }
