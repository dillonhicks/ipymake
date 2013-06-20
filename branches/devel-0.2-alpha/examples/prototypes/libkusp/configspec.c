#include <configfile.h>
#include <configspec.h>

// --- Globals ---

/// Items in this list will be mapped to the variable array
list_t *vars;

/// array of pointers to variables populated by the configuration file
void **varray;

hashtable_t *toplevel;


/* built-in types we know about:
 *
 * dictionary
 *    key,value pairs must satisfy definitions in dictionary_keys
 *    any remaining items must correspond to dictionary_members
 * list
 *    list_members
 * string
 * int
 * double
 * invocation
 *    invocation_keys
 *    arbitrary members not allowed
 * boolean
 * long
 */


int string_to_valuetype(char *s, valuetype_t *v) {
	if (strcmp(s, "dictionary") == 0) {
		*v = DICTTYPE;
		return 0;
	}
	if (strcmp(s, "list") == 0) {
		*v = LISTTYPE;
		return 0;
	}
	if (strcmp(s, "string") == 0) {
		*v = STRINGTYPE;
		return 0;
	}
	if (strcmp(s, "invocation") == 0) {
		*v = INVOTYPE;
		return 0;
	}
	if (strcmp(s, "double") == 0) {
		*v = DOUBLETYPE;
		return 0;
	}
	if (strcmp(s, "boolean") == 0) {
		*v = BOOLTYPE;
		return 0;
	}
	if (strcmp(s, "long") == 0) {
		*v = LONGTYPE;
		return 0;
	}
	if (strcmp(s, "int") == 0) {
		*v = INTTYPE;
		return 0;
	}
	return -1;
}



static int process_block(value_t *config, hashtable_t *spec, char *context)
{
	// the type field specifies which of the primitive datatypes config
	// must be. once we determine that config is of legal type, we call
	// a type-specific function for further processing.

	list_t *typelist;
	if (unhash_list(spec, "type"


	valuetype_t ctype = config->type;



	...

}

static int process_dictionary(valye
