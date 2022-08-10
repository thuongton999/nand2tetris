// C_PUSH constant 17
@17
D=A
@SP
A=M
M=D
@SP
M=M+1
// C_PUSH constant 17
@17
D=A
@SP
A=M
M=D
@SP
M=M+1
// eq
@SP
M=M-1
A=M
D=M
A=A-1
M=M-D
D=M
M=-1
@806ee678-fd35-434f-a142-0791aeba5d48
D;JEQ
@SP
A=M-1
M=0
(806ee678-fd35-434f-a142-0791aeba5d48)
// C_PUSH constant 17
@17
D=A
@SP
A=M
M=D
@SP
M=M+1
// C_PUSH constant 16
@16
D=A
@SP
A=M
M=D
@SP
M=M+1
// eq
@SP
M=M-1
A=M
D=M
A=A-1
M=M-D
D=M
M=-1
@d380c787-c0a6-4120-b421-60ce2c4c4ffd
D;JEQ
@SP
A=M-1
M=0
(d380c787-c0a6-4120-b421-60ce2c4c4ffd)
// C_PUSH constant 16
@16
D=A
@SP
A=M
M=D
@SP
M=M+1
// C_PUSH constant 17
@17
D=A
@SP
A=M
M=D
@SP
M=M+1
// eq
@SP
M=M-1
A=M
D=M
A=A-1
M=M-D
D=M
M=-1
@9119ba40-3fc0-42ad-ba01-fda679859c58
D;JEQ
@SP
A=M-1
M=0
(9119ba40-3fc0-42ad-ba01-fda679859c58)
// C_PUSH constant 892
@892
D=A
@SP
A=M
M=D
@SP
M=M+1
// C_PUSH constant 891
@891
D=A
@SP
A=M
M=D
@SP
M=M+1
// lt
@SP
M=M-1
A=M
D=M
A=A-1
M=M-D
D=M
M=-1
@fc28b211-6311-4c2e-a80e-64b7dc4f2ac2
D;JLT
@SP
A=M-1
M=0
(fc28b211-6311-4c2e-a80e-64b7dc4f2ac2)
// C_PUSH constant 891
@891
D=A
@SP
A=M
M=D
@SP
M=M+1
// C_PUSH constant 892
@892
D=A
@SP
A=M
M=D
@SP
M=M+1
// lt
@SP
M=M-1
A=M
D=M
A=A-1
M=M-D
D=M
M=-1
@277d3c36-a408-4c8b-92d1-95b425f69466
D;JLT
@SP
A=M-1
M=0
(277d3c36-a408-4c8b-92d1-95b425f69466)
// C_PUSH constant 891
@891
D=A
@SP
A=M
M=D
@SP
M=M+1
// C_PUSH constant 891
@891
D=A
@SP
A=M
M=D
@SP
M=M+1
// lt
@SP
M=M-1
A=M
D=M
A=A-1
M=M-D
D=M
M=-1
@24335378-6b1a-48d4-a62b-0339c1b76fe2
D;JLT
@SP
A=M-1
M=0
(24335378-6b1a-48d4-a62b-0339c1b76fe2)
// C_PUSH constant 32767
@32767
D=A
@SP
A=M
M=D
@SP
M=M+1
// C_PUSH constant 32766
@32766
D=A
@SP
A=M
M=D
@SP
M=M+1
// gt
@SP
M=M-1
A=M
D=M
A=A-1
M=M-D
D=M
M=-1
@84f09c4f-589c-4b03-8c54-a17fda03fc6c
D;JGT
@SP
A=M-1
M=0
(84f09c4f-589c-4b03-8c54-a17fda03fc6c)
// C_PUSH constant 32766
@32766
D=A
@SP
A=M
M=D
@SP
M=M+1
// C_PUSH constant 32767
@32767
D=A
@SP
A=M
M=D
@SP
M=M+1
// gt
@SP
M=M-1
A=M
D=M
A=A-1
M=M-D
D=M
M=-1
@2b88bfe2-8229-43d9-98d1-feacbc228061
D;JGT
@SP
A=M-1
M=0
(2b88bfe2-8229-43d9-98d1-feacbc228061)
// C_PUSH constant 32766
@32766
D=A
@SP
A=M
M=D
@SP
M=M+1
// C_PUSH constant 32766
@32766
D=A
@SP
A=M
M=D
@SP
M=M+1
// gt
@SP
M=M-1
A=M
D=M
A=A-1
M=M-D
D=M
M=-1
@0f9c49a2-ceb8-4e62-8bd0-72faca21fdb4
D;JGT
@SP
A=M-1
M=0
(0f9c49a2-ceb8-4e62-8bd0-72faca21fdb4)
// C_PUSH constant 57
@57
D=A
@SP
A=M
M=D
@SP
M=M+1
// C_PUSH constant 31
@31
D=A
@SP
A=M
M=D
@SP
M=M+1
// C_PUSH constant 53
@53
D=A
@SP
A=M
M=D
@SP
M=M+1
// add
@SP
AM=M-1
D=M
A=A-1
M=M+D
// C_PUSH constant 112
@112
D=A
@SP
A=M
M=D
@SP
M=M+1
// sub
@SP
AM=M-1
D=M
A=A-1
M=M-D
// neg
@SP
A=M-1
M=-M
// and
@SP
M=M-1
A=M
D=M
A=A-1
M=D&M
// C_PUSH constant 82
@82
D=A
@SP
A=M
M=D
@SP
M=M+1
// or
@SP
M=M-1
A=M
D=M
A=A-1
M=D|M
// not
@SP
A=M-1
M=!M
(END)
@END
0;JMP
