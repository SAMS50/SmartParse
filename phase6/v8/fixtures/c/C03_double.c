#include <stdlib.h>
void release_pair(void) {
 char *block=malloc(24);
 char *saved=block;
 free(block);
 free(saved);
}
