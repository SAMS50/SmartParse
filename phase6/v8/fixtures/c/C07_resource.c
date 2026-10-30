#include <stdio.h>
void write_record(void) {
 FILE *stream=fopen("m8-record.txt","w");
 if(!stream) return;
 fputs("record",stream);
}
