import re, sys, random

def remove_whitespace(t):
    if len(t) == 0:
        return 'SKIP'
    return t.strip()

class Compiler:
    def __init__(self):
        if len(sys.argv) != 2:
            print("Usage : cc [FILENAME]")
        lines = open(sys.argv[1], "r").readlines()
        self.lines = list(map(remove_whitespace, lines))

        self.var_init = {}
        self.fn_init = {}
        self.function_to_random_name = {}

        self.source = "void* new_object(void*, unsigned long, ...);\n"
        self.classname = ""
        self.constructors = ""
        self.fn_main = "int main(int argc, const char** argv) {\n"

    def finalise_fn(self, prelude, init):
        fn_name = "fn_" + str(random.randint(0, 1 << 20))
        fn = f"{prelude.group(2)} {fn_name} ({init[2]})";
        for i in init[3:]:
            fn += i
        return (fn, fn_name)

    def finalise_constructor(self):
        fn_name = "fn_construc_" + self.class_name
        fn = f"{self.class_name}* {fn_name} ({self.class_name}* this)" + " {\n"
        for k, v in self.var_init.items():
            fn += f"this->{k} = {v}\n"
        for k, v in self.fn_init.items():
            fn += f"this->{k} = {self.function_to_random_name[k]};\n"
        fn += "return this;\n"
        fn += "}"
        self.constructors += fn
        return fn_name

    def process(self):
        match_obj = None
        in_class = False
        in_fn = False
        output = []

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
                        self.var_init.clear()
                        self.fn_init.clear()
                        self.source += f"{self.class_name}* _{self.class_name} = " + "{0};\n"
                        self.fn_main += f"_{self.class_name} = malloc(sizeof({self.class_name})); _{self.class_name} = fn_construc_{self.class_name}(_{self.class_name});\n"
                        self.class_name = ""
                        match_obj = None
                        self.function_to_random_name.clear()
                        in_class = False
                        output.append('};\n')
                    continue

            if in_fn:
                m = re.search(new_decl, i)
                new = None
                if m:
                    new = i.replace(m.group(0), f'new_object({"fn_construc_" + self.class_name}, sizeof({self.class_name}){"" if not m.group(2) else "," + m.group(2)});\n')
                self.fn_init[match_obj.group(3)].append(i if not new else new)
                continue

            match_obj = re.search(class_decl, i)
            if match_obj:
                in_class = True
                self.class_name = match_obj.group(1)
                self.source += f"{match_obj.group(1)}* fn_construc_{match_obj.group(1)} ({match_obj.group(1)}* this); \n"
                output.append(f'typedef struct ___{match_obj.group(1)} {match_obj.group(1)};\nstruct ___{match_obj.group(1)} ' + '{\n')
                continue

            match_obj = re.search(var_decl, i)
            if match_obj:
                if not in_class:
                    raise Exception("Variables can only be defined inside classes")
                m = re.search(new_decl, i)
                new = None
                if m:
                    new = match_obj.group(4).replace(m.group(0), f'new_object({"fn_construc_" + self.class_name}, sizeof({self.class_name}){"" if not m.group(2) else "," + m.group(2)});\n')
                self.var_init[match_obj.group(3)] = match_obj.group(4) if not new else new
                output.append(f'{match_obj.group(2)} {match_obj.group(3)};\n')
                continue

            match_obj = re.search(fn_decl, i)
            if match_obj:
                if not in_class:
                    raise Exception("Functions can only be defined inside classes")
                in_fn = True
                if match_obj.group(1) == 'instance':
                    params = f"{self.class_name}* this" + ("" if not match_obj.group(4) else ","  + match_obj.group(4))
                    self.fn_init[match_obj.group(3)] = [match_obj.group(2), match_obj.group(3), params]
                    print(params)
                    output.append(f'{match_obj.group(2)} (*{match_obj.group(3)}) ({params});\n')
                else:
                    self.fn_init[match_obj.group(3)] = [match_obj.group(2), match_obj.group(3), match_obj.group(4)]
                    output.append(f'{match_obj.group(2)} (*{match_obj.group(3)}) ({match_obj.group(4)});\n')
                continue
            output.append(i)

        self.fn_main += "_Main->main();\n"
        self.fn_main += "}\n"
        generated = ""
        for i in output:
            generated += i
        generated += self.source
        generated += self.constructors
        generated += self.fn_main
        return generated
    def compile(self):
        file = open(sys.argv[1] + ".c", "w")
        file.write(self.process())

if __name__ == '__main__':
    Compiler().compile(