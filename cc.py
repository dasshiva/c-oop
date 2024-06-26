import re, sys

def remove_whitespace(t):
    if len(t) == 0:
        return 'SKIP'
    return t.strip()

copyright =""" 
/*Code generated by C-OOP
Copyright(C) 2024 Shivashish Das */
"""
class Compiler:
    def __init__(self, file):
        lines = open(file, "r").readlines()
        self.lines = list(map(remove_whitespace, lines))

        self.svar_init = {}
        self.ivar_init = {}
        self.fn_init = {}
        self.function_to_random_name = {}

        self.source = "void* new_object(void*, unsigned long, ...);\n"
        self.classname = ""
        self.constructors = ""
        self.fn_main = "int main(int argc, const char** argv) {\n"

    def finalise_fn(self, prelude, init):
        fn_name = "fn_" + prelude.group(3);
        fn = f"{prelude.group(2)} {fn_name} ({init[2]})";
        for i in init[4:]:
            fn += i
        return (fn, fn_name)

    def finalise_constructor(self):
        fn_name = "fn_construc_" + self.class_name
        fn = f"struct ___{self.class_name}* {fn_name} (struct ___{self.class_name}* this)" + " {\n"
        static_fn = f"struct ___{self.class_name}* {fn_name + 'static'} (struct ___{self.class_name}* this)" + "{\n"
        for k, v in self.ivar_init.items():
            fn += f"this->{k} = {v}\n"
        for k, v in self.svar_init.items():
            static_fn += f"this->{k} = {v}\n"
        for k, v in self.fn_init.items():
            if v[3] == 'instance':
                fn += f"this->{k} = {self.function_to_random_name[k]};\n"
            else:
                static_fn += f"this->{k} = {self.function_to_random_name[k]};\n"
        fn += "return this;\n"
        fn += "}"
        static_fn += "return this;\n"
        static_fn += "}"
        self.constructors += fn
        self.constructors += static_fn
        return fn_name

    def process(self, toplevel):
        match_obj = None
        in_class = False
        in_fn = False
        output = []

        self.fn_main = "" if not toplevel else self.fn_main
        import_decl = re.compile(r'import\s*([A-Z]+)', re.IGNORECASE)
        class_decl = re.compile(r'class\s*([A-Z]+)', re.IGNORECASE)
        var_decl = re.compile(r'(static|instance)\s*([A-Z]+)\s*([A-Z]+)\s*=\s*((\S)+;)', re.IGNORECASE)
        fn_decl = re.compile(r'(static|instance)\s*fn\s*([A-Z]+)\s*([A-Z]+)\s*\(((.)*)\)', re.IGNORECASE)
        new_decl = re.compile(r'new\s*([A-Z]+)\((.)*\)', re.IGNORECASE)

        for i in self.lines:
            if i == 'SKIP':
                continue
            if "begin" in i:
                self.fn_init[match_obj.group(3)].append('{\n')
                continue
            if "end" in i:
                if in_class:
                    if in_fn:
                        in_fn = False
                        self.fn_init[match_obj.group(3)].append('}\n')
                        fn = self.finalise_fn(match_obj, self.fn_init[match_obj.group(3)])
                        self.source += fn[0]
                        self.function_to_random_name[match_obj.group(3)] = fn[1]
                    else:
                        fn_name = self.finalise_constructor()
                        self.svar_init.clear()
                        self.ivar_init.clear()
                        self.fn_init.clear()
                        output.append('};\n')
                        output.append(f"__{self.class_name}* _{self.class_name} = " + "{0};\n")
                        self.fn_main += f"_{self.class_name} = calloc(1, sizeof(struct ___{self.class_name}));\n _{self.class_name} = fn_construc_{self.class_name + 'static'}(_{self.class_name});\n"
                        self.class_name = ""
                        match_obj = None
                        self.function_to_random_name.clear()
                        in_class = False
                    continue

            i = i.replace('.', '->')
            if in_fn:
                m = re.search(new_decl, i)
                new = None
                if m:
                    new = i.replace(m.group(0), f'new_object({"fn_construc_" + self.class_name}, sizeof(struct ___{self.class_name}){"" if not m.group(2) else "," + m.group(2)});\n')
                self.fn_init[match_obj.group(3)].append(i if not new else new)
                continue

            match_obj = re.search(import_decl, i)
            if match_obj:
                if in_class:
                    raise Exception("Import statements are only allowed in the top level namespace")
                src = Compiler(match_obj.group(1) + '.lang').process(False)
                self.source += src[0]
                self.fn_main += src[1]
                continue

            match_obj = re.search(class_decl, i)
            if match_obj:
                in_class = True
                self.class_name = match_obj.group(1)
                self.source += f"{match_obj.group(1)}* fn_construc_{match_obj.group(1)} (__{match_obj.group(1)}* this); \n"
                output.append(f'#define {self.class_name} __{self.class_name}\n')
                output.append(f'typedef struct ___{match_obj.group(1)} __{match_obj.group(1)};\nstruct ___{match_obj.group(1)} ' + '{\n')
                continue

            match_obj = re.search(var_decl, i)
            if match_obj:
                if not in_class:
                    raise Exception("Variables can only be defined inside classes")
                m = re.search(new_decl, i)
                new = None
                if m:
                    new = match_obj.group(4).replace(m.group(0), f'new_object({"fn_construc_" + self.class_name}, sizeof(struct ___{self.class_name}){"" if not m.group(2) else "," + m.group(2)});\n')
                if match_obj.group(1) == 'static':
                    self.svar_init[match_obj.group(3)] = match_obj.group(4) if not new else new
                else:
                    self.ivar_init[match_obj.group(3)] = match_obj.group(4) if not new else new
                output.append(f'{match_obj.group(2)} {match_obj.group(3)};\n')
                continue

            match_obj = re.search(fn_decl, i)
            if match_obj:
                if not in_class:
                    raise Exception("Functions can only be defined inside classes")
                in_fn = True
                if match_obj.group(1) == 'instance':
                    params = f"struct ___{self.class_name}* this" + ("" if not match_obj.group(4) else ","  + match_obj.group(4))
                    self.fn_init[match_obj.group(3)] = [match_obj.group(2), match_obj.group(3), params, match_obj.group(1)]
                    output.append(f'{match_obj.group(2)} (*{match_obj.group(3)}) ({params});\n')
                else:
                    self.fn_init[match_obj.group(3)] = [match_obj.group(2), match_obj.group(3), match_obj.group(4), match_obj.group(1)]
                    output.append(f'{match_obj.group(2)} (*{match_obj.group(3)}) ({match_obj.group(4)});\n')
                continue
            output.append(i)

        if toplevel:
            self.fn_main += "_Main->main();\n"
            self.fn_main += "}\n"
        generated = copyright + "\n" if toplevel else ""
        for i in output:
            generated += i
        generated += self.source
        generated += self.constructors
        generated += self.fn_main if toplevel else ""
        return generated if toplevel else (generated, self.fn_main)
    def compile(self):
        file = open(sys.argv[1] + ".c", "w")
        file.write(self.process(True))

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: cc.py [FILENAME]")
        exit(1)
    Compiler(sys.argv[1]).compile()
