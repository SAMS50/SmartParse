#include <stdlib.h>
void release_pair(void) {
 char *block=malloc(24);
 free(block);
}
