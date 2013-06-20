/**
 * @file
 */

#ifndef __NS_PARSER_V1_H__
#define __NS_PARSER_V1_H__

#include <hashtable.h>
#include <configfile.h>
#include <linkedlist.h>
#include <stdio.h>

/* FIXME:
   write helper function to handle family
   and entity assignments.

   put keys we know about in header instead of
   hard-coding them in the yacc file. datastructure
   in header file and C files.

*/

/* a tuple-like structure to hold an assignment */

#define MAX_FUNC_LEN 48
#define MAX_NAME_LEN 48
#define MAX_DESC_LEN 160

typedef union nsvalue_u {
	char *string;
	int32_t integer;
} nsvalue_t;

typedef struct assignment_s {
	char *key;
	nsvalue_t nsvalue;
} assignment_t;

/* Be sure to update the format strings in
 * datastreams/postprocess2/event_data.py if you change
 * any of these datastructures */

struct entity_spec {
	char name[MAX_NAME_LEN + 1];
	char shortdesc[MAX_DESC_LEN + 1];
	char print_func[MAX_FUNC_LEN + 1];
	char kernel_func[MAX_FUNC_LEN + 1];
	// unused
	char timestd[MAX_NAME_LEN + 1];
	int32_t id;
	int32_t type;

	/* histogram parameters */
	struct set_hist_params *hist_params;
	struct family_spec *fam;

};

struct family_spec {
	char name[MAX_NAME_LEN + 1];
	char shortdesc[MAX_DESC_LEN + 1];
	int32_t id;
	int32_t count[5];
	int32_t num_entities;
	struct hashtable *byname;
	struct hashtable *bynum[5];
};

struct namespace_spec {
	int32_t highest;
	int32_t num_families;
	int32_t instance_id;
	struct hashtable *byname;
	struct hashtable *bynum;
};

/* NAMESPACE UTILITY FUNCTIONS */
struct entity_spec *get_entity_byname(struct namespace_spec *ns, char *family,
				      char *entity);
struct entity_spec *get_entity_bynum(struct namespace_spec *ns, int32_t family,
				     int32_t type, int32_t entity);
struct family_spec *get_family_byname(struct namespace_spec *ns, char *family);
struct family_spec *get_family_bynum(struct namespace_spec *ns, int32_t family);

struct family_spec *create_family(void);
struct namespace_spec *create_namespace(void);
struct entity_spec *create_entity(void);

void add_family(struct namespace_spec *ns, struct family_spec *fam);
void add_entity(struct family_spec *fam, struct entity_spec *ent);

void prettyprint_ns(struct namespace_spec *ns);
void prettyprint_fam(struct family_spec *fam);
void prettyprint_ent(struct entity_spec *ent);

// namespace retrieval functions
struct namespace_spec *parse_namespace_file(FILE * infile);
struct namespace_spec *parse_namespace_filename(char *filename);

struct namespace_spec *construct_namespace(hashtable_t * nscfg);
int verify_namespace_config(hashtable_t * nscfg);

// retrieves the admin namespace
struct namespace_spec *get_admin_ns(void);

// returns the union of the listed namespaces, as well as admin namespace
// the list should be a configfile list of strings.
// returns NULL if any merges fail or filenames are invalid
struct namespace_spec *process_namespaces(list_t * namespace_filenames);
int merge_namespaces(struct namespace_spec *target_ns,
		     struct namespace_spec *source_ns);

void free_namespace(struct namespace_spec *ns);
void free_family(struct family_spec *fam);

/* enable file processing */
list_t *get_enabled_entities(hashtable_t * enabled, struct namespace_spec *ns);

void serialize_namespace(void **data, unsigned long *nssize,
		struct namespace_spec *ns);
struct namespace_spec *deserialize_namespace(void *cdata,
		unsigned long csize);

/* stuff that lex/yacc needs */
extern FILE *nsparserin;
void nsparsererror(char *s);
int nsparserlex(void);

#endif				/* __NS_PARSER_V1_H__ */
