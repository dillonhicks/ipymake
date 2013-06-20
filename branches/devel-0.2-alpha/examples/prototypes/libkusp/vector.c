#include <vector.h>
#include <kusp_common.h>

#include <string.h>
#include <stdlib.h>

/**
 * This function inserts an element into a vector. A vector is an array
 * of pointers, and an integer indicating its size. If the array is not
 * currently large enough to insert the item at the requested index, its
 * size will be doubled until it is.
 *
 * @param[in/out] arrayptr pointer to an array of pointers.
 * @param[in/out] sizeptr  pointer to integer indicating current size of array
 * @param item	item to insert into vector
 * @param index location in vector to place item
 * @retval 0 Success
 * @retval -1 Failed to allocate memory
 */
int vector_insert(void ***arrayptr, int *sizeptr, void *item, int index)
{
	// make the code more readable
	void **array, **newarray, **oldarray;
	array = oldarray = *arrayptr;
	int size = *sizeptr;
	int oldsize = *sizeptr;

	if (index < size) {
		array[index] = item;
		return 0;
	}

	while (index >= size) {
		size = size * 2;
	}
	newarray = malloc(sizeof(void*) * size);
	if (!newarray) {
		eprintf("Memory allocation failed when trying to expand array %p\n",
				arrayptr);
		return -1;
	}

	memset(newarray, 0, sizeof(void*) * size);
	memcpy(newarray, oldarray, sizeof(void*) * oldsize);

	free(array);
	*arrayptr = newarray;
	*sizeptr = size;

	newarray[index] = item;
	return 0;
}


