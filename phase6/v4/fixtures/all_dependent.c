int broken(void)
{
    return missing_identifier;
}
int caller(void)
{
    return broken();
}
