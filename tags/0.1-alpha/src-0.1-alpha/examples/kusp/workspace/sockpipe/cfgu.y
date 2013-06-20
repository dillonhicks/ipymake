%{
#include <stdlib.h>
#include <stdio.h>
#include <stdarg.h>
#include <string.h>
#include <strings.h>
#include "cfgu.h"
#include "cfgu_y.hpp"

/* Internal error function for the parser and lexer */	
static void _cfgu_error(void* p, const char* fmt, ...) 
{
	struct cfguConfig* config = (struct cfguConfig*)p;
        va_list ap;
	 
	va_start(ap, fmt);
	vsnprintf (config->error, CFGU_MAX_ERROR, fmt, ap);
	va_end(ap);
}

static struct cfguObj* cfgu_new_obj_raw()
{
	struct cfguObj* obj;

	obj = (struct cfguObj*)malloc(sizeof(struct cfguObj));

	if (!obj)
		return NULL;

	obj->var_list = create_list();
	/* 10 = the size of the iitial hash table but it will grow automatically */
	obj->var_hash = create_hashtable(10, hash_string, string_key_equal);
	return obj;
}

struct cfguVal* cfgu_new_obj()
{
	struct cfguObj* obj;
	struct cfguVal* val;

	obj = cfgu_new_obj_raw();

	if (!obj)
		return NULL;

	val = (struct cfguVal*)malloc(sizeof(struct cfguVal));

	if (!val) {
		return NULL;
	}
	
	val->type = CFGU_OBJECT;
	val->value.obj = obj;
	return val;
}
 
struct cfguVal* cfgu_new_list()
{
	struct cfguList* l;
	struct cfguVal* val;

	l = (struct cfguList*)malloc(sizeof(struct cfguList));

	if (!l)
		return NULL;

	val = (struct cfguVal*)malloc(sizeof(struct cfguVal));

	if (!val) {
		return NULL;
	}
	
	val->type = CFGU_LIST;
	val->value.list = l;
	l->value_list = create_list();
	return val;
}

int cfgu_insert_val(struct cfguList* l, struct cfguVal* val)
{
	if (!l || !val)
		return -1;

	list_append(l->value_list, val);

	return 0;
}

int cfgu_insert_var(struct cfguObj* obj, struct cfguVar* var)
{
	if (!obj || !var)
		return -1;

	hashtable_insert(obj->var_hash, var->name, var);
	list_append(obj->var_list, var);

	return 0;
}

static void cfgu_free_val(struct cfguVal* val);

static void cfgu_free_obj(struct cfguObj* obj);

static void cfgu_free_list(struct cfguList* l)
{
	list_t* pos;
	list_t* temp;

	if (!l)
		return;

	list_for_each_safe(pos, temp, l->value_list) {
		struct cfguVal* val = (struct cfguVal*)pos->item;
		cfgu_free_val(val);
	}

	list_free(l->value_list);
	l->value_list = NULL;

	free(l);
}

static void cfgu_free_val(struct cfguVal* val) 
{
	if (!val)
		return;

	if (val->type == CFGU_STRING) {
		free(val->value.str);
		val->value.str = NULL;
	}
	
	if (val->type == CFGU_OBJECT) {
		cfgu_free_obj(val->value.obj);
		val->value.obj = NULL;
	}

	if (val->type == CFGU_LIST) {
		cfgu_free_list(val->value.list);
		val->value.list = NULL;
	}

	free(val);
}

static void cfgu_free_obj(struct cfguObj* obj) 
{
	list_t* pos;
	list_t* temp;

	if (!obj)
		return;

	hashtable_destroy(obj->var_hash, 0);
	obj->var_hash = NULL;

	/* The hash table will free the names of the vars. 
	 */
	list_for_each_safe(pos, temp, obj->var_list) {
		struct cfguVar* var = (struct cfguVar*)pos->item;
		cfgu_free_val(var->val);
		free(var);
	}

	list_free(obj->var_list);
	obj->var_list = NULL;

	free(obj);
}

/* Get more descriptive error messages */
#define YYERROR_VERBOSE 1
  
/* yyparse needs to take a config object as an argument */
#define YYPARSE_PARAM config
#define YYLEX_PARAM ((struct cfguConfig*)config)->scanner, (struct cfguConfig*)config

/* Make the config get passed to the error function */
#define cfgu_error(msg) _cfgu_error(config, msg);

/* Some functions defined by the lexer */
extern int cfgu_lex(YYSTYPE* lval, void* scanner, struct cfguConfig* config);
extern void cfgu_restart(FILE* fp, void* scanner);
extern int cfgu_lex_init(void** scanner);
extern int cfgu_lex_destroy(void* scanner);

/* Check to see if an allocation worked. If it did not
 * then bail out.
 */
#define check_alloc(val, p)						\
	if (! p ) {							\
		yyerror("Out of memory.\n");				\
		YYABORT;						\
	}								\
	val = p;								

%}

%union {
	/* Used to pass the position of single characters */
	struct cfguPos pos;
	struct cfguVar* var;
	struct cfguVal* value;
}

%pure_parser

%token <pos> START_OBJ '{'
%token <pos> START_LIST '['
%token <var> IDENTIFIER "variable name"
%token <value> NUMBER "number"
%token <value> STRING "string"
%token <value> TRUE "true"
%token <value> FALSE "false"

%type <value> value
%type <value> members
%type <value> object
%type <value> list_elements
%type <value> list
%type <var> var
%type <var> start

%%

/* Only occurs at the global level */
start: { YYACCEPT; }
     | var { cfgu_insert_var(((struct cfguConfig*)config)->global, $1); $$ = $1; YYACCEPT; }

var: IDENTIFIER '=' value
     {
	     check_alloc($$, $1);
	     $$->val = $3;
     }

/* Can't compact empty object until the same rule as members
 * because a conflict will be created.
 */
object: '{' '}' { check_alloc($$, cfgu_new_obj()); $$->pos = $1; } 
      | '{' members '}' { $$ = $2; $$->pos = $1; }

members: var 
         {
		 check_alloc($$, cfgu_new_obj());
		 cfgu_insert_var($$->value.obj, $1);
         }
       | members var
         {
		 cfgu_insert_var($1->value.obj, $2);
		 $$ = $1;
         }

/* Can't compact empty list into the same rule as list_elements
 * becuase a conflict will be created.
 */
list: '[' ']' { check_alloc($$, cfgu_new_list()); $$->pos = $1; }
    | '[' list_elements ']' { $$ = $2; $$->pos = $1; }

/* Note: The grammer could work without the ','. */
list_elements: value
               {
		 check_alloc($$, cfgu_new_list());
		 cfgu_insert_val($$->value.list, $1);
               }
             | list_elements value
	       {
		 cfgu_insert_val($1->value.list, $2);
		 $$ = $1;
               }
             | list_elements ',' value
	       {
		 cfgu_insert_val($1->value.list, $3);
		 $$ = $1;
               }

value: list { $$ = $1; }
     | object { $$ = $1; }
     | STRING { check_alloc($$, $1); }
     | NUMBER { check_alloc($$, $1); }
     | TRUE { check_alloc($$, $1); }
     | FALSE { check_alloc($$, $1); }
%%

struct cfguVal* cfgu_find_val(const struct cfguObj* obj, const char* name)
{
	struct cfguVar* var;

	if (!obj)
		return NULL;

	if (!name)
		return NULL;

	var = (struct cfguVar*)hashtable_search(obj->var_hash, (void*)name);

	if (!var)
		return NULL;

	return var->val;
}

double cfgu_get_real(const struct cfguObj* obj, const char* name, double def)
{
	struct cfguVal* val;

	if (obj && name) {
		val = cfgu_find_val(obj, name);
	} else {
		return NULL;
	}

	return cfgu_real(val, def);
}

const char* cfgu_get_str(const struct cfguObj* obj, const char* name)
{
	struct cfguVal* val;

	if (obj && name) {
		val = cfgu_find_val(obj, name);
	} else {
		return NULL;
	}

	return cfgu_str(val);
}

char cfgu_get_true(const struct cfguObj* obj, const char* name)
{
	struct cfguVal* val;

	if (obj && name) {
		val = cfgu_find_val(obj, name);
	} else {
		return 0;
	}

	return cfgu_true(val);
}

char cfgu_get_false(const struct cfguObj* obj, const char* name)
{
	struct cfguVal* val;

	if (obj && name) {
		val = cfgu_find_val(obj, name);
	} else {
		return 0;
	}

	return cfgu_false(val);
}

struct cfguList* cfgu_get_list(const struct cfguObj* obj, const char* name)
{
	struct cfguVal* val;

	if (obj && name) {
		val = cfgu_find_val(obj, name);
	} else {
		return NULL;
	}

	return cfgu_list(val);
}

struct cfguObj* cfgu_get_obj(const struct cfguObj* obj, const char* name)
{
	struct cfguVal* val;

	if (obj || name) {
		val = cfgu_find_val(obj, name);
	} else {
		return NULL;
	}

	return cfgu_obj(val);
}

double cfgu_real(const struct cfguVal* val, double def)
{
	if (!val)
		return def;

	if (val->type != CFGU_REAL)
		return def;

	return val->value.real;
}

const char* cfgu_str(const struct cfguVal* val)
{
	if (!val)
		return NULL;

	if (val->type != CFGU_STRING)
		return NULL;

	return val->value.str;
}

char cfgu_true(const struct cfguVal* val)
{
	if (!val)
		return 0;

	return val->type == CFGU_TRUE;
}

char cfgu_false(const struct cfguVal* val)
{
	if (!val)
		return 0;

	return val->type == CFGU_FALSE;
}

struct cfguList* cfgu_list(const struct cfguVal* val)
{
	if (!val)
		return NULL;

	if (val->type != CFGU_LIST)
		return NULL;

	return val->value.list;
}

struct cfguObj* cfgu_obj(const struct cfguVal* val)
{
	if (!val)
		return NULL;

	if (val->type != CFGU_OBJECT)
		return NULL;

	return val->value.obj;
}

size_t cfgu_obj_size(const struct cfguObj* obj)
{
	return hashtable_count(obj->var_hash);
}
	
size_t cfgu_list_size(const struct cfguList* list)
{
	return (size_t)list_size(list->value_list);
}

void cfgu_init_config(struct cfguConfig* config)
{
	if (!config)
		return;

	/* void** */
	cfgu_lex_init(&config->scanner);
	config->global = cfgu_new_obj_raw();
	config->pos.line = 0;
	config->pos.col = 0;
}

void cfgu_destroy_config(struct cfguConfig* config)
{
	if (!config)
		return;

	/* void* */
	cfgu_lex_destroy(config->scanner);
	cfgu_free_obj(config->global);
}

void cfgu_set_input(struct cfguConfig* config, FILE* fp)
{
	if (!config)
		return;

	config->pos.line = 0;
	config->pos.col = 0;
	/* Change the input used by the lexer */
	cfgu_restart(fp, config->scanner);
}

int cfgu_load_one(struct cfguConfig* config) 
{

	if (!config)
		return -1;
	
	/* Clear the error condition */
	config->error[0] = '\0';

	size_t before = cfgu_obj_size(config->global);

	/* yyparse return 1 on error and 0 on success */
	if (yyparse((void*)config))
		return -1;

	size_t after = cfgu_obj_size(config->global);

	/* If a variable was loaded then we were successful. */
	return after == before ? -1 : 0;
}

int cfgu_load_all(struct cfguConfig* config)
{
	int found_var = -1;
	int rv = -1;

	do {
		rv = cfgu_load_one(config);

		if (!rv)
			found_var = 0;
	} while(!rv);

	return found_var;
}

int cfgu_load(struct cfguConfig* config, const char* name)
{
	FILE* fp;
	int rv;

	fp=fopen(name,"r");
	if (!fp) {
		_cfgu_error(config, "Could not open config file '%s'.", name);
		return -1;
	}

	cfgu_set_input(config, fp);

	rv = cfgu_load_all(config);
       
	fclose(fp);

	return rv;
}

namespace cfgu
{
	Exception Exception::format(const char* fmt, ...)
	{
		char error[CFGU_MAX_ERROR];
		va_list ap;

		va_start(ap, fmt);
		vsnprintf (error, CFGU_MAX_ERROR, fmt, ap);
		va_end(ap);

		return Exception(error);
	}

	Exception Exception::format(struct cfguPos pos, const char* fmt, ...)
	{
		char error[CFGU_MAX_ERROR];
		va_list ap;
		int wrote;

		wrote = snprintf(error, CFGU_MAX_ERROR, "At %u:%u, ", pos.line, pos.col);
		va_start(ap, fmt);
		vsnprintf (error + wrote, CFGU_MAX_ERROR - wrote, fmt, ap);
		va_end(ap);

		return Exception(error);
	}

	double Value::real() const throw(Exception)
	{
		if (mValue->type != CFGU_REAL) {
			throw Exception::format(mValue->pos, "expected a real value");
		}

		return mValue->value.real;
	}

	const char* Value::str() const throw(Exception)
	{
		if (mValue->type != CFGU_STRING) {
			throw Exception::format(mValue->pos, "expected a string value");
		}

		return mValue->value.str;
	}

	bool Value::is_true() const
	{
		return cfgu_true(mValue);
	}

	bool Value::is_false() const
	{
		return cfgu_false(mValue);
	}
       
	List Value::list() const throw(Exception)
	{
		if (mValue->type != CFGU_LIST) {
			throw Exception::format(mValue->pos, "expected a list value");
		}

		return List(mValue->value.list);
	}

	Object Value::obj() const throw(Exception)
	{
		if (mValue->type != CFGU_OBJECT) {
			throw Exception::format(mValue->pos, "expected an object value");
		}

		return Object(mValue->value.obj);
	}

	bool Iterator::has_next() const
	{
		return mListPos->next != mList;
	}

	Iterator::Iterator(list_t* list): 
	        mList(list), mListPos(list), mPos(0)
	{
	}

	void* Iterator::next()
	{
		if (!has_next())
			return NULL;

		mListPos = mListPos->next;
		++mPos;
		return mListPos->item;
	}

	Value ListIterator::next() throw(Exception)
	{
		cfguVal* val = (cfguVal*)Iterator::next();

		if (!val) {
			throw Exception::format(mList->pos, 
						"expected an additional value in list");
		}

		return Value(val);
	}

	size_t List::size() const
	{
		return cfgu_list_size(mList);
	}

	List::Iterator List::begin() const
	{
		return List::Iterator(mList);
	}

	Var ObjectIterator::next() throw(Exception)
	{
		cfguVar* var = (cfguVar*)Iterator::next();

		if (!var) {
			throw Exception::format(mObj->pos, 
						"expected an additional variable in object");
		}

		return Var(var);
	}

	bool Object::find(const char* name) const
	{
		return cfgu_find_val(mObj, name);
	}

	Value Object::get(const char* name) const throw(Exception)
	{
		cfguVal* val = cfgu_find_val(mObj, name);

		if (!val) {
			throw Exception::format(mObj->pos, 
						"missing declaration of '%s'.", name);
		}

		return Value(val);
	}
		
	size_t Object::size() const
	{
		return cfgu_obj_size(mObj);
	}

	Object::Iterator Object::begin() const
	{
		return Object::Iterator(mObj);
	}

	Config::Config():
	        Object(NULL)
	{
		cfgu_init_config(&mConfig);
		mObj = mConfig.global;
	}

	Config::~Config()
	{
		cfgu_destroy_config(&mConfig);
        }

	void Config::set_input(FILE* fp)
	{
		cfgu_set_input(&mConfig, fp);
	}

	void Config::load_one() throw(Exception)
        {
		if (cfgu_load_one(&mConfig)) {
			throw Exception(mConfig.error);
		}
        }

	void Config::load_all() throw(Exception)
        {
		cfgu_load_all(&mConfig);

		/* throw if an error occured */
		if (strlen(mConfig.error) > 0) {
			throw Exception::format(mConfig.pos, mConfig.error);
		}
        }

	void Config::load(const char* name) throw(Exception)
        {
		cfgu_load(&mConfig, name);

		/* throw if an error occured */
		if (strlen(mConfig.error) > 0) {
			throw Exception::format(mConfig.pos, mConfig.error);
		}
        }

};

