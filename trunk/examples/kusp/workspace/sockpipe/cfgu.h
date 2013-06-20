#ifndef CFGU_H
#define CFGU_H

#include "linkedlist.h"
#include "hashtable.h"

/* 
 * These functions have C linkage to make them accessible
 * to C programs. The library is compiled using C++ but
 * these are still callable.
 */
#ifdef __cplusplus
#include <stdexcept>

extern "C" {
#endif

/* Maximum length of lexer and parser error messages */
#define CFGU_MAX_ERROR 100

/* Used to track text positions of elements */
struct cfguPos
{
	unsigned int line;
	unsigned int col;
};

/* The different types that exists */
enum cfguType {
	CFGU_OBJECT = 0,
	CFGU_REAL = 1,
        CFGU_STRING = 2,
	CFGU_LIST = 3,
	CFGU_TRUE = 4,
	CFGU_FALSE = 5
};

/* Stores a list of unnamed values */
struct cfguList
{
	struct cfguPos pos;

	/* Stores value objects */
	list_t* value_list;
};

/* A union that represents all possible data types and keeps track of which
 * type is in use.
 */
struct cfguVal
{	
	struct cfguPos pos;

	enum cfguType type;

	union {
		struct cfguList* list;
		struct cfguObj* obj;
		double real;
		char* str;
	} value;
};

/* A named value */
struct cfguVar
{
	struct cfguPos pos;

	char* name;

	struct cfguVal* val;
};

/* A collection of named values */
struct cfguObj
{
	struct cfguPos pos;

	/* Stores var objects */
	list_t* var_list;
	/* Stores var objects */
	hashtable_t* var_hash;
};

/*
 * This structure is used to make the parser reentrant
 * it also contains an object that stores all variables
 * delcared at the global level.
 */
struct cfguConfig
{
	struct cfguPos pos;
	char error[CFGU_MAX_ERROR];
	void* scanner;
	struct cfguObj* global;
};

/*
 * Find a variable with the given name in an object and return its value.
 * @obj The object to look in.
 * @name The name of the variable.
 * @return a variable or NULL if the variable could not be found
 */
struct cfguVal* cfgu_find_val(const struct cfguObj* obj, const char* name);

/*
 * Find a variable with the given name in an object and return its value
 * as a real if the variable is a real.
 * @obj the object to look in.
 * @name The name of the variable.
 * @def The return value on error.
 * @return a real or NULL if the variable could not be found
 */
double cfgu_get_real(const struct cfguObj* obj, const char* name, double def);

/*
 * Find a variable with the given name in an object and return its value
 * as a string if the variable is a string.
 * @obj the object to look in.
 * @name The name of the variable.
 * @return a string or NULL if the variable could not be found
 */
const char* cfgu_get_str(const struct cfguObj* obj, const char* name);

char cfgu_get_true(const struct cfguObj* obj, const char* name);

char cfgu_get_false(const struct cfguObj* obj, const char* name);

/*
 * Find a variable with the given name in an object and return its value
 * as an object if the variable is an object.
 * @obj the object to look in.
 * @name The name of the variable.
 * @return an object or NULL if the variable could not be found
 */
struct cfguObj* cfgu_get_obj(const struct cfguObj* obj, const char* name);

/*
 * Find a variable with the given name in an object and return its value
 * as a list if the variable is a list.
 * @obj the object to look in.
 * @name The name of the variable.
 * @return a list or NULL if the variable could not be found
 */
struct cfguList* cfgu_get_list(const struct cfguObj* obj, const char* name);

/*
 * Retrieve the value of a variable as a real.
 * If the variable is not a real then an error occurs.
 * @var The variable is to get the value from.
 * @def the default value to return if there is an error.
 */
double cfgu_real(const struct cfguVal* var, double def);

/*
 * Retrieve the value of a variable as a string.
 * If the variable is not a string then an error occurs.
 * @var The variable is to get the value from.
 * @return a C-string or NULL if an error occured.
 */
const char* cfgu_str(const struct cfguVal* var);

char cfgu_true(const struct cfguVal* var);

char cfgu_false(const struct cfguVal* var);

/*
 * Retrieve the value of a variable as an object.
 * If the variable is not an object then an error occurs.
 * @var The variable is to get the value from.
 * @return an object or NULL if an error occured.
 */
struct cfguObj* cfgu_obj(const struct cfguVal* var);

/*
 * Retrieve the value of a variable as a list.
 * If the variable is not a list then an error occurs.
 * @var The variable is to get the value from.
 * @return a list or NULL if an error occured.
 */
struct cfguList* cfgu_list(const struct cfguVal* var);

size_t cfgu_obj_size(const struct cfguObj* obj);
	
size_t cfgu_list_size(const struct cfguList* list);

/*
 * This function should be called on a cfguConfig struct
 * before it is used.
 * @config A pointer to a cfguConfig struct.
 */
void cfgu_init_config(struct cfguConfig* config);

/*
 * This function should be called on a cfguConfig struct
 * when it is done being used.
 * @config A pointer to a cfguConfig struct.
 */
void cfgu_destroy_config(struct cfguConfig* config);

void cfgu_set_input(struct cfguConfig* config, FILE* fp);

int cfgu_load_one(struct cfguConfig* config, FILE* fp);

int cfgu_load_all(struct cfguConfig* config, FILE* fp);

int cfgu_load(struct cfguConfig* config, const char* name);

/* The C++ interface is invisible to C programs. */
#ifdef __cplusplus
} // End of extern "C" {

namespace cfgu
{
	class Exception: public std::runtime_error
	{
	public:
		static Exception format(const char* fmt, ...);
		static Exception format(struct cfguPos pos, const char* fmt, ...);

		Exception(const char* msg): runtime_error(msg) {}
	};

	class NonCopyable
	{
	protected:
		NonCopyable () {}
		~NonCopyable () {} /// Protected non-virtual destructor
	private: 
		NonCopyable (const NonCopyable &);
		NonCopyable & operator = (const NonCopyable &);
	};

	class List;
	class Object;

	class Value
	{
	public:
		Value(struct cfguVal* value): mValue(value) { }
	        cfguType type() const { return mValue->type; }
		double real() const throw(Exception);
		const char* str() const throw(Exception);
		bool is_true() const;
		bool is_false() const;
		List list() const throw(Exception);
		Object obj() const throw(Exception);
	protected:
		struct cfguVal* mValue;
	};

	class Var
	{
	public:
		Var(struct cfguVar* var): mVar(var) {}
		const char* name() const { return mVar->name; }
		Value value() const { return Value(mVar->val); }
	protected:
		struct cfguVar* mVar;
	};

	class Iterator
	{
	public:
		bool has_next() const;
		size_t pos() const { return mPos; }
	protected:
		Iterator(list_t* list);
		void* next();
	private:
		list_t* mList;
		list_t* mListPos;
		size_t mPos;
	};

	class ListIterator: public Iterator
	{
	public:
	        ListIterator(cfguList* list): Iterator(list->value_list), mList(list) {}
		Value next() throw(Exception);
	protected:
		cfguList* mList;
	};

	class List
	{
	public:
		typedef ListIterator Iterator;

	        List(struct cfguList* list): mList(list) {}
		size_t size() const;
		Iterator begin() const;
	protected:
		struct cfguList* mList;
	};

	class ObjectIterator: public Iterator
	{
	public:
	        ObjectIterator(cfguObj* obj): Iterator(obj->var_list), mObj(obj) {}
		Var next() throw(Exception);
	protected:
		cfguObj* mObj;
	};

	class Object
	{
	public:
		typedef ObjectIterator Iterator;

		Object(struct cfguObj* obj): mObj(obj) {}

		bool find(const char* name) const;
		Value get(const char* name) const throw(Exception);
		
		size_t size() const;
		Iterator begin() const;
	protected:
		struct cfguObj* mObj;
	};

	class Config: public Object, private NonCopyable
	{
	public:
		Config();
		~Config();
		void set_input(FILE* fp);
		void load_one() throw(Exception);
		void load_all() throw(Exception);
		void load(const char* name) throw(Exception);
	protected:
		struct cfguConfig mConfig;
	};

};

#endif

#endif
