#define MAKE_FUNCTION(name) int name(void) { return 7; }
MAKE_FUNCTION(generated_function)
int ordinary_function(void) { return generated_function(); }
