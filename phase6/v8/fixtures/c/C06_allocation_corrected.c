#include <stdlib.h>
int store_cell(void) {
 short *cell=malloc(sizeof *cell);
 if(!cell) return 0;
 *cell=101;
 int value=*cell;
 free(cell);
 return value;
}
