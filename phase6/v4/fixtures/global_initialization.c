int global = 2;
int broken(void)
{
    return missing_identifier;
}
int independent(void)
{
    return global;
}
