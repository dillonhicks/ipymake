	.file	"ppctsc.c"
	.section	.rodata
.LC0:
	.string	"tsc is %lld\n"
.LC1:
	.string	"%d "
	.text
.globl main
	.type	main, @function
main:
	leal	4(%esp), %ecx
	andl	$-16, %esp
	pushl	-4(%ecx)
	pushl	%ebp
	movl	%esp, %ebp
	pushl	%ebx
	pushl	%ecx
	subl	$288, %esp
	call	TB
	movl	%eax, 4(%esp)
	movl	%edx, 8(%esp)
	movl	$.LC0, (%esp)
	call	printf
	movl	$64, -16(%ebp)
	jmp	.L2
.L3:
	movl	-16(%ebp), %ebx
	call	TBl
	movl	%eax, -272(%ebp,%ebx,4)
.L2:
	subl	$1, -16(%ebp)
	cmpl	$-1, -16(%ebp)
	jne	.L3
	movl	$63, -12(%ebp)
	jmp	.L5
.L6:
	movl	-12(%ebp), %eax
	movl	-272(%ebp,%eax,4), %edx
	movl	-12(%ebp), %eax
	addl	$1, %eax
	movl	-272(%ebp,%eax,4), %eax
	movl	%edx, %ecx
	subl	%eax, %ecx
	movl	%ecx, %eax
	movl	%eax, 4(%esp)
	movl	$.LC1, (%esp)
	call	printf
.L5:
	subl	$1, -12(%ebp)
	cmpl	$-1, -12(%ebp)
	jne	.L6
	movl	$10, (%esp)
	call	putchar
	addl	$288, %esp
	popl	%ecx
	popl	%ebx
	popl	%ebp
	leal	-4(%ecx), %esp
	ret
	.size	main, .-main
	.ident	"GCC: (GNU) 4.1.2 20060928 (prerelease) (Ubuntu 4.1.1-13ubuntu5)"
	.section	.note.GNU-stack,"",@progbits
