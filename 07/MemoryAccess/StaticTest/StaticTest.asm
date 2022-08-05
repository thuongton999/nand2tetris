// C_PUSH constant 111
@111
D=A
@SP
A=M
M=D
@SP
M=M+1
// C_PUSH constant 333
@333
D=A
@SP
A=M
M=D
@SP
M=M+1
// C_PUSH constant 888
@888
D=A
@SP
A=M
M=D
@SP
M=M+1
// C_POP static 8
@SP
M=M-1
A=M
D=M
@StaticTest.8
M=D
// C_POP static 3
@SP
M=M-1
A=M
D=M
@StaticTest.3
M=D
// C_POP static 1
@SP
M=M-1
A=M
D=M
@StaticTest.1
M=D
// C_PUSH static 3
@StaticTest.3
D=M
@SP
A=M
M=D
@SP
M=M+1
// C_PUSH static 1
@StaticTest.1
D=M
@SP
A=M
M=D
@SP
M=M+1
// sub
@SP
M=M-1
A=M
D=M
A=A-1
M=M-D
// C_PUSH static 8
@StaticTest.8
D=M
@SP
A=M
M=D
@SP
M=M+1
// add
@SP
M=M-1
A=M
D=M
A=A-1
M=M+D
(END)
@END
0;JMP
