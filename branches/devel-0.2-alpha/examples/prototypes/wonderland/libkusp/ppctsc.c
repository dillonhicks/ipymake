long long TB(void);
unsigned int TBl(void);
#include <stdio.h>
int main()
{
	printf("tsc is %lld\n", TB());
	unsigned int a[64];
	{
		int j=64; 
		while(j--) 
			a[j]=TBl();
	}
	{int j=63; 
		while(j--) 
			printf("%d ", a[j] - a[j+1]);
	}
	printf("\n");

}
