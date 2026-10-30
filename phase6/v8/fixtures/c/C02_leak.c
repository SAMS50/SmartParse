#include <stdlib.h>
void collect_cells(void) {
 unsigned *cells=calloc(5,sizeof *cells);
 if(!cells) return;
 cells[0]=13;
}
