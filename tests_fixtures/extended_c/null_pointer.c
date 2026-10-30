/* Independent analyzer fixture; never run by SmartParse. */
int read_null(void) {
    int *pointer = 0;
    return *pointer;
}
