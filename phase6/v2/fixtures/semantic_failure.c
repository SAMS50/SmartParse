int identity(int value) { return value; }
int broken_call(void) { return identity(1, 2); }
int otherwise_valid(void) { return 2; }
