int broken(void)
{
    return missing_identifier;
}
int independent(int (*callback)(void))
{
    return callback();
}
