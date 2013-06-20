#include <linux/kernel.h>
#include <linux/proc_fs.h>
#include <linux/string.h>
#include "dski_common.h"

#define PROCFS_MAX_SIZE		1024

/**
 * Proc file system interface used by the system Monitor active filter to create, read and write a
 * proc file. Can also be used by other components if required. I have made it generic as much as possible.
 *
 * Author : Bala Sridhar
 */

/**
 * Structure to the proc file that is created in the /proc fs
 */
struct proc_dir_entry *our_proc_file;

/**
 *  The size of the buffer
 */ 
static unsigned long procfs_buffer_size = 0;

/*
 * procfs buffer that will hold the information required.
 */
static char procfs_buffer[PROCFS_MAX_SIZE];

/** 
 * This function is called then the /proc file is read from the user side.
 */
int procfile_read(char *buffer,char **buffer_location,off_t offset, int buffer_length, int *eof, void *data)
{
	int ret;
	if (offset > 0) {
	/* we have finished to read, return 0 */
		ret  = 0;
	} else {
	/* fill the buffer, return the buffer size */
		ret = sprintf(buffer, procfs_buffer);
	}
	return ret;
}

/**
 * This function is used to reset the buffer once the kernel gets information from the user side that it has read all the information.
 */
int reset_procfs_buffer(){

	if (memset(procfs_buffer,'\0',PROCFS_MAX_SIZE)){
		printk("Buffer reset didn't work.......%s\n", procfs_buffer);
		return -EFAULT;
	}

	//printk("The buffer is reset  %s", procfs_buffer);
	return 0;
}

/**
 * This function is called with the /proc file is written to from the user side.
 */
int procfile_write(struct file *file, const char *buffer, unsigned long count,
				   void *data)
{
	/* get buffer size */
	procfs_buffer_size = count;
	if (procfs_buffer_size > PROCFS_MAX_SIZE ) {
		procfs_buffer_size = PROCFS_MAX_SIZE;
	}
	
	/* write data to the buffer */
	if ( copy_from_user(procfs_buffer, buffer, procfs_buffer_size) ) {
		return -EFAULT;
	}

	// If the information written to the procfs file from the use side is 'Read the Information',
	// then we remove the old contents off the procfs file
	
	if (strstr(procfs_buffer,"Read the Information\n")){
		//printk("User side thread has read the information required\n");
		reset_procfs_buffer();
	}

	//printk("written to file without problems\n");
	return procfs_buffer_size;
}

/*
 * Used for creating a proc file in the proc file system.
 */
int create_proc_file(char *name){
	
	our_proc_file = create_proc_entry(name,S_IRUGO | S_IWUGO, NULL);

	if(our_proc_file == NULL){
		remove_proc_entry(name, &proc_root);
		printk("Cannot create the proc file....\n");
		return -ENOMEM;
	}
	
	our_proc_file->read_proc  = procfile_read;
	our_proc_file->write_proc = procfile_write;
	our_proc_file->uid =0;
	our_proc_file->gid =0;

	printk("proc file created %s\n",name);
	return 0;

}

/*
 * Used by the kernel side components to write to the proc file.
 */
int write_to_procfile(int pid){

	char buf[10];
	char *tempBuf;
	// first write the pid to a buffer
	sprintf(buf,"%d\n", pid);

	// concatenate the buffer created in the previous step to the current contents of the procfs file
	// and store it in a temp buffer
	tempBuf = strncat(procfs_buffer,buf,sizeof(buf));

	if(sizeof(tempBuf)>1000){
		printk("Buffer size greater than 1000 bytes\n");
		return -EFAULT;
	}

	// we are sure that the size is less than 1000 bytes so we are copying the temp buffer to the procfs file 
	if (memcpy(procfs_buffer,tempBuf,sizeof(tempBuf))==0){
		printk("Memory copy didn't work....\n");
		return -EFAULT;
	}

	//printk("written to proc file %s", procfs_buffer);
	return 0;
}

/* 
 * Used for removing the proc file from proc file system, once it has finished its requirement.
 */
int remove_proc_file(char *name){

	remove_proc_entry(name, &proc_root);
	printk("Proc file removed %s\n", name);
	return 0;
}

