
int sdf_seq_parse_member_params(void *param){
    int *rparam = ((int*)param);
    return *rparam;
}

void *num(void){
  int *n;
  *n = 34;
  return (void*)n;
}
