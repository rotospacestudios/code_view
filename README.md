# file_parser.py

This Python script contains classes for parsing and analyzing source code files. The main classes are `FileParser` and `Stack`, and subclasses for specific languages like `PythonFileParser`, `LuaFileParser`, and `CParser`, `PascalParser` and `CPlusPlusParser`.

## Language Support

The parsers support a subset of Pascal, Python, Lua, C++ and C languages. They can handle literals and table constructors where all the keys have no quotes. They can also handle basic constructs like variable assignments, function definitions, and control flow statements.

## PythonFileParser
- Handles basic Python syntax: variable assignments, function definitions, control flow statements.
- Supports literals and list, dictionary constructors.
- Limitations: Does not support decorators, dynamic typing, or complex data structures, does not support multi-file projects.

## LuaFileParser

- Handles basic Lua syntax: variable assignments, function definitions, control flow statements.
- Supports literals and table constructors where all the keys have no quotes.
- Limitations: Does not support Lua's unique features like coroutines, does not handle complex table constructors.

## CParser

- Handles basic C syntax: variable assignments, function definitions, control flow statements.
- Supports literals and array, struct constructors.
- Limitations: Does not support pointers, macros, or complex data structures.

## PascalParser

- Handles basic Pascal syntax: variable assignments, function definitions, control flow statements.
- Supports literals and array, record constructors.
- Limitations: Does not support pointers, sets, or complex data structures.
