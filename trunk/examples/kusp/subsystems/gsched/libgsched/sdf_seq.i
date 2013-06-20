 /* sdf_seq.i 
 *
 * SWIG Interface file for gsched.c.
 * 
 */
%module sdf_seq 
%inline %{
	int sdf_seq_parse_member_params(void *param);

	void *num(void);
%}
 
