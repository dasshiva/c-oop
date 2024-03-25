typedef struct ___Main Main;
struct ___Main {
int a;
int b;
void (*main) ();
void (*hehe) (Main* this,int a);
};
typedef struct ___Hello Hello;
struct ___Hello {
int c;
int d;
};
void* new_object(void*, unsigned long, ...);
Main* fn_construc_Main (Main* this); 
void fn_1012944 (){
Main* m = new_object(fn_construc_Main, sizeof(Main));
;printf("Hello World");}
void fn_805889 (Main* this,int a){
this->a = 5;}
Main* _Main = {0};
Hello* fn_construc_Hello (Hello* this); 
Hello* _Hello = {0};
Main* fn_construc_Main (Main* this) {
this->a = 90;
this->b = 90;
this->main = fn_1012944;
this->hehe = fn_805889;
return this;
}Hello* fn_construc_Hello (Hello* this) {
this->c = 90;
this->d = 100;
return this;
}int main(int argc, const char** argv) {
_Main = malloc(sizeof(Main)); _Main = fn_construc_Main(_Main);
_Hello = malloc(sizeof(Hello)); _Hello = fn_construc_Hello(_Hello);
_Main->main();
}
