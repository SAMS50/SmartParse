#include <stdlib.h>
_Static_assert(sizeof(short)>1,"requires multi-byte short");
int store_cell(void) {
 short *cell=malloc(1);
 if(!cell) return 0;
 *cell=101;
 int value=*cell;
 free(cell);
 return value;
}
