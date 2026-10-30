int broken(void)
{
    return missing_identifier;
}
int caller(void)
{
    return broken();
}
int independent(void)
{
    int *pointer = 0;
    return *pointer;
}
