int read_probe(int bias) {
 int sample=11;
 int *probe=&sample;
 return bias + *probe;
}
