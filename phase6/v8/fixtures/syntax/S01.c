int orbit(int n) {
 int total=0;
 while(n>0) { total=total+n; n=n-1; }
 return total;
}
int sentinel=9;
