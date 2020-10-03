from recip.core.Opcode import Opcode
from recip.util import DataType

class Opcodes:
    opcodes = {}
    alias = {}

    extOpcodes = {}
    extAlias = {}
    
    definitions = [
        ["STOP", 0x00, "stop", None, 0],
        ["ADD", 0x01, "add", None, 3],
        ["MUL", 0x02, "mul", None, 5],
        ["SUB", 0x03, "sub", None, 3],
        ["DIV", 0x04, "div", None, 5],
        ["SDIV", 0x05, "sdiv", None, 5],
        ["MOD", 0x06, "mod", None, 5],
        ["SMOD", 0x07, "smod", None, 5],
        ["ADDMOD", 0x08, "addmod", None, 8],
        ["MULMOD", 0x09, "mulmod", None, 8],
        ["EXP", 0x0a, "exp", None, 0],
        ["SIGNEXTEND", 0x0b, "signextend", None, 3],
        ["LT", 0x10, "lt", None, 3],
        ["GT", 0x11, "gt", None, 3],
        ["SLT", 0x12, "slt", None, 3],
        ["SGT", 0x13, "sgt", None, 3],
        ["EQ", 0x14, "eq", None, 3],
        ["ISZERO", 0x15, "iszero", None, 3],
        ["AND", 0x16, "_and", None, 3],
        ["OR", 0x17, "_or", None, 3],
        ["XOR", 0x18, "xor", None, 3],
        ["NOT", 0x19, "_not", None, 3],
        ["BYTE", 0x1a, "byte", None, 3],
        ["SHL", 0x1b, "shl", None, 3],
        ["SHR", 0x1c, "shr", None, 3],
        ["SAR", 0x1d, "sar", None, 3],
        ["SHA3", 0x20, "sha3", None, 0],
        ["ADDRESS", 0x30, "address", None, 2],
        ["BALANCE", 0x31, "balance", None, 400],
        ["ORIGIN", 0x32, "_origin", None, 2],
        ["CALLER", 0x33, "caller", None, 2],
        ["CALLVALUE", 0x34, "callvalue", None, 2],
        ["CALLDATALOAD", 0x35, "calldataload", None, 3],
        ["CALLDATASIZE", 0x36, "calldatasize", None, 2],
        ["CALLDATACOPY", 0x37, "calldatacopy", None, 3],
        ["CODESIZE", 0x38, "codesize", None, 2],
        ["CODECOPY", 0x39, "codecopy", None, 0],
        ["GASPRICE", 0x3a, "gasprice", None, 2],
        ["EXTCODESIZE", 0x3b, "extcodesize", None, 700],
        ["EXTCODECOPY", 0x3c, "extcodecopy", None, 0],
        ["RETURNDATASIZE", 0x3d, "returndatasize", None, 0],
        ["RETURNDATACOPY", 0x3e, "returndatacopy", None, 0],
        ["EXTCODEHASH", 0x3f, "extcodehash", None, 0],
        ["BLOCKHASH", 0x40, "blockhash", None, 20],
        ["COINBASE", 0x41, "coinbase", None, 2],
        ["TIMESTAMP", 0x42, "timestamp", None, 2],
        ["NUMBER", 0x43, "number", None, 2],
        ["DIFFICULTY", 0x44, "difficulty", None, 2],
        ["GASLIMIT", 0x45, "gaslimit", None, 2],
        ["CHAINID", 0x46, "chainid", None, 2],
        ["SELFBALANCE", 0x47, "selfbalance", None, 2],
        ["POP", 0x50, "_pop", None, 2],
        ["MLOAD", 0x51, "mload", None, 3],
        ["MSTORE", 0x52, "mstore", None, 3],
        ["MSTORE8", 0x53, "mstore8", None, 3],
        ["SLOAD", 0x54, "sload", None, 200],
        ["SSTORE", 0x55, "sstore", None, 0],
        ["JUMP", 0x56, "jump", None, 8],
        ["JUMPI", 0x57, "jumpi", None, 10],
        ["PC", 0x58, "_pc", None, 2],
        ["MSIZE", 0x59, "msize", None, 2],
        ["GAS", 0x5a, "gas", None, 2],
        ["JUMPDEST", 0x5b, "jumpdest", None, 1],
        ["PUSH1", 0x60, "push", 1, 3],
        ["PUSH2", 0x61, "push", 2, 3],
        ["PUSH3", 0x62, "push", 3, 3],
        ["PUSH4", 0x63, "push", 4, 3],
        ["PUSH5", 0x64, "push", 5, 3],
        ["PUSH6", 0x65, "push", 6, 3],
        ["PUSH7", 0x66, "push", 7, 3],
        ["PUSH8", 0x67, "push", 8, 3],
        ["PUSH9", 0x68, "push", 9, 3],
        ["PUSH10", 0x69, "push", 10, 3],
        ["PUSH11", 0x6a, "push", 11, 3],
        ["PUSH12", 0x6b, "push", 12, 3],
        ["PUSH13", 0x6c, "push", 13, 3],
        ["PUSH14", 0x6d, "push", 14, 3],
        ["PUSH15", 0x6e, "push", 15, 3],
        ["PUSH16", 0x6f, "push", 16, 3],
        ["PUSH17", 0x70, "push", 17, 3],
        ["PUSH18", 0x71, "push", 18, 3],
        ["PUSH19", 0x72, "push", 19, 3],
        ["PUSH20", 0x73, "push", 20, 3],
        ["PUSH21", 0x74, "push", 21, 3],
        ["PUSH22", 0x75, "push", 22, 3],
        ["PUSH23", 0x76, "push", 23, 3],
        ["PUSH24", 0x77, "push", 24, 3],
        ["PUSH25", 0x78, "push", 25, 3],
        ["PUSH26", 0x79, "push", 26, 3],
        ["PUSH27", 0x7a, "push", 27, 3],
        ["PUSH28", 0x7b, "push", 28, 3],
        ["PUSH29", 0x7c, "push", 29, 3],
        ["PUSH30", 0x7d, "push", 30, 3],
        ["PUSH31", 0x7e, "push", 31, 3],
        ["PUSH32", 0x7f, "push", 32, 3],
        ["DUP1", 0x80, "dup", 1, 3],
        ["DUP2", 0x81, "dup", 2, 3],
        ["DUP3", 0x82, "dup", 3, 3],
        ["DUP4", 0x83, "dup", 4, 3],
        ["DUP5", 0x84, "dup", 5, 3],
        ["DUP6", 0x85, "dup", 6, 3],
        ["DUP7", 0x86, "dup", 7, 3],
        ["DUP8", 0x87, "dup", 8, 3],
        ["DUP9", 0x88, "dup", 9, 3],
        ["DUP10", 0x89, "dup", 10, 3],
        ["DUP11", 0x8a, "dup", 11, 3],
        ["DUP12", 0x8b, "dup", 12, 3],
        ["DUP13", 0x8c, "dup", 13, 3],
        ["DUP14", 0x8d, "dup", 14, 3],
        ["DUP15", 0x8e, "dup", 15, 3],
        ["DUP16", 0x8f, "dup", 16, 3],
        ["SWAP1", 0x90, "swap", 2, 3],
        ["SWAP2", 0x91, "swap", 3, 3],
        ["SWAP3", 0x92, "swap", 4, 3],
        ["SWAP4", 0x93, "swap", 5, 3],
        ["SWAP5", 0x94, "swap", 6, 3],
        ["SWAP6", 0x95, "swap", 7, 3],
        ["SWAP7", 0x96, "swap", 8, 3],
        ["SWAP8", 0x97, "swap", 9, 3],
        ["SWAP9", 0x98, "swap", 10, 3],
        ["SWAP10", 0x99, "swap", 11, 3],
        ["SWAP11", 0x9a, "swap", 12, 3],
        ["SWAP12", 0x9b, "swap", 13, 3],
        ["SWAP13", 0x9c, "swap", 14, 3],
        ["SWAP14", 0x9d, "swap", 15, 3],
        ["SWAP15", 0x9e, "swap", 16, 3],
        ["SWAP16", 0x9f, "swap", 17, 3],
        ["LOG0", 0xa0, "log", 0, 2],
        ["LOG1", 0xa1, "log", 1, 3],
        ["LOG2", 0xa2, "log", 2, 4],
        ["LOG3", 0xa3, "log", 3, 5],
        ["LOG4", 0xa4, "log", 4, 6],
        ["CREATE", 0xf0, "create", None, 32000],
        ["CALL", 0xf1, "call", None, 0],
        ["CALLCODE", 0xf2, "callcode", None, 0],
        ["RETURN", 0xf3, "_return", None, 0],
        ["DELEGATECALL", 0xf4, "delegatecall", None, 0],
        ["CREATE2", 0xf5, "create2", None, 0],
        ["STATICCALL", 0xfa, "staticcall", None, 0],
        ["REVERT", 0xfd, "revert", None, 0],
        ["INVALID", 0xfe, "_invalid", None, 0],
        ["SELFDESTRUCT", 0xff, "selfdestruct", None, 5000]
    ]

    extensions = [
        ["SHA256", 0x00, "sha256", None, 0],
        ["VERIFY", 0x01, "verify", None, 0],
        ["CHECKSIG", 0x02, "checksig", None, 0],
        ["CHECKSIGVERIFY", 0x03, "checksigverify", None, 0],
        ["MERGE", 0x04, "_merge", None, 0],
        ["PUBADDR", 0x05, "pubaddr", None, 0],
        ["CHECKMULTISIG", 0x06, "checkmultisig", None, 0],
        ["CHECKMULTISIGVERIFY", 0x07, "checkmultisigverify", None, 0],
        ["CHECKATOMICSWAPVERIFY", 0x08, "checkatomicswapverify", None, 0],
        ["CHECKATOMICSWAPLOCKVERIFY", 0x09, "checkatomicswaplockverify", None, 0]
    ]

    for definition in definitions:
        opcode = Opcode()
        opcode.deserialize(definition)
        opcodes[opcode.code] = opcode 

        alias[opcode.name] = opcode.code

    for extension in extensions:
        opcode = Opcode()
        opcode.deserialize(extension)
        extOpcodes[opcode.code] = opcode 

        extAlias[opcode.name] = opcode.code
    
def alias(name, override=False):
    if override:
        if name in Opcodes.extAlias:
            return Opcodes.extAlias[name]
    return Opcodes.alias[name]

def fetch(code, override=False):
    if override:
        if code in Opcodes.extOpcodes:
            return Opcodes.extOpcodes[code]
    return Opcodes.opcodes[code]
