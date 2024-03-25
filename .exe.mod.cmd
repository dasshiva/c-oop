savedcmd_/home/shiva/module/exe.mod := printf '%s\n'   exe.o | awk '!x[$$0]++ { print("/home/shiva/module/"$$0) }' > /home/shiva/module/exe.mod
