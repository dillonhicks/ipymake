#include <configfile.h>
#include <linkedlist.h>
#include <hashtable.h>


/**
 * All data placed in configfile container datastructures
 * is encapsulated in these value_t structures. This allows
 * for a form of introspection; you do not need to know in
 * advance what the type of the stored data is.
 *
 * the unhash_*, unlist_*, and encap_* family of functions
 * perform operations on these value_t structures so that
 * you won't have to deal with them directly.
 *
 * THIS DEFINITION IS HERE DELIBERATELY. value_t is an opaque
 * type and should never be used directly.
 */
struct value_s {
	/**
	 * This field notes the data type of the stored
	 * inside this value_t.
	 */
	valuetype_t type;

	/** pointer to top-level hashtable, for
	 * looking up references */
	hashtable_t *toplevel;

	/** line number this appeared on in config file **/
	int lineno;

	/** list of pointers to specification hashtables
	 * this item has been checked against. we keep track
	 * of these to prevent an infinite loop with
	 * recursive references */
	list_t *context;
	/**
	 * The actual data is stored here.
	 */
	union {
		double d;
		hashtable_t *h;
		int i;
		list_t *l;
		char *s;
		invocation_t *v;
		long long g;
	} value;
};



struct vexcept {
	char *message;
	struct vexcept *next;
};


