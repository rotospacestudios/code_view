# File: file_types_module.py

from file_parser import LuaFileParser, FileParser

file_types = {
    ".py": FileParser,
    ".js": FileParser,
    ".java": FileParser,
    ".cpp": FileParser,
    ".cs": FileParser,
    ".rb": FileParser,
    ".php": FileParser,
    ".swift": FileParser,
    ".kt": FileParser,
    ".go": FileParser,
    ".rs": FileParser,
    ".ts": FileParser,
    ".sh": FileParser,
    ".pl": FileParser,
    ".lua": LuaFileParser,
    ".scala": FileParser,
    "None": FileParser
}